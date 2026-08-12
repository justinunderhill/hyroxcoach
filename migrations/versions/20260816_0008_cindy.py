"""Add the functional_conditioning category and create cindy_results."""

from collections.abc import Sequence
from uuid import uuid4

import sqlalchemy as sa
from alembic import op

revision: str = "20260816_0008"
down_revision: str | None = "20260815_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

USER_MATCH = "user_id = NULLIF(current_setting('app.current_user_id', true), '')"


def upgrade() -> None:
    category_table = sa.table(
        "workout_categories",
        sa.column("id", sa.Uuid()),
        sa.column("slug", sa.String()),
        sa.column("name", sa.String()),
        sa.column("category_group", sa.String()),
    )
    op.bulk_insert(
        category_table,
        [
            {
                "id": uuid4(),
                "slug": "functional_conditioning",
                "name": "Functional Conditioning",
                "category_group": "conditioning",
            }
        ],
    )

    op.create_table(
        "cindy_results",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workout_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.String(length=255), nullable=False),
        sa.Column("full_rounds", sa.Integer(), nullable=False),
        sa.Column("extra_pullups", sa.Integer(), server_default="0", nullable=False),
        sa.Column("extra_pushups", sa.Integer(), server_default="0", nullable=False),
        sa.Column("extra_squats", sa.Integer(), server_default="0", nullable=False),
        sa.Column("total_reps", sa.Integer(), nullable=False),
        sa.Column("total_seconds", sa.Integer(), nullable=False),
        sa.Column("completed_as_prescribed", sa.Boolean(), nullable=False),
        sa.Column("calories_burned", sa.Integer(), nullable=True),
        sa.Column("calorie_source", sa.String(length=16), nullable=True),
        sa.Column("calorie_estimation_version", sa.String(length=16), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("full_rounds >= 0", name="ck_cindy_results_full_rounds_positive"),
        sa.CheckConstraint("extra_pullups >= 0", name="ck_cindy_results_extra_pullups_positive"),
        sa.CheckConstraint("extra_pushups >= 0", name="ck_cindy_results_extra_pushups_positive"),
        sa.CheckConstraint("extra_squats >= 0", name="ck_cindy_results_extra_squats_positive"),
        sa.CheckConstraint("total_reps >= 0", name="ck_cindy_results_total_reps_positive"),
        sa.CheckConstraint(
            "total_seconds > 0 AND total_seconds <= 1200", name="ck_cindy_results_total_seconds"
        ),
        sa.CheckConstraint(
            "calories_burned IS NULL OR calories_burned >= 0",
            name="ck_cindy_results_calories_positive",
        ),
        sa.CheckConstraint(
            "calorie_source IS NULL OR calorie_source IN ('external', 'estimated')",
            name="ck_cindy_results_calorie_source",
        ),
        sa.ForeignKeyConstraint(["workout_id"], ["workouts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workout_id"),
    )
    op.create_index("ix_cindy_results_user_id", "cindy_results", ["user_id"])

    op.execute("ALTER TABLE cindy_results ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE cindy_results FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY cindy_results_select ON cindy_results FOR SELECT "
        "USING (workout_id IN (SELECT id FROM workouts))"
    )
    op.execute(
        f"CREATE POLICY cindy_results_insert ON cindy_results FOR INSERT "
        f"WITH CHECK (workout_id IN (SELECT id FROM workouts WHERE {USER_MATCH}))"
    )
    op.execute(
        f"CREATE POLICY cindy_results_delete ON cindy_results FOR DELETE "
        f"USING (workout_id IN (SELECT id FROM workouts WHERE {USER_MATCH}))"
    )
    op.execute("GRANT SELECT, INSERT, DELETE ON cindy_results TO hyrox_app")


def downgrade() -> None:
    op.execute("REVOKE ALL PRIVILEGES ON cindy_results FROM hyrox_app")
    op.drop_table("cindy_results")
    op.execute("DELETE FROM workout_categories WHERE slug = 'functional_conditioning'")
