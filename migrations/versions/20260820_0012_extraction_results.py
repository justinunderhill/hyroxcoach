"""Create extraction_results table for Phase 6 (AI extraction).

RLS is keyed off the owning media_assets row (media_asset_id IN (SELECT id
FROM media_assets WHERE user_id = self)) rather than a column on this table
directly, mirroring the media_links pattern from migration 20260819_0011 —
safe because it queries a different table, never itself. See migration
20260817_0009 for why a table querying its own rows from within its own
policy causes infinite recursion.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260820_0012"
down_revision: str | None = "20260819_0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

OWNED_MEDIA_ASSET = (
    "media_asset_id IN (SELECT id FROM media_assets "
    "WHERE user_id = NULLIF(current_setting('app.current_user_id', true), ''))"
)


def upgrade() -> None:
    op.create_table(
        "extraction_results",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("media_asset_id", sa.Uuid(), nullable=False),
        sa.Column("extraction_type", sa.String(length=16), nullable=False),
        sa.Column("model_name", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("confidence", sa.Numeric(3, 2), nullable=True),
        sa.Column(
            "extracted_data",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "user_confirmed", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column("confirmed_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "extraction_type IN ('workout', 'meal')", name="ck_extraction_results_type"
        ),
        sa.CheckConstraint(
            "status IN ('succeeded', 'failed')", name="ck_extraction_results_status"
        ),
        sa.CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)",
            name="ck_extraction_results_confidence_range",
        ),
        sa.ForeignKeyConstraint(["media_asset_id"], ["media_assets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_extraction_results_media_asset_id", "extraction_results", ["media_asset_id"]
    )

    op.execute("ALTER TABLE extraction_results ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE extraction_results FORCE ROW LEVEL SECURITY")
    op.execute(
        f"CREATE POLICY extraction_results_select ON extraction_results FOR SELECT "
        f"USING ({OWNED_MEDIA_ASSET})"
    )
    op.execute(
        f"CREATE POLICY extraction_results_insert ON extraction_results FOR INSERT "
        f"WITH CHECK ({OWNED_MEDIA_ASSET})"
    )
    op.execute(
        f"CREATE POLICY extraction_results_update ON extraction_results FOR UPDATE "
        f"USING ({OWNED_MEDIA_ASSET}) WITH CHECK ({OWNED_MEDIA_ASSET})"
    )
    op.execute(
        f"CREATE POLICY extraction_results_delete ON extraction_results FOR DELETE "
        f"USING ({OWNED_MEDIA_ASSET})"
    )
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON extraction_results TO hyrox_app")


def downgrade() -> None:
    op.execute("REVOKE ALL PRIVILEGES ON extraction_results FROM hyrox_app")
    op.drop_table("extraction_results")
