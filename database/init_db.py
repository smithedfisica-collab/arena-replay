from database.database import get_connection


def init_db():

    conn = get_connection()
    cursor = conn.cursor()

    # Cria a tabela caso ela ainda não exista
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

    # Verifica quais colunas já existem na tabela
    cursor.execute("PRAGMA table_info(rentals)")
    columns = [column[1] for column in cursor.fetchall()]

    # Adiciona a coluna status caso ela não exista
    if "status" not in columns:
        cursor.execute("""
            ALTER TABLE rentals
            ADD COLUMN status TEXT DEFAULT 'AGENDADO'
        """)

    # Adiciona portal_token caso ele não exista
    if "portal_token" not in columns:
        cursor.execute("""
            ALTER TABLE rentals
            ADD COLUMN portal_token TEXT
        """)

    # Adiciona extra_duration caso ele não exista
    if "extra_duration" not in columns:
        cursor.execute("""
            ALTER TABLE rentals
            ADD COLUMN extra_duration INTEGER DEFAULT 0
        """)

    conn.commit()
    conn.close()


if __name__ == "__main__":

    init_db()

    print("Banco atualizado com sucesso!")