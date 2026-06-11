from db import get_connection

print("Intentando conectar...")

conexion = get_connection()

print("Conectado correctamente")

cursor = conexion.cursor()

print("Creando tablas...")

cursor.execute("""
CREATE TABLE IF NOT EXISTS participantes (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS partidos (
    id SERIAL PRIMARY KEY,
    local VARCHAR(100) NOT NULL,
    visitante VARCHAR(100) NOT NULL,
    fecha VARCHAR(100) NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS pronosticos (
    id SERIAL PRIMARY KEY,
    partido_id INTEGER NOT NULL,
    participante_id INTEGER NOT NULL,
    gol_local INTEGER NOT NULL,
    gol_visitante INTEGER NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS resultados (
    id SERIAL PRIMARY KEY,
    partido_id INTEGER UNIQUE,
    gol_local INTEGER NOT NULL,
    gol_visitante INTEGER NOT NULL
)
""")

conexion.commit()
conexion.close()

print("Tablas creadas correctamente")