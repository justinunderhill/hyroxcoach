"""Create coach_insights table for Phase 7 (AI Coach V1).

RLS: a user can read their own scope='workout'/'weekly' rows, and any active
team member can read scope='team_weekly' rows for their team (user_id is
null there). Only the row's own user_id (or, for team_weekly, any team
member) may insert — the coach service always writes as the requesting
user via set_request_user, matching the workouts/meals ownership pattern.
No UPDATE/DELETE policies: insights are an append-only log per
CLAUDE.md rule 3 ("do not silently overwrite a user's confirmed record")
applied to generated content — a regenerated insight is a new row.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260821_0014"
down_revision: str | None = "20260821_0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CURRENT_USER = "NULLIF(current_setting('app.current_user_id', true), '')"
OWN_ROW = f"user_id = {CURRENT_USER}"
MEMBER_OF_TEAM = (
    f"team_id IN (SELECT team_id FROM team_memberships "
    f"WHERE user_id = {CURRENT_USER} AND status = 'active')"
)


def upgrade() -> None:
    op.create_table(
        "coach_insights",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("scope", sa.String(length=16), nullable=False),
        sa.Column("user_id", sa.String(length=255), nullable=True),
        sa.Column("team_id", sa.Uuid(), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=True),
        sa.Column("period_end", sa.Date(), nullable=True),
        sa.Column("source_record_id", sa.Uuid(), nullable=True),
        sa.Column("coach_version", sa.String(length=24), nullable=False),
        sa.Column("model_name", sa.String(length=80), nullable=False),
        sa.Column("insight_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("context_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "scope IN ('workout', 'daily', 'weekly', 'team_weekly')",
            name="ck_coach_insights_scope",
        ),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_coach_insights_lookup",
        "coach_insights",
        ["scope", "team_id", "user_id", "period_start"],
    )

    op.execute("ALTER TABLE coach_insights ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE coach_insights FORCE ROW LEVEL SECURITY")
    op.execute(
        f"CREATE POLICY coach_insights_select ON coach_insights FOR SELECT USING ("
        f"({OWN_ROW}) OR (scope = 'team_weekly' AND {MEMBER_OF_TEAM}))"
    )
    op.execute(
        f"CREATE POLICY coach_insights_insert ON coach_insights FOR INSERT WITH CHECK ("
        f"({OWN_ROW}) OR (scope = 'team_weekly' AND user_id IS NULL AND {MEMBER_OF_TEAM}))"
    )
    op.execute("GRANT SELECT, INSERT ON coach_insights TO hyrox_app")


def downgrade() -> None:
    op.execute("REVOKE ALL PRIVILEGES ON coach_insights FROM hyrox_app")
    op.drop_table("coach_insights")
