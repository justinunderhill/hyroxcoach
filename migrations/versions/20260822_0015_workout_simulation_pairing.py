"""Add is_simulation and paired_workout_id to workouts (Phase 8).

is_simulation marks a workout as a HYROX full/half simulation — used to
derive "compromised running" (running performed inside a simulation, as
opposed to a standalone run) and simulation-time trend history without
inventing a new activity taxonomy.

paired_workout_id self-references another row in workouts to record that
two athletes trained together in the same session ("joint session
tracking"). It is nullable and only ever set by the owner of *this* row,
pointing at a workout owned by a teammate on the same team — enforced in
application code (api/routers/workouts.py), not by RLS, because RLS cannot
see across the FK to check team membership of the *other* row without
re-introducing the team_memberships self-query recursion problem already
solved in migration 20260817_0009.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260822_0015"
down_revision: str | None = "20260821_0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "workouts",
        sa.Column(
            "is_simulation", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
    )
    op.add_column(
        "workouts",
        sa.Column("paired_workout_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_workouts_paired_workout_id",
        "workouts",
        "workouts",
        ["paired_workout_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_workouts_paired_workout_id", "workouts", ["paired_workout_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_workouts_paired_workout_id", table_name="workouts")
    op.drop_constraint("fk_workouts_paired_workout_id", "workouts", type_="foreignkey")
    op.drop_column("workouts", "paired_workout_id")
    op.drop_column("workouts", "is_simulation")
