import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

_DEFAULT_DB = Path(__file__).parent / "musica_local.sqlite"


@contextmanager
def get_db():
    path = os.environ.get("DB_PATH", str(_DEFAULT_DB))
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
