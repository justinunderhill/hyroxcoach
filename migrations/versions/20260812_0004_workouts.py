"""Create workout logging tables: categories, workouts, category links, exercise performances."""

from collections.abc import Sequence
from uuid import uuid4

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260812_0004"
down_revision: str | None = "20260812_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

USER_MATCH = "user_id = NULLIF(current_setting('app.current_user_id', true), '')"
CURRENT_USER = "NULLIF(current_setting('app.current_user_id', true), '')"

SEED_CATEGORIES = [
    ("running", "Running", "running"),
    ("skierg", "SkiErg", "hyrox_station"),
    ("sled_push", "Sled Push", "hyrox_station"),
    ("sled_pull", "Sled Pull", "hyrox_station"),
    ("burpee_broad_jumps", "Burpee Broad Jumps", "hyrox_station"),
    ("row", "Row", "hyrox_station"),
    ("farmers_carry", "Farmers Carry", "hyrox_station"),
    ("sandbag_lunges", "Sandbag Lunges", "hyrox_station"),
    ("wall_balls", "Wall Balls", "hyrox_station"),
    ("strength", "Strength", "strength"),
    ("mma_combat", "MMA / Combat", "combat"),
    ("mobility", "Mobility", "recovery"),
    ("recovery", "Recovery", "recovery"),
    ("walking", "Walking / Low-intensity aerobic", "low_intensity"),
    ("other", "Other", "other"),
]


def upgrade() -> None:
    op.create_table(
        "workout_categories",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("slug", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("category_group", sa.String(length=32), nullable=False),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )

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
            {"id": uuid4(), "slug": slug, "name": name, "category_group": group}
            for slug, name, group in SEED_CATEGORIES
        ],
    )

    op.create_table(
        "workouts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.String(length=255), nullable=False),
        sa.Column("team_id", sa.Uuid(), nullable=False),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("activity_type", sa.String(length=60), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("distance_km", sa.Numeric(6, 2), nullable=True),
        sa.Column("rpe", sa.Integer(), nullable=True),
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
        sa.CheckConstraint(
            "duration_minutes IS NULL OR duration_minutes > 0",
            name="ck_workouts_duration_positive",
        ),
        sa.CheckConstraint(
            "distance_km IS NULL OR distance_km > 0",
            name="ck_workouts_distance_positive",
        ),
        sa.CheckConstraint("rpe IS NULL OR (rpe BETWEEN 1 AND 10)", name="ck_workouts_rpe_range"),
        sa.CheckConstraint("visibility IN ('team', 'private')", name="ck_workouts_visibility"),
        sa.CheckConstraint(
            "source IN ('manual', 'image', 'integration')", name="ck_workouts_source"
        ),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_workouts_user_occurred", "workouts", ["user_id", sa.text("occurred_at DESC")]
    )
    op.create_index(
        "ix_workouts_team_occurred", "workouts", ["team_id", sa.text("occurred_at DESC")]
    )

    op.create_table(
        "workout_category_links",
        sa.Column("workout_id", sa.Uuid(), nullable=False),
        sa.Column("category_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["workout_id"], ["workouts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["category_id"], ["workout_categories.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("workout_id", "category_id"),
    )

    op.create_table(
        "exercise_performances",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workout_id", sa.Uuid(), nullable=False),
        sa.Column("exercise_name", sa.String(length=120), nullable=False),
        sa.Column("normalized_exercise_key", sa.String(length=120), nullable=True),
        sa.Column("sequence_no", sa.Integer(), server_default="1", nullable=False),
        sa.Column("sets", sa.Integer(), nullable=True),
        sa.Column("reps", sa.Integer(), nullable=True),
        sa.Column("load_kg", sa.Numeric(6, 2), nullable=True),
        sa.Column("distance_m", sa.Numeric(8, 2), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("pace_seconds_per_km", sa.Numeric(7, 2), nullable=True),
        sa.Column("calories", sa.Integer(), nullable=True),
        sa.Column("rpe", sa.Integer(), nullable=True),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "rpe IS NULL OR (rpe BETWEEN 1 AND 10)", name="ck_exercise_performances_rpe_range"
        ),
        sa.ForeignKeyConstraint(["workout_id"], ["workouts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_exercise_performances_workout_sequence",
        "exercise_performances",
        ["workout_id", "sequence_no"],
    )

    # workout_categories: shared reference data, readable by any authenticated app request.
    op.execute("ALTER TABLE workout_categories ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE workout_categories FORCE ROW LEVEL SECURITY")
    op.execute(
        f"CREATE POLICY workout_categories_select ON workout_categories FOR SELECT "
        f"USING ({CURRENT_USER} IS NOT NULL)"
    )

    op.execute("ALTER TABLE workouts ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE workouts FORCE ROW LEVEL SECURITY")
    op.execute(
        f"CREATE POLICY workouts_select ON workouts FOR SELECT USING ("
        f"{USER_MATCH} OR ("
        f"visibility = 'team' AND team_id IN ("
        f"SELECT team_id FROM team_memberships "
        f"WHERE {USER_MATCH} AND status = 'active'"
        f")))"
    )
    op.execute(f"CREATE POLICY workouts_insert ON workouts FOR INSERT WITH CHECK ({USER_MATCH})")
    op.execute(
        f"CREATE POLICY workouts_update ON workouts FOR UPDATE "
        f"USING ({USER_MATCH}) WITH CHECK ({USER_MATCH})"
    )
    op.execute(f"CREATE POLICY workouts_delete ON workouts FOR DELETE USING ({USER_MATCH})")

    op.execute("ALTER TABLE workout_category_links ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE workout_category_links FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY workout_category_links_select ON workout_category_links FOR SELECT "
        "USING (workout_id IN (SELECT id FROM workouts))"
    )
    op.execute(
        f"CREATE POLICY workout_category_links_insert ON workout_category_links FOR INSERT "
        f"WITH CHECK (workout_id IN (SELECT id FROM workouts WHERE {USER_MATCH}))"
    )
    op.execute(
        f"CREATE POLICY workout_category_links_delete ON workout_category_links FOR DELETE "
        f"USING (workout_id IN (SELECT id FROM workouts WHERE {USER_MATCH}))"
    )

    op.execute("ALTER TABLE exercise_performances ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE exercise_performances FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY exercise_performances_select ON exercise_performances FOR SELECT "
        "USING (workout_id IN (SELECT id FROM workouts))"
    )
    op.execute(
        f"CREATE POLICY exercise_performances_insert ON exercise_performances FOR INSERT "
        f"WITH CHECK (workout_id IN (SELECT id FROM workouts WHERE {USER_MATCH}))"
    )
    op.execute(
        f"CREATE POLICY exercise_performances_update ON exercise_performances FOR UPDATE "
        f"USING (workout_id IN (SELECT id FROM workouts WHERE {USER_MATCH})) "
        f"WITH CHECK (workout_id IN (SELECT id FROM workouts WHERE {USER_MATCH}))"
    )
    op.execute(
        f"CREATE POLICY exercise_performances_delete ON exercise_performances FOR DELETE "
        f"USING (workout_id IN (SELECT id FROM workouts WHERE {USER_MATCH}))"
    )

    op.execute("GRANT SELECT ON workout_categories TO hyrox_app")
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON workouts TO hyrox_app")
    op.execute("GRANT SELECT, INSERT, DELETE ON workout_category_links TO hyrox_app")
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON exercise_performances TO hyrox_app")


def downgrade() -> None:
    op.execute("REVOKE ALL PRIVILEGES ON exercise_performances FROM hyrox_app")
    op.execute("REVOKE ALL PRIVILEGES ON workout_category_links FROM hyrox_app")
    op.execute("REVOKE ALL PRIVILEGES ON workouts FROM hyrox_app")
    op.execute("REVOKE ALL PRIVILEGES ON workout_categories FROM hyrox_app")
    op.drop_table("exercise_performances")
    op.drop_table("workout_category_links")
    op.drop_table("workouts")
    op.drop_table("workout_categories")
