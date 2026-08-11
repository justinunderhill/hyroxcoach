from dotenv import load_dotenv
from sqlalchemy import text

from api.database import get_engine

load_dotenv(".env.local")

engine = get_engine()
with engine.connect() as connection:
    transaction = connection.begin()
    try:
        connection.execute(text("SET LOCAL ROLE hyrox_app"))
        anonymous_count = connection.execute(
            text("SELECT count(*) FROM athlete_profiles")
        ).scalar_one()
        connection.execute(
            text("SELECT set_config('app.current_user_id', 'rls-smoke-a', true)")
        )
        connection.execute(
            text(
                "INSERT INTO athlete_profiles "
                "(id, user_id, display_name, timezone) VALUES "
                "(gen_random_uuid(), 'rls-smoke-a', 'RLS smoke test', 'UTC')"
            )
        )
        owner_count = connection.execute(
            text("SELECT count(*) FROM athlete_profiles WHERE user_id = 'rls-smoke-a'")
        ).scalar_one()
        connection.execute(
            text("SELECT set_config('app.current_user_id', 'rls-smoke-b', true)")
        )
        other_user_count = connection.execute(
            text("SELECT count(*) FROM athlete_profiles WHERE user_id = 'rls-smoke-a'")
        ).scalar_one()
    finally:
        transaction.rollback()

engine.dispose()

if (anonymous_count, owner_count, other_user_count) != (0, 1, 0):
    raise SystemExit(
        "RLS verification failed: "
        f"anonymous={anonymous_count}, owner={owner_count}, other_user={other_user_count}."
    )

print("RLS verified: anonymous=0, owner=1, other_user=0; smoke row rolled back")
