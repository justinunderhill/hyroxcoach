"""Create teams and team memberships."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260812_0003"
down_revision: str | None = "20260811_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

USER_MATCH = "user_id = NULLIF(current_setting('app.current_user_id', true), '')"
CREATOR_MATCH = "created_by = NULLIF(current_setting('app.current_user_id', true), '')"


def upgrade() -> None:
    op.create_table(
        "teams",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("created_by", sa.String(length=255), nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_teams_created_by", "teams", ["created_by"])

    op.create_table(
        "team_memberships",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("team_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=16), server_default="active", nullable=False),
        sa.Column(
            "joined_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("role IN ('owner', 'athlete')", name="ck_team_memberships_role"),
        sa.CheckConstraint(
            "status IN ('invited', 'active', 'left')",
            name="ck_team_memberships_status",
        ),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("team_id", "user_id", name="uq_team_memberships_team_user"),
    )
    op.create_index("ix_team_memberships_user_id", "team_memberships", ["user_id"])
    op.create_index("ix_team_memberships_team_id", "team_memberships", ["team_id"])

    op.execute("ALTER TABLE teams ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE teams FORCE ROW LEVEL SECURITY")
    op.execute(
        f"CREATE POLICY teams_select ON teams FOR SELECT USING ("
        f"{CREATOR_MATCH} OR id IN ("
        f"SELECT team_id FROM team_memberships "
        f"WHERE {USER_MATCH} AND status = 'active'"
        f"))"
    )
    op.execute(f"CREATE POLICY teams_insert ON teams FOR INSERT WITH CHECK ({CREATOR_MATCH})")
    op.execute(
        f"CREATE POLICY teams_update ON teams FOR UPDATE "
        f"USING ({CREATOR_MATCH}) WITH CHECK ({CREATOR_MATCH})"
    )

    op.execute("ALTER TABLE team_memberships ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE team_memberships FORCE ROW LEVEL SECURITY")
    op.execute(
        f"CREATE POLICY team_memberships_select ON team_memberships FOR SELECT USING ("
        f"{USER_MATCH} OR team_id IN ("
        f"SELECT team_id FROM team_memberships tm "
        f"WHERE tm.user_id = NULLIF(current_setting('app.current_user_id', true), '') "
        f"AND tm.status = 'active'"
        f"))"
    )
    op.execute(
        f"CREATE POLICY team_memberships_insert ON team_memberships FOR INSERT "
        f"WITH CHECK ({USER_MATCH})"
    )
    op.execute(
        f"CREATE POLICY team_memberships_update ON team_memberships FOR UPDATE "
        f"USING ({USER_MATCH}) WITH CHECK ({USER_MATCH})"
    )

    op.execute("GRANT SELECT, INSERT, UPDATE ON teams TO hyrox_app")
    op.execute("GRANT SELECT, INSERT, UPDATE ON team_memberships TO hyrox_app")


def downgrade() -> None:
    op.execute("REVOKE ALL PRIVILEGES ON team_memberships FROM hyrox_app")
    op.execute("REVOKE ALL PRIVILEGES ON teams FROM hyrox_app")
    op.drop_table("team_memberships")
    op.drop_table("teams")
