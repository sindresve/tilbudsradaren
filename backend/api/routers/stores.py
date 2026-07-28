from fastapi import APIRouter, Depends

from ..deps import get_db
from ..utils import row_to_dict

router = APIRouter(prefix="/api/stores", tags=["stores"])


@router.get("")
def get_stores(conn=Depends(get_db)):
    """Return known stores and whether they're enabled."""
    cursor = conn.cursor()
    cursor.execute("SELECT store, enabled FROM store_toggles")
    rows = cursor.fetchall()
    return [row_to_dict(row) for row in rows]