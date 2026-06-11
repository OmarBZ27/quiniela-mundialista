from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)

from db import get_connection

try:

    conexion = get_connection()
    cursor = conexion.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS participantes (
        id SERIAL PRIMARY KEY,
        nombre VARCHAR(100) NOT NULL,
        apellido VARCHAR(100) NOT NULL
    )
    """)

    conexion.commit()
    conexion.close()

    print("POSTGRES OK")

except Exception as e:

    print("ERROR POSTGRES")
    print(e)

@app.route("/")
def inicio():
    return render_template("index.html")

@app.route("/partidos")
def lista_partidos():

    conexion = sqlite3.connect("quiniela.db")
    cursor = conexion.cursor()

    cursor.execute("SELECT * FROM partidos")

    partidos = cursor.fetchall()

    conexion.close()

    return render_template(
        "lista_partidos.html",
        partidos=partidos
    )

@app.route("/participantes", methods=["GET", "POST"])
def participantes():

    conexion = sqlite3.connect("quiniela.db")
    cursor = conexion.cursor()

    if request.method == "POST":

        nombre = request.form["nombre"]
        apellido = request.form["apellido"]

        cursor.execute("""
            INSERT INTO participantes
            (nombre, apellido)
            VALUES (?, ?)
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

    conexion = sqlite3.connect("quiniela.db")
    cursor = conexion.cursor()

    if request.method == "POST":

        participante_id = request.form["participante_id"]
        gol_local = request.form["gol_local"]
        gol_visitante = request.form["gol_visitante"]

        cursor.execute("""
            INSERT INTO pronosticos
            (partido_id, participante_id, gol_local, gol_visitante)
            VALUES (?, ?, ?, ?)
            """, (
            partido_id,
            participante_id,
            gol_local,
            gol_visitante
                ))

        conexion.commit()

    cursor.execute(
        "SELECT * FROM partidos WHERE id = ?",
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
    WHERE partido_id = ?
    """, (partido_id,))

    pronosticos_lista = cursor.fetchall()

    cursor.execute("""
    SELECT
    gol_local,
    gol_visitante,
    COUNT(*) as cantidad
    FROM pronosticos
    WHERE partido_id = ?
    GROUP BY gol_local, gol_visitante
    ORDER BY cantidad DESC
    """, (partido_id,))

    estadisticas = cursor.fetchall()

    cursor.execute("""
    SELECT COUNT(*)
    FROM pronosticos
    WHERE partido_id = ?
    """, (partido_id,))

    total_pronosticos = cursor.fetchone()[0]

    cursor.execute("""
    SELECT id,
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
        WHERE partido_id = ?
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

        conexion = sqlite3.connect("quiniela.db")
        cursor = conexion.cursor()

        cursor.execute("""
            INSERT INTO partidos(local, visitante, fecha)
            VALUES (?, ?, ?)
        """, (local, visitante, fecha))

        conexion.commit()
        conexion.close()

        return redirect("/partidos")

    return render_template("nuevo_partido.html")

@app.route("/ganadores/<int:partido_id>")
def ganadores(partido_id):

    conexion = sqlite3.connect("quiniela.db")
    cursor = conexion.cursor()

    cursor.execute(
        "SELECT * FROM partidos WHERE id = ?",
        (partido_id,)
    )

    partido = cursor.fetchone()

    cursor.execute("""
        SELECT gol_local,
               gol_visitante
        FROM resultados
        WHERE partido_id = ?
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
        WHERE partido_id = ?
          AND pronosticos.gol_local = ?
          AND pronosticos.gol_visitante = ?
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

    conexion = sqlite3.connect("quiniela.db")
    cursor = conexion.cursor()

    if request.method == "POST":

        gol_local = request.form["gol_local"]
        gol_visitante = request.form["gol_visitante"]

        cursor.execute("""
            INSERT OR REPLACE INTO resultados
            (partido_id, gol_local, gol_visitante)
            VALUES (?, ?, ?)
        """, (
            partido_id,
            gol_local,
            gol_visitante
        ))

        conexion.commit()

        conexion.close()

        return redirect("/partidos")

    cursor.execute(
        "SELECT * FROM partidos WHERE id = ?",
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

    conexion = sqlite3.connect("quiniela.db")
    cursor = conexion.cursor()

    cursor.execute(
        "DELETE FROM participantes WHERE id = ?",
        (id,)
    )

    conexion.commit()
    conexion.close()

    return redirect("/participantes")

@app.route("/eliminar-pronostico/<int:id>/<int:partido_id>")
def eliminar_pronostico(id, partido_id):

    conexion = sqlite3.connect("quiniela.db")
    cursor = conexion.cursor()

    cursor.execute(
        "DELETE FROM pronosticos WHERE id = ?",
        (id,)
    )

    conexion.commit()
    conexion.close()

    return redirect(f"/pronosticos/{partido_id}")

@app.route("/eliminar-partido/<int:id>")
def eliminar_partido(id):

    conexion = sqlite3.connect("quiniela.db")
    cursor = conexion.cursor()

    cursor.execute(
        "DELETE FROM partidos WHERE id = ?",
        (id,)
    )

    cursor.execute(
        "DELETE FROM pronosticos WHERE partido_id = ?",
        (id,)
    )

    cursor.execute(
        "DELETE FROM resultados WHERE partido_id = ?",
        (id,)
    )

    conexion.commit()
    conexion.close()

    return redirect("/partidos")    

@app.route("/test-postgres")
def test_postgres():

        from db import get_connection

        conexion = get_connection()
        cursor = conexion.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS prueba (
            id SERIAL PRIMARY KEY,
            nombre VARCHAR(50)
        )
        """)

        conexion.commit()
        conexion.close()

        return "Tabla creada correctamente"

if __name__ == "__main__":
    app.run(debug=True)