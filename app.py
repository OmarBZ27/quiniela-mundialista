from flask import Flask, render_template, request, redirect
from db import get_connection
from datetime import datetime

app = Flask(__name__)

@app.route("/")
def inicio():
    return render_template("index.html")

@app.route("/partidos")
def lista_partidos():

    conexion = get_connection()
    cursor = conexion.cursor()

    cursor.execute("SELECT * FROM partidos")

    partidos = cursor.fetchall()

    partidos_formateados = []

    for p in partidos:

        fecha_bonita = p[3].strftime("%d-%m-%Y")

        partidos_formateados.append(
            (p[0], p[1], p[2], fecha_bonita)
        )

    partidos = partidos_formateados

    conexion.close()

    return render_template(
        "lista_partidos.html",
        partidos=partidos
    )

@app.route("/participantes", methods=["GET", "POST"])
def participantes():

    conexion = get_connection()
    cursor = conexion.cursor()

    if request.method == "POST":

        nombre = request.form["nombre"]
        apellido = request.form["apellido"]

        cursor.execute("""
            INSERT INTO participantes
            (nombre, apellido)
            VALUES (%s, %s)
        """, (
            nombre,
            apellido
        ))

        conexion.commit()

    cursor.execute("""
        SELECT *
        FROM participantes
        ORDER BY apellido, nombre
    """)

    lista = cursor.fetchall()

    conexion.close()

    return render_template(
        "participantes.html",
        participantes=lista
    )

@app.route("/pronosticos/<int:partido_id>", methods=["GET", "POST"])
def pronosticos(partido_id):

    conexion = get_connection()
    cursor = conexion.cursor()

    if request.method == "POST":

        participante_id = request.form["participante_id"]
        gol_local = request.form["gol_local"]
        gol_visitante = request.form["gol_visitante"]

        cursor.execute("""
            INSERT INTO pronosticos
            (partido_id, participante_id, gol_local, gol_visitante)
            VALUES (%s, %s, %s, %s)
        """, (
            partido_id,
            participante_id,
            gol_local,
            gol_visitante
        ))

        conexion.commit()
        conexion.close()

        return redirect(f"/pronosticos/{partido_id}")

    cursor.execute(
        "SELECT * FROM partidos WHERE id = %s",
        (partido_id,)
    )

    partido = cursor.fetchone()

    cursor.execute("""
        SELECT
            pronosticos.id,
            participantes.nombre || ' ' || participantes.apellido,
            pronosticos.gol_local,
            pronosticos.gol_visitante
        FROM pronosticos
        INNER JOIN participantes
            ON participantes.id = pronosticos.participante_id
        WHERE partido_id = %s
    """, (partido_id,))

    pronosticos_lista = cursor.fetchall()

    cursor.execute("""
        SELECT
            gol_local,
            gol_visitante,
            COUNT(*) as cantidad
        FROM pronosticos
        WHERE partido_id = %s
        GROUP BY gol_local, gol_visitante
        ORDER BY cantidad DESC
    """, (partido_id,))

    estadisticas = cursor.fetchall()

    cursor.execute("""
        SELECT COUNT(*)
        FROM pronosticos
        WHERE partido_id = %s
    """, (partido_id,))

    total_pronosticos = cursor.fetchone()[0]

    cursor.execute("""
        SELECT
            id,
            nombre,
            apellido
        FROM participantes
        ORDER BY apellido, nombre
    """)

    participantes = cursor.fetchall()

    cursor.execute("""
        SELECT
            nombre,
            apellido
        FROM participantes
        WHERE id NOT IN (
            SELECT participante_id
            FROM pronosticos
            WHERE partido_id = %s
        )
        ORDER BY apellido, nombre
    """, (partido_id,))

    faltantes = cursor.fetchall()

    conexion.close()

    return render_template(
        "pronosticos.html",
        partido=partido,
        pronosticos=pronosticos_lista,
        participantes=participantes,
        estadisticas=estadisticas,
        total_pronosticos=total_pronosticos,
        faltantes=faltantes
    )

@app.route("/nuevo-partido", methods=["GET", "POST"])
def nuevo_partido():

    if request.method == "POST":

        local = request.form["local"]
        visitante = request.form["visitante"]
        fecha = request.form["fecha"]

        conexion = get_connection()
        cursor = conexion.cursor()

        cursor.execute("""
            INSERT INTO partidos(local, visitante, fecha)
            VALUES (%s, %s, %s)
        """, (local, visitante, fecha))

        conexion.commit()
        conexion.close()

        return redirect("/partidos")

    return render_template("nuevo_partido.html")

@app.route("/ganadores/<int:partido_id>")
def ganadores(partido_id):

    conexion = get_connection()
    cursor = conexion.cursor()

    cursor.execute(
        "SELECT * FROM partidos WHERE id = %s",
        (partido_id,)
    )

    partido = cursor.fetchone()

    cursor.execute("""
        SELECT gol_local,
               gol_visitante
        FROM resultados
        WHERE partido_id = %s
    """, (partido_id,))

    resultado = cursor.fetchone()

    if not resultado:
        conexion.close()
        return "Este partido aún no tiene resultado."

    cursor.execute("""
        SELECT
            participantes.nombre || ' ' || participantes.apellido
        FROM pronosticos
        INNER JOIN participantes
            ON participantes.id = pronosticos.participante_id
        WHERE partido_id = %s
          AND pronosticos.gol_local = %s
          AND pronosticos.gol_visitante = %s
    """, (
        partido_id,
        resultado[0],
        resultado[1]
    ))

    ganadores = cursor.fetchall()

    conexion.close()

    return render_template(
        "ganadores.html",
        partido=partido,
        resultado=resultado,
        ganadores=ganadores
    )

@app.route("/resultado/<int:partido_id>", methods=["GET", "POST"])
def resultado(partido_id):

    conexion = get_connection()
    cursor = conexion.cursor()

    if request.method == "POST":

        gol_local = request.form["gol_local"]
        gol_visitante = request.form["gol_visitante"]

        cursor.execute("""
            INSERT INTO resultados
            (partido_id, gol_local, gol_visitante)
            VALUES (%s, %s, %s)
            ON CONFLICT (partido_id)
            DO UPDATE SET
                gol_local = EXCLUDED.gol_local,
                gol_visitante = EXCLUDED.gol_visitante
        """, (
            partido_id,
            gol_local,
            gol_visitante
        ))

        conexion.commit()
        conexion.close()

        return redirect("/partidos")

    cursor.execute(
        "SELECT * FROM partidos WHERE id = %s",
        (partido_id,)
    )

    partido = cursor.fetchone()

    conexion.close()

    return render_template(
        "resultado.html",
        partido=partido
    )
@app.route("/eliminar-participante/<int:id>")
def eliminar_participante(id):

    conexion = get_connection()
    cursor = conexion.cursor()

    cursor.execute(
        "DELETE FROM participantes WHERE id = %s",
        (id,)
    )

    conexion.commit()
    conexion.close()

    return redirect("/participantes")

@app.route("/eliminar-pronostico/<int:id>/<int:partido_id>")
def eliminar_pronostico(id, partido_id):

    conexion = get_connection()
    cursor = conexion.cursor()

    cursor.execute(
        "DELETE FROM pronosticos WHERE id = %s",
        (id,)
    )

    conexion.commit()
    conexion.close()

    return redirect(f"/pronosticos/{partido_id}")

@app.route("/eliminar-partido/<int:id>")
def eliminar_partido(id):

    conexion = get_connection()
    cursor = conexion.cursor()

    cursor.execute(
        "DELETE FROM partidos WHERE id = %s",
        (id,)
    )

    cursor.execute(
        "DELETE FROM pronosticos WHERE partido_id = %s",
        (id,)
    )

    cursor.execute(
        "DELETE FROM resultados WHERE partido_id = %s",
        (id,)
    )

    conexion.commit()
    conexion.close()

    return redirect("/partidos")    

@app.route("/crear-tablas")
def crear_tablas():

    conexion = get_connection()
    cursor = conexion.cursor()

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

    return "Tablas creadas"

if __name__ == "__main__":
    app.run(debug=True)