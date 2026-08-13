import os
from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker


def sqlalchemy_database_url(database_url: str) -> str:
    """Select psycopg 3 while preserving Neon's pooled connection parameters."""
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+psycopg://", 1)
    return database_url


@lru_cache
def get_engine() -> Engine:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is required for database access.")

    return create_engine(
        sqlalchemy_database_url(database_url),
        pool_pre_ping=True,
        pool_recycle=300,
    )


def get_session() -> Generator[Session, None, None]:
    session_factory = sessionmaker(bind=get_engine(), expire_on_commit=False)
    with session_factory() as session:
        yield session


def set_request_user(session: Session, user_id: str) -> None:
    """Set the transaction-local identity consumed by Postgres RLS policies."""
    if session.bind is not None and session.bind.dialect.name == "postgresql":
        session.execute(text("SET LOCAL ROLE hyrox_app"))
        session.execute(
            text("SELECT set_config('app.current_user_id', :user_id, true)"),
            {"user_id": user_id},
        )


def set_invite_token_lookup(session: Session, token_hash: str) -> None:
    """Scopes team_invites SELECT/UPDATE to exactly one row for this
    transaction, for a caller who isn't a team member yet (see migration
    20260823_0016's docstring: knowing the plaintext token is what proves
    the right to read/accept that row)."""
    if session.bind is not None and session.bind.dialect.name == "postgresql":
        session.execute(
            text("SELECT set_config('app.lookup_invite_token_hash', :token_hash, true)"),
            {"token_hash": token_hash},
        )
