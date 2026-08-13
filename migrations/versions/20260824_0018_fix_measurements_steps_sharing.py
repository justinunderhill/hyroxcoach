"""Fix measurements/daily_steps team-visibility sharing, broken since the
team_memberships recursion fix.

measurements (20260813_0005) and daily_steps (20260815_0007) both gate
`visibility = 'team'` rows behind a raw SQL EXISTS self-join against
team_memberships, evaluated as part of *their own* SELECT policy. Since
20260817_0009 narrowed team_memberships' own SELECT policy to `user_id =
self` (to fix infinite recursion), any read of team_memberships from
anywhere -- including from another table's policy -- collapses to "just
the caller" under real RLS. That silently makes the "theirs" side of the
self-join always empty, so a teammate's `visibility = 'team'` measurement
or daily_steps row was never actually visible to their partner, ever
since 20260817_0009 shipped -- confirmed against the real dev DB (a
`visibility='team'` row belonging to user A returned zero rows when
queried as user B under `SET LOCAL ROLE hyrox_app`).

20260818_0010 already solved this exact class of problem for
athlete_profiles via a SECURITY DEFINER function,
`shares_active_team_with(target_user_id)`, which reads team_memberships
with the table owner's privileges instead of the caller's. Point
measurements and daily_steps at that same function rather than their own
broken inline subquery -- no new function needed.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260824_0018"
down_revision: str | None = "20260823_0017"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

USER_MATCH = "user_id = NULLIF(current_setting('app.current_user_id', true), '')"
CURRENT_USER = "NULLIF(current_setting('app.current_user_id', true), '')"

BROKEN_SHARED_TEAM_EXISTS = """EXISTS (
    SELECT 1 FROM team_memberships mine
    JOIN team_memberships theirs ON theirs.team_id = mine.team_id
    WHERE mine.user_id = {current_user}
      AND mine.status = 'active'
      AND theirs.user_id = {table}.user_id
      AND theirs.status = 'active'
)"""


def upgrade() -> None:
    op.execute("DROP POLICY measurements_select ON measurements")
    op.execute(
        f"CREATE POLICY measurements_select ON measurements FOR SELECT USING ("
        f"{USER_MATCH} OR (visibility = 'team' AND shares_active_team_with(user_id)))"
    )

    op.execute("DROP POLICY daily_steps_select ON daily_steps")
    op.execute(
        f"CREATE POLICY daily_steps_select ON daily_steps FOR SELECT USING ("
        f"{USER_MATCH} OR (visibility = 'team' AND shares_active_team_with(user_id)))"
    )


def downgrade() -> None:
    op.execute("DROP POLICY measurements_select ON measurements")
    op.execute(
        f"CREATE POLICY measurements_select ON measurements FOR SELECT USING ("
        f"{USER_MATCH} OR (visibility = 'team' AND "
        f"{BROKEN_SHARED_TEAM_EXISTS.format(current_user=CURRENT_USER, table='measurements')}))"
    )

    op.execute("DROP POLICY daily_steps_select ON daily_steps")
    op.execute(
        f"CREATE POLICY daily_steps_select ON daily_steps FOR SELECT USING ("
        f"{USER_MATCH} OR (visibility = 'team' AND "
        f"{BROKEN_SHARED_TEAM_EXISTS.format(current_user=CURRENT_USER, table='daily_steps')}))"
    )
