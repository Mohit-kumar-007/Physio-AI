"""Engine and session dependency."""

from __future__ import annotations

import logging
from collections.abc import Iterator

from sqlalchemy import inspect, text
from sqlmodel import Session, SQLModel, create_engine

from .config import DATABASE_URL

# check_same_thread=False is required because FastAPI serves requests from a
# thread pool; SQLModel still hands each request its own Session.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)


def init_db() -> None:
    from . import models  # noqa: F401  (registers tables on SQLModel.metadata)

    SQLModel.metadata.create_all(engine)
    _add_missing_columns()


# SQL type for the Python types actually used on the models.
_SQL_TYPES = {bool: "BOOLEAN", int: "INTEGER", float: "FLOAT", str: "VARCHAR"}


def _add_missing_columns() -> None:
    """Add columns that exist on a model but not yet in the table.

    create_all() only ever creates whole tables, so adding a field to an
    existing model would otherwise mean dropping the database and losing the
    patient's recorded sessions. This covers the one case a real migration
    tool would be overkill for: new nullable columns with defaults. Anything
    else -- renames, type changes, drops -- still needs a proper migration.
    """
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    for table in SQLModel.metadata.sorted_tables:
        if table.name not in existing_tables:
            continue
        present = {c["name"] for c in inspector.get_columns(table.name)}
        for column in table.columns:
            if column.name in present:
                continue
            sql_type = _SQL_TYPES.get(column.type.python_type, "VARCHAR")
            default = column.default.arg if column.default is not None else None
            if isinstance(default, bool):
                clause = f" DEFAULT {1 if default else 0}"
            elif isinstance(default, (int, float)):
                clause = f" DEFAULT {default}"
            else:
                clause = ""
            with engine.begin() as conn:
                conn.execute(text(
                    f"ALTER TABLE {table.name} "
                    f"ADD COLUMN {column.name} {sql_type}{clause}"
                ))
            logging.getLogger("physio").info(
                "Added column %s.%s", table.name, column.name
            )


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session
