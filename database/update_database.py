import sqlite3


conn = sqlite3.connect("arena.db")
conn.row_factory = sqlite3.Row

cursor = conn.cursor()


# ======================================================
# TABELA DE REPLAYS
# ======================================================

cursor.execute("""
    CREATE TABLE IF NOT EXISTS replays (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        rental_id INTEGER NOT NULL,

        filename TEXT NOT NULL,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (rental_id) REFERENCES rentals(id)

    )
""")


conn.commit()


# ======================================================
# VERIFICAÇÃO
# ======================================================

print("Tabela 'replays' verificada/criada com sucesso.")


cursor.execute("""
    SELECT
        id,
        customer_name,
        public_token
    FROM rentals
    ORDER BY id DESC
""")


for row in cursor.fetchall():
    print(dict(row))


conn.close()