"""Create team_invites table (team-invite system).

DATA_MODEL.md and API_CONTRACT.md specified this since Phase 1 ("target
event setup" sibling deliverable "team invitation") but it was never built
-- team membership has required a direct DB insert until now, which was
flagged as a real gap before two-athlete usage (see project build-status
memory). Building it now.

Never store a reusable plain-text invite token (DATA_MODEL.md) -- only
token_hash (sha256 hex) is persisted; the plaintext token is returned once,
at creation, and never again.

RLS design note: the accepting user is *not yet* a team member when they
need to read/update the invite row, so the usual "team member" scoping
can't gate that access. Instead, both the SELECT and UPDATE (accept)
policies also allow access when the row's token_hash matches a
per-transaction GUC (`app.lookup_invite_token_hash`), set via
`SET LOCAL`/`set_config(..., true)` exactly like `app.current_user_id`
already is in api/database.py::set_request_user. Knowing the plaintext
token is what proves the right to read/accept that one row -- the same
trust model as a password-reset link -- so this doesn't need a
SECURITY DEFINER function the way cross-member team_memberships reads do
(see migration 20260818_0010's docstring for why *that* case needed one).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260823_0016"
down_revision: str | None = "20260822_0015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CURRENT_USER = "NULLIF(current_setting('app.current_user_id', true), '')"
LOOKUP_TOKEN_HASH = "NULLIF(current_setting('app.lookup_invite_token_hash', true), '')"
MEMBER_OF_TEAM = (
    "team_id IN (SELECT team_id FROM team_memberships "
    f"WHERE user_id = {CURRENT_USER} AND status = 'active')"
)


def upgrade() -> None:
    op.create_table(
        "team_invites",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("team_id", sa.Uuid(), nullable=False),
        sa.Column("invited_email", sa.String(length=255), nullable=True),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash", name="uq_team_invites_token_hash"),
    )
    op.create_index("ix_team_invites_team_id", "team_invites", ["team_id"])

    op.execute("ALTER TABLE team_invites ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE team_invites FORCE ROW LEVEL SECURITY")
    op.execute(
        f"CREATE POLICY team_invites_select ON team_invites FOR SELECT USING "
        f"({MEMBER_OF_TEAM} OR token_hash = {LOOKUP_TOKEN_HASH})"
    )
    op.execute(
        f"CREATE POLICY team_invites_insert ON team_invites FOR INSERT WITH CHECK "
        f"(created_by = {CURRENT_USER} AND {MEMBER_OF_TEAM})"
    )
    op.execute(
        f"CREATE POLICY team_invites_update ON team_invites FOR UPDATE "
        f"USING (token_hash = {LOOKUP_TOKEN_HASH}) "
        f"WITH CHECK (token_hash = {LOOKUP_TOKEN_HASH})"
    )
    op.execute("GRANT SELECT, INSERT, UPDATE ON team_invites TO hyrox_app")


def downgrade() -> None:
    op.execute("REVOKE ALL PRIVILEGES ON team_invites FROM hyrox_app")
    op.drop_table("team_invites")
