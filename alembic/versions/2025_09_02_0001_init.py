from __future__ import annotations
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "2025_09_02_0001"
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    txn_type = sa.Enum(
        "ADJUSTMENT",
        "IN",
        "OUT",
        "TRANSFER",
        "RESERVE",
        "RELEASE",
        name="inventory_txn_type",
    )
    po_status = sa.Enum("DRAFT", "OPEN", "RECEIVED", "CANCELLED", name="po_status")

    op.create_table(
        "product",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("sku", sa.String(64), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("unit", sa.String(16), nullable=False, server_default="pcs"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "location",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(32), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "supplier",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(64), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "inventory_item",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("location_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("on_hand", sa.Numeric(14, 4), nullable=False, server_default="0"),
        sa.Column("reserved", sa.Numeric(14, 4), nullable=False, server_default="0"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["product_id"], ["product.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["location_id"], ["location.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("product_id", "location_id", name="uq_inventory_item_product_location"),
    )
    op.create_index(
        "ix_inventory_item_product_location",
        "inventory_item",
        ["product_id", "location_id"],
    )

    op.create_table(
        "inventory_txn",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("from_location_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("to_location_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("qty", sa.Numeric(14, 4), nullable=False),
        sa.Column("txn_type", txn_type, nullable=False),
        sa.Column("reason", sa.String(255), nullable=True),
        sa.Column("reference", sa.String(255), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["product_id"], ["product.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["from_location_id"], ["location.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["to_location_id"], ["location.id"], ondelete="SET NULL"),
    )

    op.create_table(
        "purchase_order",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("supplier_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", po_status, nullable=False, server_default="DRAFT"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["supplier_id"], ["supplier.id"], ondelete="RESTRICT"),
    )
    op.create_table(
        "purchase_order_line",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("purchase_order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("qty_ordered", sa.Numeric(14, 4), nullable=False),
        sa.Column("qty_received", sa.Numeric(14, 4), nullable=False, server_default="0"),
        sa.Column("unit_cost", sa.Numeric(14, 4), nullable=True),
        sa.ForeignKeyConstraint(["purchase_order_id"], ["purchase_order.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["product.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("purchase_order_id", "product_id", name="uq_pol_po_product"),
    )


def downgrade() -> None:
    op.drop_table("purchase_order_line")
    op.drop_table("purchase_order")
    op.drop_table("inventory_txn")
    op.drop_table("inventory_item")
    op.drop_table("supplier")
    op.drop_table("location")
    op.drop_table("product")
    op.execute("DROP TYPE IF EXISTS inventory_txn_type")
    op.execute("DROP TYPE IF EXISTS po_status")