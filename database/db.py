import sqlite3
from contextlib import contextmanager
from pathlib import Path

from config import DATABASE_PATH


def get_connection(path: Path | str = DATABASE_PATH) -> sqlite3.Connection:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db(path: Path | str = DATABASE_PATH) -> None:
    schema = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")
    with get_connection(path) as connection:
        connection.executescript(schema)


@contextmanager
def transaction(path: Path | str = DATABASE_PATH):
    connection = get_connection(path)
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
