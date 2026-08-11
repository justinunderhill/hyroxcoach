"""Create the restricted application role used for RLS-enforced API traffic."""

from collections.abc import Sequence

from alembic import op

revision: str = "20260811_0002"
down_revision: str | None = "20260811_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
          IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'hyrox_app') THEN
            CREATE ROLE hyrox_app NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;
          END IF;
          EXECUTE format('GRANT hyrox_app TO %I', current_user);
        END
        $$
        """
    )
    op.execute("GRANT USAGE ON SCHEMA public TO hyrox_app")
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON athlete_profiles TO hyrox_app")
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON measurements TO hyrox_app")


def downgrade() -> None:
    op.execute("REVOKE ALL PRIVILEGES ON measurements FROM hyrox_app")
    op.execute("REVOKE ALL PRIVILEGES ON athlete_profiles FROM hyrox_app")
    op.execute("REVOKE USAGE ON SCHEMA public FROM hyrox_app")
    op.execute(
        """
        DO $$
        BEGIN
          EXECUTE format('REVOKE hyrox_app FROM %I', current_user);
          IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'hyrox_app') THEN
            DROP ROLE hyrox_app;
          END IF;
        END
        $$
        """
    )
