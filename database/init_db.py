from database.database import get_connection


def init_db():

    conn = get_connection()

    cursor = conn.cursor()

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

    conn.commit()

    conn.close()


if __name__ == "__main__":

    init_db()

    print("Banco criado com sucesso!")