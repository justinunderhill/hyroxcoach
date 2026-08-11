from api.database import sqlalchemy_database_url


def test_neon_url_uses_psycopg_driver() -> None:
    source = "postgresql://user:password@example.neon.tech/neondb?sslmode=require"

    assert sqlalchemy_database_url(source) == (
        "postgresql+psycopg://user:password@example.neon.tech/neondb?sslmode=require"
    )
