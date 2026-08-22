"""Allow goal_events.event_type to be 'hyrox_singles' in addition to 'hyrox_doubles'.

The app is opening up beyond its original two-athlete-only assumption to
also support a single athlete training solo (PRODUCT_REQUIREMENTS.md and
DATA_MODEL.md updated alongside this migration). goal_events.event_type was
previously constrained to exactly one legal value ('hyrox_doubles'), which
blocked a solo athlete from recording their actual race format.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260825_0019"
down_revision: str | None = "20260824_0018"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("ck_goal_events_event_type", "goal_events", type_="check")
    op.create_check_constraint(
        "ck_goal_events_event_type",
        "goal_events",
        "event_type IN ('hyrox_singles', 'hyrox_doubles')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_goal_events_event_type", "goal_events", type_="check")
    op.create_check_constraint(
        "ck_goal_events_event_type",
        "goal_events",
        "event_type IN ('hyrox_doubles')",
    )
