from typing import Optional

from fastapi import APIRouter, Depends

from ..deps import get_db
from ..utils import row_to_dict

router = APIRouter(prefix="/api/catalogs", tags=["catalogs"])


@router.get("")
def get_catalogs(
    store: Optional[str] = None,
    year: Optional[int] = None,
    week: Optional[int] = None,
    conn=Depends(get_db),
):
    """Return catalog metadata (useful for a week/store picker in the frontend)."""
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
    return [row_to_dict(row) for row in rows]