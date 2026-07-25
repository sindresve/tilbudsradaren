from db.database import get_connection

def create_catalog(store, info):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO catalogs(
        store,
        year,
        week
    )

    VALUES (?, ?, ?)
    """, 
    (
        store, 
        info["year"], 
        info["week"])
    )


    catalog_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return catalog_id

def save_products(products, catalog_id):
    conn = get_connection()
    cursor = conn.cursor()

    for product in products:
        cursor.execute("""
        INSERT INTO products(
            catalog_id,
            product_name,
            brand,
            category,
            current_price,
            old_price,
            discount_percent,
            price_per_kg,
            unit_type,
            package_size
        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            catalog_id,
            product.get("product_name"),
            product.get("brand"),
            product.get("category"),
            product.get("current_price"),
            product.get("old_price"),
            product.get("discount_percent"),
            product.get("price_per_kg"),
            product.get("unit_type"),
            product.get("package_size")
        ))

        product_id = cursor.lastrowid

        for term in product.get("search_terms", []):
            cursor.execute("""
            INSERT INTO product_search_terms(
                product_id,
                term
            )
            VALUES (?, ?)
            """, (
                product_id,
                term.lower().strip()
            ))

    conn.commit()
    conn.close()