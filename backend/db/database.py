import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "tilbudsradar.db"


def get_connection():
    conn = sqlite3.connect(
        DB_PATH,
        check_same_thread=False,
        timeout=10
    )
    conn.row_factory = sqlite3.Row
    return conn