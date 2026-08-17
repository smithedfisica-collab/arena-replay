import sqlite3
import os


# ==========================================================
# CAMINHO ABSOLUTO DO BANCO
# ==========================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


DATABASE = os.path.join(
    BASE_DIR,
    "arena.db"
)


print("=" * 60)
print("BANCO DE DADOS UTILIZADO:")
print(DATABASE)
print("=" * 60)


# ==========================================================
# CONEXÃO
# ==========================================================

def get_connection():

    conn = sqlite3.connect(
        DATABASE
    )

    conn.row_factory = sqlite3.Row

    return conn


# ==========================================================
# BUSCAR ALUGUÉIS
# ==========================================================

def get_all_rentals():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(

        """
        SELECT *
        FROM rentals
        ORDER BY id DESC
        """

    )

    rentals = cursor.fetchall()

    conn.close()

    return rentals


# ==========================================================
# CRIAR ALUGUEL
# ==========================================================

def create_rental(
    customer_name,
    phone,
    court,
    scheduled_date,
    scheduled_time,
    duration
):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(

        """
        INSERT INTO rentals
        (
            customer_name,
            phone,
            court,
            scheduled_date,
            scheduled_time,
            duration
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,

        (

            customer_name,
            phone,
            court,
            scheduled_date,
            scheduled_time,
            duration

        )

    )

    conn.commit()

    conn.close()