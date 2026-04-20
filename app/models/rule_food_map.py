from extensions import db

class RuleFoodMapTable(db.Model):
    __tablename__ = "tbl_rule_food_map"

    id = db.Column(db.Integer, primary_key=True)
    diet_rule_id = db.Column(db.Integer, db.ForeignKey("tbl_diet_rules.id"), nullable=False)
    food_id = db.Column(db.Integer, db.ForeignKey("tbl_foods.id"), nullable=True)
    cooked_food_id = db.Column(db.Integer, db.ForeignKey("tbl_cooked_foods.id"), nullable=True)
    notes = db.Column(db.String(255))

    diet_rule = db.relationship("DietRulesTable", back_populates="rule_food_maps")
    food = db.relationship("FoodsTable", back_populates="rule_food_maps")
    cooked_food = db.relationship("CookedFoodsTable", back_populates="rule_food_maps")

    def __repr__(self) -> str:
        return (
            f"<RuleFoodMap {self.diet_rule_id}-food:{self.food_id}"
            f"-cooked:{self.cooked_food_id}>"
        )
