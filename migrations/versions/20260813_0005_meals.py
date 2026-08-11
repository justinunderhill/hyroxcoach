"""Create meals table and extend measurement RLS to support explicit team sharing."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260813_0005"
down_revision: str | None = "20260812_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

USER_MATCH = "user_id = NULLIF(current_setting('app.current_user_id', true), '')"
CURRENT_USER = "NULLIF(current_setting('app.current_user_id', true), '')"

SHARED_TEAM_EXISTS = f"""EXISTS (
    SELECT 1 FROM team_memberships mine
    JOIN team_memberships theirs ON theirs.team_id = mine.team_id
    WHERE mine.user_id = {CURRENT_USER}
      AND mine.status = 'active'
      AND theirs.user_id = measurements.user_id
      AND theirs.status = 'active'
)"""


def upgrade() -> None:
    op.create_table(
        "meals",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.String(length=255), nullable=False),
        sa.Column("team_id", sa.Uuid(), nullable=False),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column("meal_type", sa.String(length=30), nullable=True),
        sa.Column("description", sa.String(length=500), nullable=False),
        sa.Column("calories", sa.Integer(), nullable=True),
        sa.Column("protein_g", sa.Numeric(6, 1), nullable=True),
        sa.Column("carbs_g", sa.Numeric(6, 1), nullable=True),
        sa.Column("fat_g", sa.Numeric(6, 1), nullable=True),
        sa.Column(
            "nutrition_is_estimated", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("visibility", sa.String(length=16), server_default="private", nullable=False),
        sa.Column("source", sa.String(length=16), server_default="manual", nullable=False),
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
        sa.CheckConstraint("calories IS NULL OR calories >= 0", name="ck_meals_calories_positive"),
        sa.CheckConstraint(
            "protein_g IS NULL OR protein_g >= 0", name="ck_meals_protein_positive"
        ),
        sa.CheckConstraint("carbs_g IS NULL OR carbs_g >= 0", name="ck_meals_carbs_positive"),
        sa.CheckConstraint("fat_g IS NULL OR fat_g >= 0", name="ck_meals_fat_positive"),
        sa.CheckConstraint("visibility IN ('team', 'private')", name="ck_meals_visibility"),
        sa.CheckConstraint("source IN ('manual', 'image')", name="ck_meals_source"),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_meals_user_occurred", "meals", ["user_id", sa.text("occurred_at DESC")])
    op.create_index("ix_meals_team_occurred", "meals", ["team_id", sa.text("occurred_at DESC")])

    op.execute("ALTER TABLE meals ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE meals FORCE ROW LEVEL SECURITY")
    op.execute(
        f"CREATE POLICY meals_select ON meals FOR SELECT USING ("
        f"{USER_MATCH} OR ("
        f"visibility = 'team' AND team_id IN ("
        f"SELECT team_id FROM team_memberships "
        f"WHERE {USER_MATCH} AND status = 'active'"
        f")))"
    )
    op.execute(f"CREATE POLICY meals_insert ON meals FOR INSERT WITH CHECK ({USER_MATCH})")
    op.execute(
        f"CREATE POLICY meals_update ON meals FOR UPDATE "
        f"USING ({USER_MATCH}) WITH CHECK ({USER_MATCH})"
    )
    op.execute(f"CREATE POLICY meals_delete ON meals FOR DELETE USING ({USER_MATCH})")
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON meals TO hyrox_app")

    # Measurements were owner-only under a single FOR ALL policy. Split it so
    # SELECT can also honour explicit team sharing, per SECURITY_PRIVACY.md
    # ("sharing weight/waist must be an explicit user choice").
    op.execute("DROP POLICY measurements_owner_all ON measurements")
    op.execute(
        f"CREATE POLICY measurements_select ON measurements FOR SELECT USING ("
        f"{USER_MATCH} OR (visibility = 'team' AND {SHARED_TEAM_EXISTS}))"
    )
    op.execute(
        f"CREATE POLICY measurements_insert ON measurements FOR INSERT WITH CHECK ({USER_MATCH})"
    )
    op.execute(
        f"CREATE POLICY measurements_update ON measurements FOR UPDATE "
        f"USING ({USER_MATCH}) WITH CHECK ({USER_MATCH})"
    )
    op.execute(
        f"CREATE POLICY measurements_delete ON measurements FOR DELETE USING ({USER_MATCH})"
    )


def downgrade() -> None:
    op.execute("DROP POLICY measurements_delete ON measurements")
    op.execute("DROP POLICY measurements_update ON measurements")
    op.execute("DROP POLICY measurements_insert ON measurements")
    op.execute("DROP POLICY measurements_select ON measurements")
    op.execute(
        f"CREATE POLICY measurements_owner_all ON measurements "
        f"FOR ALL USING ({USER_MATCH}) WITH CHECK ({USER_MATCH})"
    )

    op.execute("REVOKE ALL PRIVILEGES ON meals FROM hyrox_app")
    op.drop_table("meals")
