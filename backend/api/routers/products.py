from typing import Optional

from fastapi import APIRouter, Depends, Query

from ..deps import get_db
from ..utils import current_year_week, row_to_dict

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("")
def get_products(
    store: Optional[str] = Query(None, description="Filter by store, e.g. 'rema'"),
    year: Optional[int] = Query(None, description="Override year (defaults to current)"),
    week: Optional[int] = Query(None, description="Override week (defaults to current)"),
    all_weeks: bool = Query(False, description="If true, ignore year/week filter entirely"),
    conn=Depends(get_db),
):
    """
    Return products joined with their catalog info.
    Defaults to the current ISO year/week unless all_weeks=true.
    """
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
    return [row_to_dict(row) for row in rows]