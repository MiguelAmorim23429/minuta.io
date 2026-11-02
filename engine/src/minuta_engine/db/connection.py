"""Ligação à base de dados e aplicação de migrações."""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from importlib import resources

from minuta_engine.paths import data_dir

DB_FILE = "minuta.db"


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    """Abre a base de dados (criando-a e migrando-a se necessário) e fecha-a no fim.

    As alterações feitas dentro do bloco são confirmadas se não houver exceção.
    """
    directory = data_dir()
    directory.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(directory / DB_FILE)
    try:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        _migrate(connection)
        with connection:
            yield connection
    finally:
        connection.close()


def _migrate(connection: sqlite3.Connection) -> None:
    current = connection.execute("PRAGMA user_version").fetchone()[0]
    scripts = sorted(
        (
            entry
            for entry in resources.files(__package__ + ".migrations").iterdir()
            if entry.name.endswith(".sql")
        ),
        key=lambda entry: entry.name,
    )
    for script in scripts:
        version = int(script.name.split("_", 1)[0])
        if version <= current:
            continue
        connection.executescript(script.read_text(encoding="utf-8"))
        connection.execute(f"PRAGMA user_version = {version:d}")
        connection.commit()
