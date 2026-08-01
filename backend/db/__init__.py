from db.database import get_connection

KNOWN_STORES = {
    "europris": "image",
    "rema": "image",
    "kiwi": "pdf",
    "coopExtra": "pdf",
    "meny": "pdf",
}

ALLERGIES = ["gluten", "laktose", "nøtter", "egg", "skalldyr"]

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
        discount_percent REAL,


        FOREIGN KEY(catalog_id)
            REFERENCES catalogs(id)
    )
    """)


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        id INTEGER PRIMARY KEY CHECK (id = 1),

        discord_webhook_url TEXT,
        webhook_enabled BOOLEAN NOT NULL DEFAULT 0,

        smtp_host TEXT,
        smtp_port INTEGER,
        smtp_username TEXT,
        smtp_password TEXT,
        email_to TEXT,
        smtp_enabled BOOLEAN NOT NULL DEFAULT 0,

        gemini_api_key TEXT,

        postal_code TEXT,
        weekly_budget REAL,

        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS store_toggles (
        store TEXT PRIMARY KEY,
        enabled BOOLEAN NOT NULL DEFAULT 1
    )
    """)


    for store in KNOWN_STORES:
        cursor.execute("""
        INSERT OR IGNORE INTO store_toggles (store, enabled)
        VALUES (?, 1)
        """, (store,))

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS allergens (
        allergy TEXT PRIMARY KEY,
        enabled BOOLEAN NOT NULL DEFAULT 1
    )
    """)

    for allergy in ALLERGIES:
        cursor.execute("""
        INSERT OR IGNORE INTO allergens (allergy, enabled)
        VALUES (?, 1)
        """, (allergy,))

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS staples (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS product_search_terms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        term TEXT NOT NULL,

        FOREIGN KEY(product_id)
            REFERENCES products(id)
            ON DELETE CASCADE
    )
    """)

    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_product_search_term
    ON product_search_terms(term)
    """)


    cursor.execute("""
    INSERT OR IGNORE INTO settings (id)
    VALUES (1)
    """)


    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()