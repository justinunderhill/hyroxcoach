"""Add team_roster() SECURITY DEFINER function returning role/status per member.

Caught by manually verifying the team-invite system's RLS behaviour against
the real dev DB (not just SQLite pytest, which has no RLS to catch this):
`GET /api/teams/{team_id}` queried team_memberships directly for the full
roster (user_id, role, status). Per migration 20260817_0009 / 20260818_0010,
any direct query against team_memberships -- from any table's policy or from
plain app code -- collapses to "just the caller's own row" under real RLS,
even though it looks correct against SQLite. `team_member_user_ids()`
(20260818_0010) already solves this for user_id-only roster reads; this adds
the same pattern for the fuller (user_id, role, status) row shape the team
detail endpoint needs.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260823_0017"
down_revision: str | None = "20260823_0016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE FUNCTION team_roster(target_team_id uuid)
        RETURNS TABLE(user_id text, role text, status text)
        LANGUAGE sql
        SECURITY DEFINER
        STABLE
        SET search_path = public
        AS $$
            SELECT tm2.user_id, tm2.role, tm2.status
            FROM team_memberships tm2
            WHERE tm2.team_id = target_team_id
              AND tm2.status = 'active'
              AND EXISTS (
                  SELECT 1 FROM team_memberships tm1
                  WHERE tm1.team_id = target_team_id
                    AND tm1.user_id = NULLIF(current_setting('app.current_user_id', true), '')
                    AND tm1.status = 'active'
              )
        $$
        """
    )
    op.execute("REVOKE ALL ON FUNCTION team_roster(uuid) FROM PUBLIC")
    op.execute("GRANT EXECUTE ON FUNCTION team_roster(uuid) TO hyrox_app")


def downgrade() -> None:
    op.execute("DROP FUNCTION team_roster(uuid)")
