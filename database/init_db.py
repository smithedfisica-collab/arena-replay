from database.database import get_connection


def init_database():

    conn = get_connection()

    cursor = conn.cursor()

    # ======================================================
    # TABELA DE ALUGUÉIS
    # ======================================================

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

            public_token TEXT UNIQUE,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )
        """
    )

    # ======================================================
    # TABELA DE REPLAYS
    # ======================================================

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS replays (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            rental_id INTEGER NOT NULL,

            filename TEXT NOT NULL,

            created_at TEXT,

            FOREIGN KEY (rental_id)
                REFERENCES rentals(id)

        )
        """
    )

    conn.commit()

    conn.close()

    print("=" * 60)
    print("BANCO DE DADOS INICIALIZADO COM SUCESSO")
    print("TABELA RENTALS: OK")
    print("TABELA REPLAYS: OK")
    print("=" * 60)


if __name__ == "__main__":

    init_database()

    print("Banco criado com sucesso!")