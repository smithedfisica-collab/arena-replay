from database.database import get_connection


def init_database():

    conn = get_connection()

    cursor = conn.cursor()

    # ==========================================================
    # CRIA A TABELA, CASO ELA AINDA NÃO EXISTA
    # ==========================================================

    cursor.execute("""
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

            portal_token TEXT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )
    """)


    # ==========================================================
    # VERIFICA AS COLUNAS EXISTENTES
    # ==========================================================

    cursor.execute("PRAGMA table_info(rentals)")

    columns = [
        column[1]
        for column in cursor.fetchall()
    ]


    # ==========================================================
    # ADICIONA AS NOVAS COLUNAS CASO NÃO EXISTAM
    # ==========================================================

    if "actual_start" not in columns:

        cursor.execute("""
            ALTER TABLE rentals
            ADD COLUMN actual_start TEXT
        """)


    if "actual_end" not in columns:

        cursor.execute("""
            ALTER TABLE rentals
            ADD COLUMN actual_end TEXT
        """)


    if "extra_duration" not in columns:

        cursor.execute("""
            ALTER TABLE rentals
            ADD COLUMN extra_duration INTEGER DEFAULT 0
        """)


    if "status" not in columns:

        cursor.execute("""
            ALTER TABLE rentals
            ADD COLUMN status TEXT DEFAULT 'AGENDADO'
        """)


    if "portal_token" not in columns:

        cursor.execute("""
            ALTER TABLE rentals
            ADD COLUMN portal_token TEXT
        """)


    conn.commit()

    conn.close()


    print("=" * 60)
    print("BANCO DE DADOS VERIFICADO COM SUCESSO!")
    print("TABELA RENTALS ATUALIZADA.")
    print("=" * 60)


if __name__ == "__main__":

    init_database()

    print("Banco criado/atualizado com sucesso!")