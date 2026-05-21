import requests
from groq import Groq
import datetime
import json
import os
import sqlite3
import time
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env local
load_dotenv()

# --- 1. CONFIGURACIÓN ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
NEWS_API_KEY = os.environ.get("NEWS_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

cliente = Groq(api_key=GROQ_API_KEY)

def obtener_noticias(intentos=3):
    print("🌍 1/4 Buscando noticias en NewsAPI...")
    url = f"https://newsapi.org/v2/everything?q=tecnología&language=es&sortBy=publishedAt&pageSize=5&apiKey={NEWS_API_KEY}"
    for intento in range(intentos):
        try:
            respuesta = requests.get(url, timeout=10)
            datos = respuesta.json()
            if datos.get("status") == "ok" and len(datos.get("articles", [])) > 0:
                return datos["articles"][:5]
            print(f"⚠️ NewsAPI no devolvió artículos o hubo un error. Intento {intento+1}/{intentos}")
        except Exception as e:
            print(f"❌ Error de conexión: {e}. Intento {intento+1}/{intentos}")
        time.sleep(2)
    return None

def procesar_con_ia(articulos_crudos, intentos=3):
    print("🧠 2/4 Procesando y dividiendo textos con IA...")
    
    texto_noticias = ""
    for i, art in enumerate(articulos_crudos):
        texto_noticias += f"[{i}] Título: {art['title']}\nDetalle: {art['description']}\n\n"

    # NUEVA INSTRUCCIÓN: Forzamos la llave "noticias" para poder usar json_object
    instrucciones = """
    Eres el editor principal de 'Nexus 8'. Evalúa las siguientes noticias.
    Devuelve ÚNICAMENTE un objeto JSON válido con una clave "noticias" que contenga un arreglo de objetos.
    Cada objeto dentro del arreglo debe tener esta estructura exacta:
    {
      "id_referencia": (el número entre corchetes),
      "titulo": "Título atractivo",
      "gancho": "Una sola frase impactante que invite a leer más (máximo 20 palabras).",
      "contenido_completo": "El artículo detallado y profundo en 3 párrafos.",
      "categoria": "Palabra clave (ej. IA, Gadgets, Software, Hardware)",
      "impacto": "alto" o "bajo"
    }
    """
    
    for intento in range(intentos):
        try:
            respuesta = cliente.chat.completions.create(
                messages=[
                    {"role": "system", "content": instrucciones},
                    {"role": "user", "content": texto_noticias}
                ],
                model="llama-3.3-70b-versatile", 
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            texto_ia = respuesta.choices[0].message.content
            datos_ia = json.loads(texto_ia)
            
            if "noticias" in datos_ia and isinstance(datos_ia["noticias"], list):
                return datos_ia["noticias"]
            else:
                print(f"⚠️ Estructura JSON incorrecta (falta clave 'noticias'). Intento {intento+1}/{intentos}")
                
        except Exception as e:
            print(f"❌ Error al procesar con IA: {e}. Intento {intento+1}/{intentos}")
            
        time.sleep(2)
        
    return []

def actualizar_base_datos(noticias_ia, articulos_crudos):
    print("💾 3/4 Guardando en SQLite y exportando JS...")
    fecha_hoy = datetime.datetime.now().strftime("%d/%m/%Y")
    
    conexion = sqlite3.connect(os.path.join(BASE_DIR, "nexus.db"))
    cursor = conexion.cursor()
    
    # Asegurarnos de que la tabla exista (por si acaso)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS noticias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT,
        titulo TEXT,
        gancho TEXT,
        contenido_completo TEXT,
        categoria TEXT,
        impacto TEXT,
        fuente_nombre TEXT,
        fuente_url TEXT UNIQUE
    )
    ''')
    
    for noticia in noticias_ia:
        idx = noticia.get("id_referencia", 0)
        
        titulo = noticia.get("titulo", "")
        gancho = noticia.get("gancho", "")
        contenido = noticia.get("contenido_completo", "").replace("\n\n", "</p><p>").replace("\n", "<br>")
        categoria = noticia.get("categoria", "")
        impacto = noticia.get("impacto", "")
        fuente_nombre = articulos_crudos[idx]["source"]["name"] if idx < len(articulos_crudos) else ""
        fuente_url = articulos_crudos[idx]["url"] if idx < len(articulos_crudos) else ""
        
        try:
            cursor.execute('''
            INSERT INTO noticias (fecha, titulo, gancho, contenido_completo, categoria, impacto, fuente_nombre, fuente_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (fecha_hoy, titulo, gancho, contenido, categoria, impacto, fuente_nombre, fuente_url))
        except sqlite3.IntegrityError:
            # Si ya existe la URL, la ignoramos
            pass
            
    conexion.commit()
    
    # Extraer todos los datos para generar el JS
    cursor.execute("SELECT fecha, titulo, gancho, contenido_completo, categoria, impacto, fuente_nombre, fuente_url FROM noticias ORDER BY id DESC")
    filas = cursor.fetchall()
    
    historial_actualizado = []
    for f in filas:
        historial_actualizado.append({
            "fecha": f[0],
            "titulo": f[1],
            "gancho": f[2],
            "contenido_completo": f[3],
            "categoria": f[4],
            "impacto": f[5],
            "fuente_nombre": f[6],
            "fuente_url": f[7]
        })
        
    conexion.close()
    return historial_actualizado

def generar_archivo_js(historial):
    print("🌐 4/4 Construyendo el archivo de datos JS (modo local)...")
    
    contenido_js = f"const historial_noticias = {json.dumps(historial, ensure_ascii=False, indent=4)};\n"
    
    with open(os.path.join(BASE_DIR, "historial_datos.js"), "w", encoding="utf-8") as archivo:
        archivo.write(contenido_js)

if __name__ == "__main__":
    articulos = obtener_noticias()
    if articulos:
        noticias_ia = procesar_con_ia(articulos)
        if noticias_ia:
            historial = actualizar_base_datos(noticias_ia, articulos)
            generar_archivo_js(historial)
            print("🚀 ¡Todo listo! La base de datos y los archivos para la web local han sido actualizados.")

