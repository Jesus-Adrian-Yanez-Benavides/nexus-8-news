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
            return datos["articles"][:5]
        return None
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return None

def procesar_con_ia(articulos_crudos):
    print("🧠 2/4 Procesando y dividiendo textos con IA...")
    
    texto_noticias = ""
    for i, art in enumerate(articulos_crudos):
        texto_noticias += f"[{i}] Título: {art['title']}\nDetalle: {art['description']}\n\n"

    # NUEVA INSTRUCCIÓN: Le pedimos el gancho y el texto completo
    instrucciones = """
    Eres el editor principal de 'Nexus 8'. Evalúa las siguientes noticias.
    Devuelve ÚNICAMENTE un arreglo en formato JSON válido. Nada de texto extra.
    Cada objeto del JSON debe tener esta estructura exacta:
    {
      "id_referencia": (el número entre corchetes),
      "titulo": "Título atractivo",
      "gancho": "Una sola frase impactante que invite a leer más (máximo 20 palabras).",
      "contenido_completo": "El artículo detallado y profundo en 3 párrafos.",
      "categoria": "Palabra clave (ej. IA, Gadgets, Software, Hardware)",
      "impacto": "alto" o "bajo"
    }
    """
    
    respuesta = cliente.chat.completions.create(
        messages=[
            {"role": "system", "content": instrucciones},
            {"role": "user", "content": texto_noticias}
        ],
        model="llama-3.3-70b-versatile", 
        temperature=0.3
    )
    
    texto_ia = respuesta.choices[0].message.content
    texto_ia = texto_ia.replace('```json', '').replace('```', '').strip()
    
    try:
        return json.loads(texto_ia)
    except:
        print("❌ Error al procesar el formato de la IA.")
        return []

def actualizar_base_datos(noticias_ia, articulos_crudos):
    print("💾 3/4 Guardando en el historial...")
    fecha_hoy = datetime.datetime.now().strftime("%d/%m/%Y")
    
    nuevas_noticias = []
    for noticia in noticias_ia:
        idx = noticia.get("id_referencia", 0)
        noticia_completa = {
            "fecha": fecha_hoy,
            "titulo": noticia["titulo"],
            "gancho": noticia["gancho"],
            "contenido_completo": noticia["contenido_completo"].replace("\n\n", "</p><p>").replace("\n", "<br>"),
            "categoria": noticia["categoria"],
            "impacto": noticia["impacto"],
            "fuente_nombre": articulos_crudos[idx]["source"]["name"],
            "fuente_url": articulos_crudos[idx]["url"]
        }
        nuevas_noticias.append(noticia_completa)

    historial = []
    if os.path.exists("historial.json"):
        with open("historial.json", "r", encoding="utf-8") as f:
            try:
                historial = json.load(f)
            except:
                pass

    historial_actualizado = nuevas_noticias + historial
    
    with open("historial.json", "w", encoding="utf-8") as f:
        json.dump(historial_actualizado, f, ensure_ascii=False, indent=4)
        
    return historial_actualizado

def generar_pagina_web(historial):
    print("🌐 4/4 Construyendo la nueva interfaz interactiva con Modal...")
    
    html_noticias = ""
    for n in historial:
        clase_impacto = "card-grande" if n["impacto"].lower() == "alto" else "card-pequena"
        
        # --- EL PARCHE MÁGICO ---
        # Si la noticia es vieja y no tiene 'gancho', usamos el 'resumen'. Si no tiene nada, ponemos un texto por defecto.
        texto_gancho = n.get('gancho', n.get('resumen', 'Haz clic para leer el artículo completo...'))
        texto_completo = n.get('contenido_completo', n.get('resumen', 'Contenido no disponible.'))
        # ------------------------

        html_noticias += f"""
        <article class="tarjeta {clase_impacto}" data-titulo="{n['titulo'].lower()}" data-categoria="{n['categoria'].lower()}" onclick="abrirNoticia(this)">
            <span class="etiqueta-categoria">{n['categoria']}</span>
            <span class="etiqueta-fecha">{n['fecha']}</span>
            <h2>{n['titulo']}</h2>
            <div class="contenido"><p>{texto_gancho} <span style="color: #0ea5e9; font-weight: bold;">Leer más...</span></p></div>
            
            <div class="texto-oculto" style="display:none;">
                <p>{texto_completo}</p>
            </div>
            <div class="fuente-oculta" style="display:none;">
                <strong>Fuente original:</strong> <a href="{n['fuente_url']}" target="_blank">{n['fuente_nombre']}</a>
            </div>
        </article>
        """

    # ... (El resto del HTML gigante se queda exactamente igual) ...
    html_template = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nexus 8 | Archivo Global</title>
    <style>
        body {{ font-family: 'Segoe UI', Roboto, sans-serif; background-color: #0f172a; color: #e2e8f0; margin: 0; padding: 0; }}
        header {{ background-color: #1e293b; padding: 40px 20px; text-align: center; border-bottom: 4px solid #0ea5e9; }}
        h1 {{ color: #0ea5e9; font-size: 3rem; margin: 0; letter-spacing: 2px; }}
        
        .controles {{ max-width: 1000px; margin: 30px auto; padding: 0 20px; display: flex; justify-content: center; }}
        input[type="text"] {{ padding: 12px 20px; font-size: 1.1rem; border-radius: 30px; border: none; width: 60%; background: #334155; color: white; outline: none; box-shadow: 0 4px 6px rgba(0,0,0,0.2); }}
        
        .grid-noticias {{ max-width: 1200px; margin: 0 auto 50px; padding: 20px; display: grid; gap: 25px; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); grid-auto-flow: dense; }}
        .tarjeta {{ background: #1e293b; border-radius: 12px; padding: 25px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.4); transition: all 0.3s ease; border: 1px solid #334155; display: flex; flex-direction: column; cursor: pointer; }}
        .tarjeta:hover {{ transform: translateY(-5px); border-color: #0ea5e9; box-shadow: 0 15px 25px -5px rgba(14, 165, 233, 0.3); }}
        
        .card-grande {{ grid-column: span 2; background: linear-gradient(145deg, #1e293b 0%, #172554 100%); border-left: 5px solid #0ea5e9; }}
        .card-grande h2 {{ font-size: 2rem; color: white; }}
        .card-pequena h2 {{ font-size: 1.3rem; color: #bae6fd; }}
        
        .etiqueta-categoria {{ background: #0ea5e9; color: #0f172a; padding: 4px 12px; border-radius: 20px; font-weight: bold; font-size: 0.8rem; text-transform: uppercase; display: inline-block; margin-bottom: 15px; }}
        .etiqueta-fecha {{ color: #64748b; font-size: 0.85rem; float: right; }}
        .contenido p {{ color: #cbd5e1; line-height: 1.6; font-size: 1.1rem; }}
        
        .modal-overlay {{ display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(15, 23, 42, 0.9); z-index: 1000; align-items: center; justify-content: center; backdrop-filter: blur(5px); }}
        .modal-content {{ background: #1e293b; width: 90%; max-width: 800px; max-height: 85vh; border-radius: 15px; padding: 40px; position: relative; overflow-y: auto; border: 1px solid #334155; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5); }}
        .cerrar-btn {{ position: absolute; top: 20px; right: 25px; font-size: 2rem; color: #94a3b8; cursor: pointer; background: none; border: none; transition: color 0.2s; }}
        .cerrar-btn:hover {{ color: #ef4444; }}
        #modal-texto p {{ font-size: 1.15rem; line-height: 1.8; color: #e2e8f0; text-align: justify; margin-bottom: 20px; }}
        #modal-fuente {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #334155; }}
        #modal-fuente a {{ color: #0ea5e9; text-decoration: none; }}
        
        @media (max-width: 768px) {{ .card-grande {{ grid-column: span 1; }} .controles input {{ width: 100%; }} .modal-content{{ padding: 25px; }} }}
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

    <div id="modal-noticia" class="modal-overlay" onclick="cerrarSiClickFuera(event)">
        <div class="modal-content">
            <button class="cerrar-btn" onclick="cerrarModal()">&times;</button>
            <span id="modal-categoria" class="etiqueta-categoria"></span>
            <span id="modal-fecha" class="etiqueta-fecha"></span>
            <h2 id="modal-titulo" style="font-size: 2.2rem; margin-top: 10px;"></h2>
            <div id="modal-texto"></div>
            <div id="modal-fuente"></div>
        </div>
    </div>

    <script>
        function filtrarNoticias() {{
            let input = document.getElementById('buscador').value.toLowerCase();
            let tarjetas = document.getElementsByClassName('tarjeta');
            for (let i = 0; i < tarjetas.length; i++) {{
                let titulo = tarjetas[i].getAttribute('data-titulo');
                let categoria = tarjetas[i].getAttribute('data-categoria');
                tarjetas[i].style.display = (titulo.includes(input) || categoria.includes(input)) ? "" : "none";
            }}
        }}

        function abrirNoticia(elemento) {{
            document.getElementById('modal-categoria').innerText = elemento.querySelector('.etiqueta-categoria').innerText;
            document.getElementById('modal-fecha').innerText = elemento.querySelector('.etiqueta-fecha').innerText;
            document.getElementById('modal-titulo').innerText = elemento.querySelector('h2').innerText;
            document.getElementById('modal-texto').innerHTML = elemento.querySelector('.texto-oculto').innerHTML;
            document.getElementById('modal-fuente').innerHTML = elemento.querySelector('.fuente-oculta').innerHTML;

            document.getElementById('modal-noticia').style.display = 'flex';
            document.body.style.overflow = 'hidden'; 
        }}

        function cerrarModal() {{
            document.getElementById('modal-noticia').style.display = 'none';
            document.body.style.overflow = 'auto';
        }}

        function cerrarSiClickFuera(event) {{
            if (event.target.id === 'modal-noticia') {{
                cerrarModal();
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
