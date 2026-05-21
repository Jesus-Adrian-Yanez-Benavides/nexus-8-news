import json
import sqlite3
import os

def crear_base_datos():
    conexion = sqlite3.connect("nexus.db")
    cursor = conexion.cursor()
    
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
    
    conexion.commit()
    return conexion

def migrar_datos(conexion):
    if not os.path.exists("historial.json"):
        print("No se encontró historial.json, nada que migrar.")
        return
        
    with open("historial.json", "r", encoding="utf-8") as f:
        try:
            historial = json.load(f)
        except:
            print("Error al leer historial.json.")
            return

    cursor = conexion.cursor()
    insertadas = 0
    duplicadas = 0
    
    for n in historial:
        # Algunos campos pueden no existir si la estructura varió, usamos fallback
        try:
            cursor.execute('''
            INSERT INTO noticias (fecha, titulo, gancho, contenido_completo, categoria, impacto, fuente_nombre, fuente_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                n.get('fecha', ''),
                n.get('titulo', ''),
                n.get('gancho', n.get('resumen', '')),
                n.get('contenido_completo', n.get('resumen', '')),
                n.get('categoria', ''),
                n.get('impacto', ''),
                n.get('fuente_nombre', ''),
                n.get('fuente_url', '')
            ))
            insertadas += 1
        except sqlite3.IntegrityError:
            duplicadas += 1
            
    conexion.commit()
    print(f"Migración completada. Insertadas: {insertadas}, Duplicadas (ignoradas): {duplicadas}")

if __name__ == "__main__":
    print("Iniciando migración a SQLite...")
    conn = crear_base_datos()
    migrar_datos(conn)
    conn.close()
    print("Migración finalizada.")
