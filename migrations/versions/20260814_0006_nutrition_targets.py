"""Create nutrition_targets table."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260814_0006"
down_revision: str | None = "20260813_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

USER_MATCH = "user_id = NULLIF(current_setting('app.current_user_id', true), '')"


def upgrade() -> None:
    op.create_table(
        "nutrition_targets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.String(length=255), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("calories_target", sa.Integer(), nullable=True),
        sa.Column("protein_g_target", sa.Numeric(6, 1), nullable=True),
        sa.Column("carbs_g_target", sa.Numeric(6, 1), nullable=True),
        sa.Column("fat_g_target", sa.Numeric(6, 1), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "calories_target IS NOT NULL OR protein_g_target IS NOT NULL "
            "OR carbs_g_target IS NOT NULL OR fat_g_target IS NOT NULL",
            name="ck_nutrition_targets_value_present",
        ),
        sa.CheckConstraint(
            "calories_target IS NULL OR calories_target >= 0",
            name="ck_nutrition_targets_calories_positive",
        ),
        sa.CheckConstraint(
            "protein_g_target IS NULL OR protein_g_target >= 0",
            name="ck_nutrition_targets_protein_positive",
        ),
        sa.CheckConstraint(
            "carbs_g_target IS NULL OR carbs_g_target >= 0",
            name="ck_nutrition_targets_carbs_positive",
        ),
        sa.CheckConstraint(
            "fat_g_target IS NULL OR fat_g_target >= 0", name="ck_nutrition_targets_fat_positive"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_nutrition_targets_user_effective",
        "nutrition_targets",
        ["user_id", sa.text("effective_from DESC")],
    )

    op.execute("ALTER TABLE nutrition_targets ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE nutrition_targets FORCE ROW LEVEL SECURITY")
    op.execute(
        f"CREATE POLICY nutrition_targets_owner_all ON nutrition_targets "
        f"FOR ALL USING ({USER_MATCH}) WITH CHECK ({USER_MATCH})"
    )
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON nutrition_targets TO hyrox_app")


def downgrade() -> None:
    op.execute("REVOKE ALL PRIVILEGES ON nutrition_targets FROM hyrox_app")
    op.drop_table("nutrition_targets")
