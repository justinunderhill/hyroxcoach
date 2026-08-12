"""Create daily_steps table."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260815_0007"
down_revision: str | None = "20260814_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

USER_MATCH = "user_id = NULLIF(current_setting('app.current_user_id', true), '')"
CURRENT_USER = "NULLIF(current_setting('app.current_user_id', true), '')"

SHARED_TEAM_EXISTS = f"""EXISTS (
    SELECT 1 FROM team_memberships mine
    JOIN team_memberships theirs ON theirs.team_id = mine.team_id
    WHERE mine.user_id = {CURRENT_USER}
      AND mine.status = 'active'
      AND theirs.user_id = daily_steps.user_id
      AND theirs.status = 'active'
)"""


def upgrade() -> None:
    op.create_table(
        "daily_steps",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.String(length=255), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("steps", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=20), server_default="manual", nullable=False),
        sa.Column("visibility", sa.String(length=16), server_default="private", nullable=False),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("steps >= 0", name="ck_daily_steps_steps_positive"),
        sa.CheckConstraint(
            "source IN ('manual', 'health_connect', 'apple_health', 'other_import')",
            name="ck_daily_steps_source",
        ),
        sa.CheckConstraint("visibility IN ('team', 'private')", name="ck_daily_steps_visibility"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "date", name="uq_daily_steps_user_date"),
    )
    op.create_index(
        "ix_daily_steps_user_date", "daily_steps", ["user_id", sa.text("date DESC")]
    )

    op.execute("ALTER TABLE daily_steps ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE daily_steps FORCE ROW LEVEL SECURITY")
    op.execute(
        f"CREATE POLICY daily_steps_select ON daily_steps FOR SELECT USING ("
        f"{USER_MATCH} OR (visibility = 'team' AND {SHARED_TEAM_EXISTS}))"
    )
    op.execute(
        f"CREATE POLICY daily_steps_insert ON daily_steps FOR INSERT WITH CHECK ({USER_MATCH})"
    )
    op.execute(
        f"CREATE POLICY daily_steps_update ON daily_steps FOR UPDATE "
        f"USING ({USER_MATCH}) WITH CHECK ({USER_MATCH})"
    )
    op.execute(f"CREATE POLICY daily_steps_delete ON daily_steps FOR DELETE USING ({USER_MATCH})")
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON daily_steps TO hyrox_app")


def downgrade() -> None:
    op.execute("REVOKE ALL PRIVILEGES ON daily_steps FROM hyrox_app")
    op.drop_table("daily_steps")
