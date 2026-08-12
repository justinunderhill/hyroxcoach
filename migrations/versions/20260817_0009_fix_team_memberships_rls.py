"""Fix infinite recursion in the team_memberships SELECT policy.

Postgres re-applies a table's own RLS policies when that table is
queried from inside one of its own policies. The original policy's
"OR team_id IN (SELECT ... FROM team_memberships ...)" branch queried
team_memberships from within a team_memberships policy, which Postgres
rejects outright as infinite recursion. A user only ever needs to see
their own membership rows today (active_team_ids, teammate_user_ids);
seeing teammates' membership rows for a roster view would need a
SECURITY DEFINER function to break the cycle, and isn't built yet.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260817_0009"
down_revision: str | None = "20260816_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

USER_MATCH = "user_id = NULLIF(current_setting('app.current_user_id', true), '')"

OLD_SELECT_POLICY = (
    f"CREATE POLICY team_memberships_select ON team_memberships FOR SELECT USING ("
    f"{USER_MATCH} OR team_id IN ("
    f"SELECT team_id FROM team_memberships tm "
    f"WHERE tm.user_id = NULLIF(current_setting('app.current_user_id', true), '') "
    f"AND tm.status = 'active'"
    f"))"
)


def upgrade() -> None:
    op.execute("DROP POLICY team_memberships_select ON team_memberships")
    op.execute(
        f"CREATE POLICY team_memberships_select ON team_memberships FOR SELECT "
        f"USING ({USER_MATCH})"
    )


def downgrade() -> None:
    op.execute("DROP POLICY team_memberships_select ON team_memberships")
    op.execute(OLD_SELECT_POLICY)
