import os
import psycopg

def get_connection():

    database_url = os.getenv("DATABASE_URL")

    return psycopg.connect(database_url)