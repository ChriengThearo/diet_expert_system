"""add tbl_food_groups and move rule-food linkage through it

Revision ID: d2a7c4e9f1b8
Revises: b9d4e8f1c2a7
Create Date: 2026-04-21 15:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "d2a7c4e9f1b8"
down_revision = "b9d4e8f1c2a7"
branch_labels = None
depends_on = None


def _table_exists(inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _column_names(inspector, table_name: str):
    return {column["name"] for column in inspector.get_columns(table_name)}


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _table_exists(inspector, "tbl_food_groups"):
        food_group_columns = _column_names(inspector, "tbl_food_groups")
        if "group_key" not in food_group_columns:
            with op.batch_alter_table("tbl_food_groups", schema=None) as batch_op:
                batch_op.add_column(
                    sa.Column(
                        "group_key",
                        sa.String(length=64),
                        nullable=False,
                        server_default="group_1",
                    )
                )
            inspector = sa.inspect(bind)
            food_group_columns = _column_names(inspector, "tbl_food_groups")
    else:
        op.create_table(
            "tbl_food_groups",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("diet_rule_id", sa.Integer(), nullable=False),
            sa.Column("rule_food_map_id", sa.Integer(), nullable=False),
            sa.Column(
                "group_key",
                sa.String(length=64),
                nullable=False,
                server_default="group_1",
            ),
            sa.ForeignKeyConstraint(
                ["diet_rule_id"], ["tbl_diet_rules.id"], ondelete="CASCADE"
            ),
            sa.ForeignKeyConstraint(
                ["rule_food_map_id"], ["tbl_rule_food_map.id"], ondelete="CASCADE"
            ),
        )
        op.create_index(
            "ix_tbl_food_groups_diet_rule_id", "tbl_food_groups", ["diet_rule_id"]
        )
        op.create_index(
            "ix_tbl_food_groups_rule_food_map_id",
            "tbl_food_groups",
            ["rule_food_map_id"],
        )
        inspector = sa.inspect(bind)
        food_group_columns = _column_names(inspector, "tbl_food_groups")

    if _table_exists(sa.inspect(bind), "tbl_food_groups"):
        existing_indexes = {
            idx["name"] for idx in sa.inspect(bind).get_indexes("tbl_food_groups")
        }
        if "ix_tbl_food_groups_diet_rule_id" not in existing_indexes:
            op.create_index(
                "ix_tbl_food_groups_diet_rule_id", "tbl_food_groups", ["diet_rule_id"]
            )
        if "ix_tbl_food_groups_rule_food_map_id" not in existing_indexes:
            op.create_index(
                "ix_tbl_food_groups_rule_food_map_id",
                "tbl_food_groups",
                ["rule_food_map_id"],
            )

    if _table_exists(inspector, "tbl_rule_food_map"):
        rule_food_columns = _column_names(inspector, "tbl_rule_food_map")
        if "diet_rule_id" in rule_food_columns:
            if "group_key" in food_group_columns:
                op.execute(
                    sa.text(
                        """
                        INSERT INTO tbl_food_groups (diet_rule_id, rule_food_map_id, group_key)
                        SELECT m.diet_rule_id, m.id, 'group_1'
                        FROM tbl_rule_food_map m
                        LEFT JOIN tbl_food_groups g
                          ON g.rule_food_map_id = m.id
                         AND g.diet_rule_id = m.diet_rule_id
                        WHERE m.diet_rule_id IS NOT NULL
                          AND g.id IS NULL
                        """
                    )
                )
            else:
                op.execute(
                    sa.text(
                        """
                        INSERT INTO tbl_food_groups (diet_rule_id, rule_food_map_id)
                        SELECT m.diet_rule_id, m.id
                        FROM tbl_rule_food_map m
                        LEFT JOIN tbl_food_groups g
                          ON g.rule_food_map_id = m.id
                         AND g.diet_rule_id = m.diet_rule_id
                        WHERE m.diet_rule_id IS NOT NULL
                          AND g.id IS NULL
                        """
                    )
                )

            inspector = sa.inspect(bind)
            foreign_keys = inspector.get_foreign_keys("tbl_rule_food_map")
            indexes = inspector.get_indexes("tbl_rule_food_map")

            with op.batch_alter_table("tbl_rule_food_map", schema=None) as batch_op:
                for fk in foreign_keys:
                    constrained = set(fk.get("constrained_columns") or [])
                    fk_name = fk.get("name")
                    if "diet_rule_id" in constrained and fk_name:
                        batch_op.drop_constraint(fk_name, type_="foreignkey")

                for index in indexes:
                    columns = set(index.get("column_names") or [])
                    index_name = index.get("name")
                    if "diet_rule_id" in columns and index_name:
                        batch_op.drop_index(index_name)

                batch_op.drop_column("diet_rule_id")

    if _table_exists(inspector, "tbl_food_groups"):
        columns = _column_names(sa.inspect(bind), "tbl_food_groups")
        if "group_key" in columns:
            with op.batch_alter_table("tbl_food_groups", schema=None) as batch_op:
                batch_op.alter_column(
                    "group_key",
                    existing_type=sa.String(length=64),
                    server_default=None,
                )


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _table_exists(inspector, "tbl_rule_food_map"):
        columns = _column_names(inspector, "tbl_rule_food_map")
        if "diet_rule_id" not in columns:
            with op.batch_alter_table("tbl_rule_food_map", schema=None) as batch_op:
                batch_op.add_column(sa.Column("diet_rule_id", sa.Integer(), nullable=True))
                batch_op.create_foreign_key(
                    "fk_tbl_rule_food_map_diet_rule_id_tbl_diet_rules",
                    "tbl_diet_rules",
                    ["diet_rule_id"],
                    ["id"],
                )

    if _table_exists(sa.inspect(bind), "tbl_food_groups") and _table_exists(
        sa.inspect(bind), "tbl_rule_food_map"
    ):
        op.execute(
            sa.text(
                """
                UPDATE tbl_rule_food_map m
                JOIN (
                    SELECT rule_food_map_id, MIN(diet_rule_id) AS diet_rule_id
                    FROM tbl_food_groups
                    GROUP BY rule_food_map_id
                ) g ON g.rule_food_map_id = m.id
                SET m.diet_rule_id = g.diet_rule_id
                """
            )
        )

    if _table_exists(sa.inspect(bind), "tbl_food_groups"):
        indexes = {idx["name"] for idx in sa.inspect(bind).get_indexes("tbl_food_groups")}
        if "ix_tbl_food_groups_rule_food_map_id" in indexes:
            op.drop_index(
                "ix_tbl_food_groups_rule_food_map_id", table_name="tbl_food_groups"
            )
        if "ix_tbl_food_groups_diet_rule_id" in indexes:
            op.drop_index(
                "ix_tbl_food_groups_diet_rule_id", table_name="tbl_food_groups"
            )
        op.drop_table("tbl_food_groups")
