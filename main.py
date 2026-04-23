import requests
from groq import Groq
import datetime
import json
import os

# --- 1. CONFIGURACIÓN ---
NEWS_API_KEY = os.environ.get("NEWS_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

cliente = Groq(api_key=GROQ_API_KEY)

def obtener_noticias():
    print("🌍 1/4 Buscando noticias en NewsAPI...")
    url = f"https://newsapi.org/v2/everything?q=tecnología&language=es&sortBy=publishedAt&pageSize=5&apiKey={NEWS_API_KEY}"
    try:
        respuesta = requests.get(url, timeout=10)
        datos = respuesta.json()
        if datos.get("status") == "ok" and len(datos.get("articles", [])) > 0:
            return datos["articles"][:5] # Devolvemos los datos crudos para extraer los links luego
        return None
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return None

def procesar_con_ia(articulos_crudos):
    print("🧠 2/4 Procesando y clasificando con IA...")
    
    texto_noticias = ""
    for i, art in enumerate(articulos_crudos):
        texto_noticias += f"[{i}] Título: {art['title']}\nDetalle: {art['description']}\n\n"

    # Obligamos a la IA a devolver un formato de base de datos exacto
    instrucciones = """
    Eres el editor principal de 'Nexus 8'. Evalúa las siguientes noticias.
    Devuelve ÚNICAMENTE un arreglo en formato JSON válido. Nada de texto extra.
    Cada objeto del JSON debe tener esta estructura exacta:
    {
      "id_referencia": (el número que te di entre corchetes),
      "titulo": "Título atractivo y moderno",
      "resumen": "Resumen dinámico de 2 párrafos cortos.",
      "categoria": "Palabra clave (ej. IA, Gadgets, Software, Espacio)",
      "impacto": "alto" (asigna esto solo a la 1 o 2 noticias más revolucionarias) o "bajo" (para las demás)
    }
    """
    
    respuesta = cliente.chat.completions.create(
        messages=[
            {"role": "system", "content": instrucciones},
            {"role": "user", "content": texto_noticias}
        ],
        model="llama-3.3-70b-versatile", 
        temperature=0.3 # Temperatura baja para que no se equivoque en el formato JSON
    )
    
    texto_ia = respuesta.choices[0].message.content
    # Limpiamos por si la IA añade formato markdown
    texto_ia = texto_ia.replace('```json', '').replace('```', '').strip()
    
    try:
        noticias_procesadas = json.loads(texto_ia)
        return noticias_procesadas
    except:
        print("❌ Error al procesar el formato de la IA.")
        return []

def actualizar_base_datos(noticias_ia, articulos_crudos):
    print("💾 3/4 Guardando en el historial...")
    fecha_hoy = datetime.datetime.now().strftime("%d/%m/%Y")
    
    # Enlazamos los textos de la IA con los links originales de la API
    nuevas_noticias = []
    for noticia in noticias_ia:
        idx = noticia.get("id_referencia", 0)
        noticia_completa = {
            "fecha": fecha_hoy,
            "titulo": noticia["titulo"],
            "resumen": noticia["resumen"].replace("\n\n", "</p><p>").replace("\n", "<br>"),
            "categoria": noticia["categoria"],
            "impacto": noticia["impacto"],
            "fuente_nombre": articulos_crudos[idx]["source"]["name"],
            "fuente_url": articulos_crudos[idx]["url"]
        }
        nuevas_noticias.append(noticia_completa)

    # Leemos el historial anterior si existe
    historial = []
    if os.path.exists("historial.json"):
        with open("historial.json", "r", encoding="utf-8") as f:
            try:
                historial = json.load(f)
            except:
                pass

    # Agregamos las nuevas arriba (las más recientes primero)
    historial_actualizado = nuevas_noticias + historial
    
    with open("historial.json", "w", encoding="utf-8") as f:
        json.dump(historial_actualizado, f, ensure_ascii=False, indent=4)
        
    return historial_actualizado

def generar_pagina_web(historial):
    print("🌐 4/4 Construyendo la nueva interfaz interactiva...")
    
    html_noticias = ""
    for n in historial:
        # Clases dinámicas basadas en el impacto
        clase_impacto = "card-grande" if n["impacto"].lower() == "alto" else "card-pequena"
        
        html_noticias += f"""
        <article class="tarjeta {clase_impacto}" data-titulo="{n['titulo'].lower()}" data-categoria="{n['categoria'].lower()}">
            <span class="etiqueta-categoria">{n['categoria']}</span>
            <span class="etiqueta-fecha">{n['fecha']}</span>
            <h2>{n['titulo']}</h2>
            <div class="contenido"><p>{n['resumen']}</p></div>
            <div class="bibliografia">
                <strong>Fuente:</strong> <a href="{n['fuente_url']}" target="_blank">{n['fuente_nombre']}</a>
            </div>
        </article>
        """

    html_template = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nexus 8 | Archivo Global</title>
    <style>
        body {{
            font-family: 'Segoe UI', Roboto, sans-serif;
            background-color: #0f172a; color: #e2e8f0; margin: 0; padding: 0;
        }}
        header {{
            background-color: #1e293b; padding: 40px 20px; text-align: center;
            border-bottom: 4px solid #0ea5e9;
        }}
        h1 {{ color: #0ea5e9; font-size: 3rem; margin: 0; letter-spacing: 2px; }}
        
        /* Buscador */
        .controles {{
            max-width: 1000px; margin: 30px auto; padding: 0 20px;
            display: flex; gap: 15px; justify-content: center;
        }}
        input[type="text"] {{
            padding: 12px 20px; font-size: 1.1rem; border-radius: 30px;
            border: none; width: 60%; background: #334155; color: white;
            outline: none; box-shadow: 0 4px 6px rgba(0,0,0,0.2);
        }}
        input[type="text"]::placeholder {{ color: #94a3b8; }}
        
        /* Grid Asimétrico */
        .grid-noticias {{
            max-width: 1200px; margin: 0 auto 50px; padding: 20px;
            display: grid; gap: 25px;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            /* Permite que las tarjetas grandes ocupen más espacio */
            grid-auto-flow: dense;
        }}
        .tarjeta {{
            background: #1e293b; border-radius: 12px; padding: 25px;
            box-shadow: 0 10px 15px -3px rgba(0,0,0,0.4);
            transition: transform 0.2s; border: 1px solid #334155;
            display: flex; flex-direction: column; justify-content: space-between;
        }}
        .tarjeta:hover {{ transform: translateY(-5px); border-color: #0ea5e9; }}
        
        /* Clases de Impacto */
        .card-grande {{
            grid-column: span 2; /* Ocupa doble ancho */
            background: linear-gradient(145deg, #1e293b 0%, #172554 100%);
            border-left: 5px solid #0ea5e9;
        }}
        .card-grande h2 {{ font-size: 2rem; color: white; }}
        .card-pequena h2 {{ font-size: 1.3rem; color: #bae6fd; }}
        
        /* Metadatos */
        .etiqueta-categoria {{
            background: #0ea5e9; color: #0f172a; padding: 4px 12px;
            border-radius: 20px; font-weight: bold; font-size: 0.8rem;
            text-transform: uppercase; display: inline-block; margin-bottom: 15px;
        }}
        .etiqueta-fecha {{ color: #64748b; font-size: 0.85rem; float: right; }}
        .contenido p {{ color: #cbd5e1; line-height: 1.6; font-size: 1rem; text-align: justify; }}
        .card-grande .contenido p {{ font-size: 1.15rem; }}
        
        /* Bibliografía */
        .bibliografia {{
            margin-top: 20px; padding-top: 15px; border-top: 1px solid #334155;
            font-size: 0.9rem; color: #94a3b8;
        }}
        .bibliografia a {{ color: #38bdf8; text-decoration: none; font-weight: bold; }}
        .bibliografia a:hover {{ text-decoration: underline; }}
        
        @media (max-width: 768px) {{
            .card-grande {{ grid-column: span 1; }} /* En celular todo es 1 columna */
            .controles input {{ width: 100%; }}
        }}
    </style>
</head>
<body>

    <header>
        <h1>NEXUS 8</h1>
        <p style="color: #94a3b8; font-size: 1.2rem;">Radar Tecnológico | Base de Datos Interactiva</p>
    </header>

    <div class="controles">
        <input type="text" id="buscador" onkeyup="filtrarNoticias()" placeholder="Buscar por palabra clave o categoría (ej. Hardware)...">
    </div>

    <div class="grid-noticias" id="contenedor-noticias">
        {html_noticias}
    </div>

    <script>
        // Lógica del Motor de Búsqueda
        function filtrarNoticias() {{
            let input = document.getElementById('buscador').value.toLowerCase();
            let tarjetas = document.getElementsByClassName('tarjeta');
            
            for (let i = 0; i < tarjetas.length; i++) {{
                let titulo = tarjetas[i].getAttribute('data-titulo');
                let categoria = tarjetas[i].getAttribute('data-categoria');
                
                if (titulo.includes(input) || categoria.includes(input)) {{
                    tarjetas[i].style.display = "";
                }} else {{
                    tarjetas[i].style.display = "none";
                }}
            }}
        }}
    </script>
</body>
</html>"""

    with open("index.html", "w", encoding="utf-8") as archivo:
        archivo.write(html_template)

if __name__ == "__main__":
    articulos = obtener_noticias()
    if articulos:
        noticias_ia = procesar_con_ia(articulos)
        if noticias_ia:
            historial = actualizar_base_datos(noticias_ia, articulos)
            generar_pagina_web(historial)
            print("🚀 ¡Todo listo! La base de datos y la web han sido actualizadas.")
