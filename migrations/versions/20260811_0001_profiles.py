"""Create athlete profiles and private onboarding measurements."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260811_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

USER_MATCH = "user_id = NULLIF(current_setting('app.current_user_id', true), '')"


def upgrade() -> None:
    op.create_table(
        "athlete_profiles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=80), nullable=False),
        sa.Column("avatar_path", sa.Text(), nullable=True),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column("baseline_5k_seconds", sa.Integer(), nullable=True),
        sa.Column(
            "training_availability",
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
        sa.CheckConstraint(
            "baseline_5k_seconds IS NULL OR baseline_5k_seconds > 0",
            name="ck_athlete_profiles_baseline_5k_positive",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_athlete_profiles_user_id", "athlete_profiles", ["user_id"])

    op.create_table(
        "measurements",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.String(length=255), nullable=False),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("weight_kg", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("waist_cm", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("resting_hr", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("visibility", sa.String(length=16), server_default="private", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "weight_kg IS NOT NULL OR waist_cm IS NOT NULL OR notes IS NOT NULL",
            name="ck_measurements_value_present",
        ),
        sa.CheckConstraint(
            "weight_kg IS NULL OR weight_kg > 0",
            name="ck_measurements_weight_positive",
        ),
        sa.CheckConstraint(
            "waist_cm IS NULL OR waist_cm > 0",
            name="ck_measurements_waist_positive",
        ),
        sa.CheckConstraint("visibility IN ('private', 'team')", name="ck_measurements_visibility"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_measurements_user_id", "measurements", ["user_id"])
    op.create_index("ix_measurements_user_occurred", "measurements", ["user_id", "occurred_at"])

    for table in ("athlete_profiles", "measurements"):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY {table}_owner_all ON {table} "
            f"FOR ALL USING ({USER_MATCH}) WITH CHECK ({USER_MATCH})"
        )


def downgrade() -> None:
    op.drop_table("measurements")
    op.drop_table("athlete_profiles")
