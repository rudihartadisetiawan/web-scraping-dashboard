"""Database connection module using SQLAlchemy connection pooling.

Credentials are read exclusively from environment variables.
"""

import os

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


DEFAULT_PORT = "3306"


def get_connection() -> Engine:
    """Build and return a SQLAlchemy engine with connection pooling."""
    host = os.environ.get("MYSQL_HOST", "")
    port = os.environ.get("MYSQL_PORT", DEFAULT_PORT)
    user = os.environ.get("MYSQL_USER", "")
    password = os.environ.get("MYSQL_PASSWORD", "")
    database = os.environ.get("MYSQL_DATABASE", "")

    if not all([host, port, user, database]):
        raise ValueError(
            "Missing required MySQL environment variables: "
            "MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_DATABASE"
        )

    connection_url = (
        f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
        "?charset=utf8mb4"
    )
    # pool_pre_ping reconnects if a stale connection is detected
    return create_engine(connection_url, pool_pre_ping=True)


def test_connection() -> bool:
    """Try connecting to the database and print status."""
    engine = get_connection()
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 AS alive"))
            row = result.fetchone()
        print(f"[OK] Database connection successful: {row}")
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"[FAIL] Database connection failed: {type(exc).__name__}")
        return False


if __name__ == "__main__":
    test_connection()
