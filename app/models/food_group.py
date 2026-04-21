from extensions import db


class FoodGroupTable(db.Model):
    __tablename__ = "tbl_food_groups"

    id = db.Column(db.Integer, primary_key=True)
    diet_rule_id = db.Column(
        db.Integer, db.ForeignKey("tbl_diet_rules.id", ondelete="CASCADE"), nullable=False
    )
    rule_food_map_id = db.Column(
        db.Integer,
        db.ForeignKey("tbl_rule_food_map.id", ondelete="CASCADE"),
        nullable=False,
    )
    group_key = db.Column(db.String(64), nullable=False, default="group_1")

    diet_rule = db.relationship("DietRulesTable", back_populates="food_groups")
    rule_food_map = db.relationship("RuleFoodMapTable", back_populates="food_groups")

    def __repr__(self) -> str:
        return (
            f"<FoodGroup rule:{self.diet_rule_id} "
            f"group:{self.group_key} map:{self.rule_food_map_id}>"
        )

