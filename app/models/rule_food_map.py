from extensions import db

class RuleFoodMapTable(db.Model):
    __tablename__ = "tbl_rule_food_map"

    id = db.Column(db.Integer, primary_key=True)
    food_id = db.Column(db.Integer, db.ForeignKey("tbl_foods.id"), nullable=True)
    cooked_food_id = db.Column(db.Integer, db.ForeignKey("tbl_cooked_foods.id"), nullable=True)
    notes = db.Column(db.String(255))

    food_groups = db.relationship(
        "FoodGroupTable", back_populates="rule_food_map", cascade="all, delete-orphan"
    )
    food = db.relationship("FoodsTable", back_populates="rule_food_maps")
    cooked_food = db.relationship("CookedFoodsTable", back_populates="rule_food_maps")

    def __repr__(self) -> str:
        return f"<RuleFoodMap id:{self.id}-food:{self.food_id}-cooked:{self.cooked_food_id}>"
