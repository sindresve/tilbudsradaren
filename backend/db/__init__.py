from db.database import get_connection


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS catalogs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        store TEXT NOT NULL,
        year INTEGER NOT NULL,
        week INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        catalog_id INTEGER NOT NULL,
        product_name TEXT NOT NULL,
        brand TEXT,
        category TEXT,
        current_price REAL,
        old_price REAL,
        price_per_kg REAL,
        unit_type TEXT,
        package_size TEXT,
        source_image TEXT,

        FOREIGN KEY(catalog_id)
            REFERENCES catalogs(id)
    )
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()