"""Let teammates see each other's athlete_profiles row (for team analytics/rosters).

athlete_profiles previously used a single owner-only FOR ALL policy, which
blocks the team comparison DTO (and existing measurements/steps sharing code
in api/services/teams.teammate_user_ids) from resolving anything about a
teammate.

The natural policy - "user_id IN (SELECT ... FROM team_memberships WHERE
current user shares an active team)" - cannot be written directly: since the
20260817_0009 fix, team_memberships' own SELECT policy only exposes the
current user's row, so any subquery against team_memberships from another
table's policy sees nobody but yourself, no matter which table is asking.

Fix it the way 20260817_0009 anticipated: a SECURITY DEFINER helper function
that reads team_memberships with the table owner's privileges instead of the
caller's. That requires the table owner to actually be exempt from RLS on
team_memberships, which needs NO FORCE ROW LEVEL SECURITY (FORCE would make
the policy apply to the owner too, defeating the point). hyrox_app is never
the table owner, so its direct access stays fully policy-restricted either
way - only the SECURITY DEFINER function's internal query is exempt.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260818_0010"
down_revision: str | None = "20260817_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

USER_MATCH = "user_id = NULLIF(current_setting('app.current_user_id', true), '')"


def upgrade() -> None:
    op.execute("ALTER TABLE team_memberships NO FORCE ROW LEVEL SECURITY")

    op.execute(
        """
        CREATE FUNCTION shares_active_team_with(target_user_id text)
        RETURNS boolean
        LANGUAGE sql
        SECURITY DEFINER
        STABLE
        SET search_path = public
        AS $$
            SELECT EXISTS (
                SELECT 1
                FROM team_memberships tm1
                JOIN team_memberships tm2 ON tm2.team_id = tm1.team_id
                WHERE tm1.user_id = NULLIF(current_setting('app.current_user_id', true), '')
                  AND tm1.status = 'active'
                  AND tm2.user_id = target_user_id
                  AND tm2.status = 'active'
            )
        $$
        """
    )
    op.execute("REVOKE ALL ON FUNCTION shares_active_team_with(text) FROM PUBLIC")
    op.execute("GRANT EXECUTE ON FUNCTION shares_active_team_with(text) TO hyrox_app")

    # Roster enumeration for the team comparison DTO: only returns rows for a
    # team the caller is themselves an active member of.
    op.execute(
        """
        CREATE FUNCTION team_member_user_ids(target_team_id uuid)
        RETURNS TABLE(user_id text)
        LANGUAGE sql
        SECURITY DEFINER
        STABLE
        SET search_path = public
        AS $$
            SELECT tm2.user_id
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
    op.execute("REVOKE ALL ON FUNCTION team_member_user_ids(uuid) FROM PUBLIC")
    op.execute("GRANT EXECUTE ON FUNCTION team_member_user_ids(uuid) TO hyrox_app")

    op.execute("DROP POLICY athlete_profiles_owner_all ON athlete_profiles")
    op.execute(
        f"CREATE POLICY athlete_profiles_select ON athlete_profiles FOR SELECT "
        f"USING ({USER_MATCH} OR shares_active_team_with(user_id))"
    )
    op.execute(
        f"CREATE POLICY athlete_profiles_insert ON athlete_profiles FOR INSERT "
        f"WITH CHECK ({USER_MATCH})"
    )
    op.execute(
        f"CREATE POLICY athlete_profiles_update ON athlete_profiles FOR UPDATE "
        f"USING ({USER_MATCH}) WITH CHECK ({USER_MATCH})"
    )
    op.execute(
        f"CREATE POLICY athlete_profiles_delete ON athlete_profiles FOR DELETE "
        f"USING ({USER_MATCH})"
    )


def downgrade() -> None:
    op.execute("DROP POLICY athlete_profiles_delete ON athlete_profiles")
    op.execute("DROP POLICY athlete_profiles_update ON athlete_profiles")
    op.execute("DROP POLICY athlete_profiles_insert ON athlete_profiles")
    op.execute("DROP POLICY athlete_profiles_select ON athlete_profiles")
    op.execute(
        f"CREATE POLICY athlete_profiles_owner_all ON athlete_profiles "
        f"FOR ALL USING ({USER_MATCH}) WITH CHECK ({USER_MATCH})"
    )
    op.execute("DROP FUNCTION team_member_user_ids(uuid)")
    op.execute("DROP FUNCTION shares_active_team_with(text)")
    op.execute("ALTER TABLE team_memberships FORCE ROW LEVEL SECURITY")
