"""Create goal_events table.

This was specified in DATA_MODEL.md and PRODUCT_REQUIREMENTS.md as a Phase 1
deliverable ("target event setup") but was never actually built — building
it now because Phase 7's CoachContext (AI_COACH.md #3) needs target_event to
discuss race countdown, which is the product's core premise.

RLS mirrors the workouts/meals pattern: a team member can read/write their
team's single goal event, checked via a subquery against team_memberships
for the caller's own rows only (safe — see migration 20260817_0009 for why
a table must never subquery itself from its own policy).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260821_0013"
down_revision: str | None = "20260820_0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

MEMBER_OF_TEAM = (
    "team_id IN (SELECT team_id FROM team_memberships "
    "WHERE user_id = NULLIF(current_setting('app.current_user_id', true), '') "
    "AND status = 'active')"
)


def upgrade() -> None:
    op.create_table(
        "goal_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("team_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column(
            "event_type", sa.String(length=24), server_default="hyrox_doubles", nullable=False
        ),
        sa.Column("event_date", sa.Date(), nullable=False),
        sa.Column("division", sa.String(length=80), nullable=True),
        sa.Column("location", sa.String(length=120), nullable=True),
        sa.Column("preparation_start_date", sa.Date(), nullable=True),
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
        sa.CheckConstraint("event_type IN ('hyrox_doubles')", name="ck_goal_events_event_type"),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("team_id", name="uq_goal_events_team_id"),
    )

    op.execute("ALTER TABLE goal_events ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE goal_events FORCE ROW LEVEL SECURITY")
    op.execute(
        f"CREATE POLICY goal_events_select ON goal_events FOR SELECT USING ({MEMBER_OF_TEAM})"
    )
    op.execute(
        f"CREATE POLICY goal_events_insert ON goal_events FOR INSERT WITH CHECK ({MEMBER_OF_TEAM})"
    )
    op.execute(
        f"CREATE POLICY goal_events_update ON goal_events FOR UPDATE "
        f"USING ({MEMBER_OF_TEAM}) WITH CHECK ({MEMBER_OF_TEAM})"
    )
    op.execute(
        f"CREATE POLICY goal_events_delete ON goal_events FOR DELETE USING ({MEMBER_OF_TEAM})"
    )
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON goal_events TO hyrox_app")


def downgrade() -> None:
    op.execute("REVOKE ALL PRIVILEGES ON goal_events FROM hyrox_app")
    op.drop_table("goal_events")
