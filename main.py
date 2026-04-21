import requests
from groq import Groq
import datetime
import os # Nueva librería para leer secretos del sistema

# --- 1. CONFIGURACIÓN DE TUS LLAVES (Modo Nube) ---
# Ahora el código buscará las llaves en las variables ocultas del servidor
NEWS_API_KEY = os.environ.get("NEWS_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

cliente = Groq(api_key=GROQ_API_KEY)

def obtener_noticias():
    print("🌍 1/4 Buscando las últimas noticias en NewsAPI...")
    url = f"https://newsapi.org/v2/everything?q=tecnología&language=es&sortBy=publishedAt&pageSize=5&apiKey={NEWS_API_KEY}"
    try:
        respuesta = requests.get(url, timeout=10)
        datos = respuesta.json()
        articulos = []
        if datos.get("status") == "ok" and len(datos.get("articles", [])) > 0:
            print(f"✅ ¡Se encontraron {len(datos['articles'])} noticias! Limpiando datos...")
            for articulo in datos["articles"]:
                titulo = articulo["title"]
                descripcion = articulo["description"] or "Sin descripción detallada"
                articulos.append(f"- TÍTULO: {titulo}\n  DETALLE: {descripcion}\n")
            return "\n".join(articulos)
        return None
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return None

def procesar_con_ia(texto_noticias):
    print("🧠 2/4 Procesando la información con Llama 3 (El Divulgador Educativo)...")
    
    # Aquí inyectamos la nueva personalidad
    instrucciones_sistema = """
    Eres el editor principal de 'Nexus 8', un espacio dedicado a la innovación tecnológica. 
    Tu objetivo es redactar un artículo resumen de 3 párrafos basado en las noticias proporcionadas.
    Tu audiencia principal son jóvenes y estudiantes curiosos por la tecnología. 
    Usa un tono inspirador, dinámico y muy fácil de entender. Evita la jerga excesivamente técnica 
    o aburrida. Queremos que el lector sienta que el futuro ya está aquí.
    Responde ÚNICAMENTE con el artículo final en español (en formato HTML con etiquetas <p>), sin saludos.
    """
    
    respuesta = cliente.chat.completions.create(
        messages=[
            {"role": "system", "content": instrucciones_sistema},
            {"role": "user", "content": f"Noticias a procesar:\n{texto_noticias}"}
        ],
        model="llama-3.3-70b-versatile", 
        temperature=0.75 # Le subimos un puntito de creatividad para que sea más inspirador
    )
    return respuesta.choices[0].message.content

def generar_pagina_web(articulo):
    print("🌐 3/4 Construyendo la interfaz web (index.html)...")
    
    fecha_hoy = datetime.datetime.now().strftime("%d de %B, %Y")
    
    html_template = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nexus 8 | Tech News</title>
    <style>
        body {{
            font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background-color: #0f172a;
            color: #e2e8f0;
            margin: 0;
            padding: 0;
            line-height: 1.6;
        }}
        header {{
            background-color: #1e293b;
            padding: 30px 20px;
            text-align: center;
            border-bottom: 3px solid #0ea5e9;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
        }}
        h1 {{
            margin: 0;
            color: #0ea5e9;
            font-size: 2.8rem;
            letter-spacing: 2px;
        }}
        .subtitle {{
            color: #94a3b8;
            font-size: 1.1rem;
            margin-top: 5px;
        }}
        .container {{
            max-width: 800px;
            margin: 40px auto;
            padding: 30px;
            background-color: #1e293b;
            border-radius: 12px;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
        }}
        .date {{
            display: inline-block;
            background-color: #0ea5e9;
            color: #0f172a;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.85rem;
            margin-bottom: 20px;
            text-transform: uppercase;
        }}
        .content p {{
            font-size: 1.15rem;
            color: #cbd5e1;
            margin-bottom: 20px;
            text-align: justify;
        }}
        footer {{
            text-align: center;
            padding: 30px;
            color: #64748b;
            font-size: 0.9rem;
            margin-top: 20px;
        }}
    </style>
</head>
<body>

    <header>
        <h1>NEXUS 8</h1>
        <div class="subtitle">Radar Tecnológico Automatizado</div>
    </header>

    <div class="container">
        <div class="date">Actualizado: {fecha_hoy}</div>
        <div class="content">
            {articulo}
        </div>
    </div>

    <footer>
        &copy; 2026 Nexus 8. Plataforma generada y curada por Inteligencia Artificial.
    </footer>

</body>
</html>"""

    with open("index.html", "w", encoding="utf-8") as archivo:
        archivo.write(html_template)

# --- EJECUCIÓN DEL PROGRAMA ---
if __name__ == "__main__":
    noticias_crudas = obtener_noticias()
    
    if noticias_crudas:
        articulo_final = procesar_con_ia(noticias_crudas)
        generar_pagina_web(articulo_final)
        
        print("🚀 4/4 ¡Proceso terminado con éxito!")
        print("\n" + "=" * 60)
        print("✅ Abre el archivo 'index.html' en tu navegador web.")
        print("=" * 60 + "\n")