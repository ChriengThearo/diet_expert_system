"""add cooked_food_id to rule food map

Revision ID: f4b2c7d9e1a6
Revises: e21a4c9d7b3f
Create Date: 2026-04-20 11:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f4b2c7d9e1a6"
down_revision = "e21a4c9d7b3f"
branch_labels = None
depends_on = None

FK_NAME = "fk_tbl_rule_food_map_cooked_food_id_tbl_cooked_foods"
INDEX_NAME = "ix_tbl_rule_food_map_cooked_food_id"


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = inspector.get_table_names()

    if "tbl_rule_food_map" not in table_names:
        return

    existing_columns = {
        column["name"] for column in inspector.get_columns("tbl_rule_food_map")
    }
    food_id_column = next(
        (
            column
            for column in inspector.get_columns("tbl_rule_food_map")
            if column["name"] == "food_id"
        ),
        None,
    )
    if food_id_column is not None and not bool(food_id_column.get("nullable", False)):
        with op.batch_alter_table("tbl_rule_food_map", schema=None) as batch_op:
            batch_op.alter_column(
                "food_id",
                existing_type=sa.Integer(),
                nullable=True,
            )

    if "cooked_food_id" not in existing_columns:
        with op.batch_alter_table("tbl_rule_food_map", schema=None) as batch_op:
            batch_op.add_column(sa.Column("cooked_food_id", sa.Integer(), nullable=True))

    inspector = sa.inspect(bind)
    existing_indexes = {
        index["name"] for index in inspector.get_indexes("tbl_rule_food_map")
    }
    if INDEX_NAME not in existing_indexes:
        with op.batch_alter_table("tbl_rule_food_map", schema=None) as batch_op:
            batch_op.create_index(INDEX_NAME, ["cooked_food_id"], unique=False)

    table_names = inspector.get_table_names()
    if "tbl_cooked_foods" not in table_names:
        return

    existing_foreign_keys = inspector.get_foreign_keys("tbl_rule_food_map")
    has_cooked_food_fk = any(
        "cooked_food_id" in (foreign_key.get("constrained_columns") or [])
        for foreign_key in existing_foreign_keys
    )
    if not has_cooked_food_fk:
        with op.batch_alter_table("tbl_rule_food_map", schema=None) as batch_op:
            batch_op.create_foreign_key(
                FK_NAME, "tbl_cooked_foods", ["cooked_food_id"], ["id"]
            )


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = inspector.get_table_names()

    if "tbl_rule_food_map" not in table_names:
        return

    existing_indexes = {
        index["name"] for index in inspector.get_indexes("tbl_rule_food_map")
    }
    if INDEX_NAME in existing_indexes:
        with op.batch_alter_table("tbl_rule_food_map", schema=None) as batch_op:
            batch_op.drop_index(INDEX_NAME)

    for foreign_key in inspector.get_foreign_keys("tbl_rule_food_map"):
        fk_name = foreign_key.get("name")
        constrained_columns = set(foreign_key.get("constrained_columns") or [])
        if fk_name and "cooked_food_id" in constrained_columns:
            with op.batch_alter_table("tbl_rule_food_map", schema=None) as batch_op:
                batch_op.drop_constraint(fk_name, type_="foreignkey")

    existing_columns = {
        column["name"] for column in inspector.get_columns("tbl_rule_food_map")
    }
    if "cooked_food_id" in existing_columns:
        with op.batch_alter_table("tbl_rule_food_map", schema=None) as batch_op:
            batch_op.drop_column("cooked_food_id")

    food_id_column = next(
        (
            column
            for column in inspector.get_columns("tbl_rule_food_map")
            if column["name"] == "food_id"
        ),
        None,
    )
    if food_id_column is not None and bool(food_id_column.get("nullable", False)):
        op.execute(sa.text("DELETE FROM tbl_rule_food_map WHERE food_id IS NULL"))
        with op.batch_alter_table("tbl_rule_food_map", schema=None) as batch_op:
            batch_op.alter_column(
                "food_id",
                existing_type=sa.Integer(),
                nullable=False,
            )
