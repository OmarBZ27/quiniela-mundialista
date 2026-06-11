import sqlite3

conexion = sqlite3.connect("quiniela.db")

cursor = conexion.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS partidos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    local TEXT NOT NULL,
    visitante TEXT NOT NULL,
    fecha TEXT NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS pronosticos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    partido_id INTEGER NOT NULL,
    nombre TEXT NOT NULL,
    apellido TEXT NOT NULL,
    gol_local INTEGER NOT NULL,
    gol_visitante INTEGER NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS resultados (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    partido_id INTEGER UNIQUE,
    gol_local INTEGER NOT NULL,
    gol_visitante INTEGER NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS participantes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    apellido TEXT NOT NULL
)
""")

conexion.commit()
conexion.close()

print("Base de datos creada")