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
# VERIFICAR SE COLUNA EXISTE
# ==========================================================

def column_exists(cursor, table_name, column_name):

    cursor.execute(
        f"PRAGMA table_info({table_name})"
    )

    columns = cursor.fetchall()

    return any(
        column["name"] == column_name
        for column in columns
    )


# ==========================================================
# ADICIONAR COLUNA SE NÃO EXISTIR
# ==========================================================

def add_column_if_not_exists(
    cursor,
    table_name,
    column_name,
    column_definition
):

    if not column_exists(
        cursor,
        table_name,
        column_name
    ):

        cursor.execute(
            f"""
            ALTER TABLE {table_name}
            ADD COLUMN {column_name} {column_definition}
            """
        )

        print(
            f"Coluna '{column_name}' adicionada à tabela '{table_name}'."
        )


# ==========================================================
# CRIAR / ATUALIZAR BANCO
# ==========================================================

def init_database():

    conn = get_connection()

    cursor = conn.cursor()


    # ------------------------------------------------------
    # CRIA A TABELA COMPLETA CASO AINDA NÃO EXISTA
    # ------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS rentals (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            customer_name TEXT NOT NULL,

            phone TEXT,

            court TEXT NOT NULL,

            scheduled_date TEXT NOT NULL,

            scheduled_time TEXT NOT NULL,

            duration INTEGER NOT NULL,

            actual_start TEXT,

            actual_end TEXT,

            extra_duration INTEGER DEFAULT 0,

            status TEXT DEFAULT 'AGENDADO',

            public_token TEXT,

            portal_token TEXT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )
        """
    )


    # ------------------------------------------------------
    # ATUALIZA BANCOS ANTIGOS
    # ------------------------------------------------------

    add_column_if_not_exists(
        cursor,
        "rentals",
        "actual_start",
        "TEXT"
    )


    add_column_if_not_exists(
        cursor,
        "rentals",
        "actual_end",
        "TEXT"
    )


    add_column_if_not_exists(
        cursor,
        "rentals",
        "extra_duration",
        "INTEGER DEFAULT 0"
    )


    add_column_if_not_exists(
        cursor,
        "rentals",
        "status",
        "TEXT DEFAULT 'AGENDADO'"
    )


    add_column_if_not_exists(
        cursor,
        "rentals",
        "public_token",
        "TEXT"
    )


    add_column_if_not_exists(
        cursor,
        "rentals",
        "portal_token",
        "TEXT"
    )


    add_column_if_not_exists(
        cursor,
        "rentals",
        "created_at",
        "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
    )


    conn.commit()

    conn.close()

    print(
        "Banco de dados verificado e atualizado com sucesso."
    )


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
# CRIAR ALUGUEL SIMPLES
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
            duration,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            customer_name,
            phone,
            court,
            scheduled_date,
            scheduled_time,
            duration,
            "AGENDADO"
        )
    )

    conn.commit()

    rental_id = cursor.lastrowid

    conn.close()

    return rental_id


# ==========================================================
# INICIALIZAR BANCO AUTOMATICAMENTE
# ==========================================================

init_database()