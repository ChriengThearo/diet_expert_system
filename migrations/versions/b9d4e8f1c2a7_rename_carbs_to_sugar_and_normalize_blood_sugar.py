"""rename carbs to sugar and normalize blood sugar payloads

Revision ID: b9d4e8f1c2a7
Revises: f4b2c7d9e1a6
Create Date: 2026-04-21 09:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
import json
import re


# revision identifiers, used by Alembic.
revision = "b9d4e8f1c2a7"
down_revision = "f4b2c7d9e1a6"
branch_labels = None
depends_on = None


def _replace_word(text: str, old_word: str, new_word: str) -> str:
    def repl(match: re.Match[str]) -> str:
        token = match.group(0)
        if token.isupper():
            return new_word.upper()
        if token[:1].isupper():
            return new_word[:1].upper() + new_word[1:]
        return new_word

    return re.sub(rf"\b{re.escape(old_word)}\b", repl, text, flags=re.IGNORECASE)


def _transform_value(value, key_map, word_swap=None):
    if isinstance(value, dict):
        transformed = {}
        for key, item in value.items():
            new_key = key_map.get(key, key)
            transformed[new_key] = _transform_value(item, key_map, word_swap)
        return transformed

    if isinstance(value, list):
        return [_transform_value(item, key_map, word_swap) for item in value]

    if isinstance(value, str) and word_swap:
        old_word, new_word = word_swap
        return _replace_word(value, old_word, new_word)

    return value


def _transform_rule_conditions(raw_value: str, key_map, word_swap):
    if raw_value in (None, ""):
        return raw_value

    try:
        parsed = json.loads(raw_value)
    except Exception:
        old_word, new_word = word_swap
        return _replace_word(str(raw_value), old_word, new_word)

    transformed = _transform_value(parsed, key_map, word_swap)
    return json.dumps(transformed, ensure_ascii=False)


def _transform_result_data(raw_value: str, key_map):
    if raw_value in (None, ""):
        return raw_value

    try:
        parsed = json.loads(raw_value)
    except Exception:
        return raw_value

    transformed = _transform_value(parsed, key_map)
    return json.dumps(transformed, ensure_ascii=False)


def _rename_column_if_present(table_name: str, old_column: str, new_column: str):
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if table_name not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns(table_name)}
    if old_column not in columns or new_column in columns:
        return

    with op.batch_alter_table(table_name, schema=None) as batch_op:
        batch_op.alter_column(
            old_column,
            existing_type=sa.Float(),
            existing_nullable=True,
            new_column_name=new_column,
        )


def _rewrite_diet_rule_conditions(key_map, word_swap):
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "tbl_diet_rules" not in inspector.get_table_names():
        return

    diet_rules = sa.table(
        "tbl_diet_rules",
        sa.column("id", sa.Integer()),
        sa.column("conditions", sa.Text()),
    )

    rows = bind.execute(
        sa.select(diet_rules.c.id, diet_rules.c.conditions)
    ).mappings().all()

    for row in rows:
        original = row["conditions"]
        transformed = _transform_rule_conditions(original, key_map, word_swap)
        if transformed != original:
            bind.execute(
                diet_rules.update()
                .where(diet_rules.c.id == row["id"])
                .values(conditions=transformed)
            )


def _rewrite_user_result_payloads(key_map):
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "tbl_user_results" not in inspector.get_table_names():
        return

    user_results = sa.table(
        "tbl_user_results",
        sa.column("id", sa.Integer()),
        sa.column("result_data", sa.Text()),
    )

    rows = bind.execute(
        sa.select(user_results.c.id, user_results.c.result_data)
    ).mappings().all()

    for row in rows:
        original = row["result_data"]
        transformed = _transform_result_data(original, key_map)
        if transformed != original:
            bind.execute(
                user_results.update()
                .where(user_results.c.id == row["id"])
                .values(result_data=transformed)
            )


def upgrade():
    _rename_column_if_present("tbl_foods", "carbs", "sugar")
    _rename_column_if_present("tbl_cooked_foods", "carbs", "sugar")

    _rewrite_diet_rule_conditions(
        key_map={"carbs": "sugar", "bloodSugar": "blood_sugar"},
        word_swap=("carbs", "sugar"),
    )
    _rewrite_user_result_payloads(
        key_map={"carbs": "sugar", "bloodSugar": "blood_sugar"}
    )


def downgrade():
    _rename_column_if_present("tbl_foods", "sugar", "carbs")
    _rename_column_if_present("tbl_cooked_foods", "sugar", "carbs")

    _rewrite_diet_rule_conditions(
        key_map={"sugar": "carbs", "blood_sugar": "bloodSugar"},
        word_swap=("sugar", "carbs"),
    )
    _rewrite_user_result_payloads(
        key_map={"sugar": "carbs", "blood_sugar": "bloodSugar"}
    )
