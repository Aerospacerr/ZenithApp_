from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from meal_generator import MealGenerator
from user import User
import pandas as pd

# Load your food data
df = pd.read_csv("updated_food_data_with_clusters.csv")

app = FastAPI()


# Pydantic Models to define request body structure
class UserInput(BaseModel):
    name: str
    age: int
    weight: float
    height: float
    activity_level: str
    calories: float
    protein: float
    carbs: float
    fats: float


class MealSelection(BaseModel):
    meals: dict  # Example: {"Breakfast": 0.3, "Lunch": 0.4, "Dinner": 0.3}
    user_selected_items: (
        dict  # Example: {"Breakfast": ["item1", "item2"], "Lunch": ["item3"]}
    )


@app.post("/generate_meal_plan")
def generate_meal_plan(user_input: UserInput, meal_selection: MealSelection):
    """Endpoint to generate meal plan based on user input and meal selection."""

    # Step 1: Create a User instance
    user = User(
        name=user_input.name,
        age=user_input.age,
        weight=user_input.weight,
        height=user_input.height,
        activity_level=user_input.activity_level,
    )

    # Step 2: Set the user's target nutrients
    user.calories = user_input.calories
    user.protein = user_input.protein
    user.carbs = user_input.carbs
    user.fats = user_input.fats

    # Step 3: Initialize MealGenerator
    meal_generator = MealGenerator(user, meal_selection.meals, df)

    # Step 4: Generate the full meal plan
    meal_plan = meal_generator.generate_full_plan(meal_selection.user_selected_items)

    if not meal_plan:
        raise HTTPException(status_code=400, detail="Meal plan generation failed.")

    return meal_plan
