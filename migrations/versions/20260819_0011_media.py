"""Create media_assets and media_links tables for Phase 5 (media uploads).

Policies follow the meals/workouts pattern: a table's SELECT policy may
subquery team_memberships for the caller's own team_id list (safe — that
only ever needs `user_id = self`), but never subqueries its own table. See
migration 20260817_0009 for why the latter causes infinite recursion.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260819_0011"
down_revision: str | None = "20260818_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

USER_MATCH = "user_id = NULLIF(current_setting('app.current_user_id', true), '')"


def upgrade() -> None:
    op.create_table(
        "media_assets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.String(length=255), nullable=False),
        sa.Column("team_id", sa.Uuid(), nullable=True),
        sa.Column("storage_path", sa.Text(), nullable=False),
        sa.Column("mime_type", sa.String(length=80), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("purpose", sa.String(length=24), nullable=False),
        sa.Column("visibility", sa.String(length=16), server_default="private", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("size_bytes > 0", name="ck_media_assets_size_positive"),
        sa.CheckConstraint(
            "purpose IN ('workout_evidence', 'meal_photo', 'measurement', 'other')",
            name="ck_media_assets_purpose",
        ),
        sa.CheckConstraint("visibility IN ('team', 'private')", name="ck_media_assets_visibility"),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("storage_path"),
    )
    op.create_index("ix_media_assets_user_id", "media_assets", ["user_id"])

    op.create_table(
        "media_links",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("media_asset_id", sa.Uuid(), nullable=False),
        sa.Column("entity_type", sa.String(length=20), nullable=False),
        sa.Column("entity_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "entity_type IN ('workout', 'meal', 'measurement')",
            name="ck_media_links_entity_type",
        ),
        sa.ForeignKeyConstraint(["media_asset_id"], ["media_assets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "media_asset_id", "entity_type", "entity_id", name="uq_media_links_asset_entity"
        ),
    )
    op.create_index("ix_media_links_entity", "media_links", ["entity_type", "entity_id"])

    op.execute("ALTER TABLE media_assets ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE media_assets FORCE ROW LEVEL SECURITY")
    op.execute(
        f"CREATE POLICY media_assets_select ON media_assets FOR SELECT USING ("
        f"{USER_MATCH} OR ("
        f"visibility = 'team' AND team_id IN ("
        f"SELECT team_id FROM team_memberships "
        f"WHERE {USER_MATCH} AND status = 'active'"
        f")))"
    )
    op.execute(
        f"CREATE POLICY media_assets_insert ON media_assets FOR INSERT WITH CHECK ({USER_MATCH})"
    )
    op.execute(
        f"CREATE POLICY media_assets_update ON media_assets FOR UPDATE "
        f"USING ({USER_MATCH}) WITH CHECK ({USER_MATCH})"
    )
    op.execute(f"CREATE POLICY media_assets_delete ON media_assets FOR DELETE USING ({USER_MATCH})")

    op.execute("ALTER TABLE media_links ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE media_links FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY media_links_select ON media_links FOR SELECT USING ("
        "media_asset_id IN (SELECT id FROM media_assets))"
    )
    op.execute(
        f"CREATE POLICY media_links_insert ON media_links FOR INSERT WITH CHECK ("
        f"media_asset_id IN (SELECT id FROM media_assets WHERE {USER_MATCH}))"
    )
    op.execute(
        f"CREATE POLICY media_links_delete ON media_links FOR DELETE USING ("
        f"media_asset_id IN (SELECT id FROM media_assets WHERE {USER_MATCH}))"
    )

    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON media_assets TO hyrox_app")
    op.execute("GRANT SELECT, INSERT, DELETE ON media_links TO hyrox_app")


def downgrade() -> None:
    op.execute("REVOKE ALL PRIVILEGES ON media_links FROM hyrox_app")
    op.execute("REVOKE ALL PRIVILEGES ON media_assets FROM hyrox_app")
    op.drop_table("media_links")
    op.drop_table("media_assets")
