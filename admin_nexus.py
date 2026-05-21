import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3
import datetime
import json
import os
import sys

# Obtener la ruta absoluta del directorio del script para evitar errores al hacer doble clic
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "nexus.db")
JS_PATH = os.path.join(BASE_DIR, "historial_datos.js")

def guardar_noticia():
    titulo = entry_titulo.get().strip()
    gancho = entry_gancho.get().strip()
    categoria = entry_categoria.get().strip()
    contenido = text_contenido.get("1.0", tk.END).strip()
    
    if not titulo or not gancho or not contenido or not categoria:
        messagebox.showerror("Error", "Todos los campos son obligatorios.")
        return
        
    fecha_hoy = datetime.datetime.now().strftime("%d/%m/%Y")
    impacto = "alto" # Por defecto para locales
    fuente_nombre = "Actualización Local"
    # Generar URL falsa única para evitar constraint
    fuente_url = f"local_nexus_{datetime.datetime.now().timestamp()}"
    
    # Formatear el contenido para HTML (saltos de línea)
    contenido_formateado = contenido.replace("\n\n", "</p><p>").replace("\n", "<br>")
    
    try:
        conexion = sqlite3.connect(DB_PATH)
        cursor = conexion.cursor()
        
        # Insertar a BD
        cursor.execute('''
        INSERT INTO noticias (fecha, titulo, gancho, contenido_completo, categoria, impacto, fuente_nombre, fuente_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (fecha_hoy, titulo, gancho, contenido_formateado, categoria, impacto, fuente_nombre, fuente_url))
        
        conexion.commit()
        
        # Regenerar JS
        cursor.execute("SELECT fecha, titulo, gancho, contenido_completo, categoria, impacto, fuente_nombre, fuente_url FROM noticias ORDER BY id DESC")
        filas = cursor.fetchall()
        
        historial = []
        for f in filas:
            historial.append({
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
        
        # Sobrescribir JS
        contenido_js = f"const historial_noticias = {json.dumps(historial, ensure_ascii=False, indent=4)};\n"
        with open(JS_PATH, "w", encoding="utf-8") as archivo:
            archivo.write(contenido_js)
            
        messagebox.showinfo("Éxito", "¡Actualización de Nexus 8 publicada correctamente!\nEl archivo historial_datos.js ha sido actualizado.")
        
        # Limpiar formulario
        entry_titulo.delete(0, tk.END)
        entry_gancho.delete(0, tk.END)
        text_contenido.delete("1.0", tk.END)
        
    except Exception as e:
        messagebox.showerror("Error", f"Ocurrió un error al guardar: {str(e)}")

# --- UI Setup ---
root = tk.Tk()
root.title("Nexus 8 - Panel de Administración")
root.geometry("600x650")
root.configure(bg="#0B0F19")

style = ttk.Style()
style.theme_use('clam')

# Custom styles
bg_color = "#0B0F19"
fg_color = "#f8fafc"
accent = "#0ea5e9"

label_font = ("Segoe UI", 11, "bold")

frame = tk.Frame(root, bg=bg_color, padx=20, pady=20)
frame.pack(fill=tk.BOTH, expand=True)

# Header
tk.Label(frame, text="NEXUS 8 - NUEVA ACTUALIZACIÓN", font=("Segoe UI", 16, "bold"), bg=bg_color, fg=accent).pack(pady=(0, 20))

# Titulo
tk.Label(frame, text="Título de la noticia:", font=label_font, bg=bg_color, fg=fg_color).pack(anchor="w")
entry_titulo = tk.Entry(frame, width=50, font=("Segoe UI", 11), bg="#1e293b", fg="white", insertbackground="white", relief="flat")
entry_titulo.pack(fill=tk.X, pady=(5, 15), ipady=5)

# Categoria
tk.Label(frame, text="Categoría (ej. Mantenimiento, Eventos):", font=label_font, bg=bg_color, fg=fg_color).pack(anchor="w")
entry_categoria = tk.Entry(frame, width=50, font=("Segoe UI", 11), bg="#1e293b", fg="white", insertbackground="white", relief="flat")
entry_categoria.insert(0, "Aviso General")
entry_categoria.pack(fill=tk.X, pady=(5, 15), ipady=5)

# Gancho
tk.Label(frame, text="Gancho (resumen corto para la tarjeta):", font=label_font, bg=bg_color, fg=fg_color).pack(anchor="w")
entry_gancho = tk.Entry(frame, width=50, font=("Segoe UI", 11), bg="#1e293b", fg="white", insertbackground="white", relief="flat")
entry_gancho.pack(fill=tk.X, pady=(5, 15), ipady=5)

# Contenido
tk.Label(frame, text="Contenido Completo (usa Enter para párrafos):", font=label_font, bg=bg_color, fg=fg_color).pack(anchor="w")
text_contenido = tk.Text(frame, height=10, font=("Segoe UI", 11), bg="#1e293b", fg="white", insertbackground="white", relief="flat")
text_contenido.pack(fill=tk.BOTH, expand=True, pady=(5, 20))

# Boton Publicar
btn_publicar = tk.Button(frame, text="PUBLICAR EN NEXUS 8", font=("Segoe UI", 12, "bold"), bg="#8b5cf6", fg="white", 
                         activebackground="#7c3aed", activeforeground="white", relief="flat", cursor="hand2", command=guardar_noticia)
btn_publicar.pack(fill=tk.X, ipady=10)

root.mainloop()
