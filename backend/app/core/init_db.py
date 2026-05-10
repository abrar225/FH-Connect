"""
Deprecated schema bootstrap module.

Runtime schema creation is intentionally disabled. FH-Connect now owns schema
changes through Alembic migrations; run `alembic upgrade head` before starting
the API or workers.
"""


async def create_tables():
    raise RuntimeError("create_tables() is disabled. Use `alembic upgrade head`.")


if __name__ == "__main__":
    raise SystemExit("create_tables() is disabled. Use `alembic upgrade head`.")
