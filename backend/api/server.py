from datetime import date
from typing import Optional

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from db.database import get_connection

app = FastAPI(title="Discount Catalog API")

# Allow your frontend (adjust origins for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def current_year_week() -> tuple[int, int]:
    iso = date.today().isocalendar()
    return iso.year, iso.week


def row_to_dict(row):
    return dict(row)


@app.get("/api/products")
def get_products(
    store: Optional[str] = Query(None, description="Filter by store, e.g. 'rema'"),
    year: Optional[int] = Query(None, description="Override year (defaults to current)"),
    week: Optional[int] = Query(None, description="Override week (defaults to current)"),
    all_weeks: bool = Query(False, description="If true, ignore year/week filter entirely"),
):
    """
    Return products joined with their catalog info.
    Defaults to the current ISO year/week unless all_weeks=true.
    """
    conn = get_connection()
    cursor = conn.cursor()

    filters = []
    params: list = []

    if not all_weeks:
        y, w = (year, week) if (year and week) else current_year_week()
        filters.append("catalogs.year = ?")
        filters.append("catalogs.week = ?")
        params.extend([y, w])

    if store:
        filters.append("catalogs.store = ?")
        params.append(store)

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""

    query = f"""
        SELECT
            products.id,
            products.product_name,
            products.brand,
            products.category,
            products.current_price,
            products.old_price,
            products.discount_percent,
            products.price_per_kg,
            products.unit_type,
            products.package_size,
            catalogs.store,
            catalogs.year,
            catalogs.week,
            catalogs.created_at AS catalog_created_at
        FROM products
        JOIN catalogs ON products.catalog_id = catalogs.id
        {where_clause}
        ORDER BY catalogs.store, products.product_name
    """

    cursor.execute(query, params)
    rows = cursor.fetchall()
    result = [row_to_dict(row) for row in rows]
    conn.close()
    return result


@app.get("/api/stores")
def get_stores():
    """Return known stores and whether they're enabled."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT store, enabled FROM store_toggles")
    rows = cursor.fetchall()
    result = [row_to_dict(row) for row in rows]
    conn.close()
    return result


@app.get("/api/catalogs")
def get_catalogs(
    store: Optional[str] = None,
    year: Optional[int] = None,
    week: Optional[int] = None,
):
    """Return catalog metadata (useful for a week/store picker in the frontend)."""
    conn = get_connection()
    cursor = conn.cursor()

    filters = []
    params: list = []
    if store:
        filters.append("store = ?")
        params.append(store)
    if year:
        filters.append("year = ?")
        params.append(year)
    if week:
        filters.append("week = ?")
        params.append(week)

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
    cursor.execute(f"SELECT * FROM catalogs {where_clause} ORDER BY year DESC, week DESC", params)
    rows = cursor.fetchall()
    result = [row_to_dict(row) for row in rows]
    conn.close()
    return result


@app.get("/api/health")
def health():
    return {"status": "ok"}