from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from meal_generator import MealGenerator
from recommendation_rulebase import (
    RecommendationEngine as RuleBasedRecommendationEngine,
)  # Use rule-based engine
from user import User
import pandas as pd

# Load your food data
df = pd.read_csv("updated_food_data_with_clusters.csv")

app = FastAPI()


# Pydantic Models for Meal Generation
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


# Pydantic Models for Recommendation
class MealItem(BaseModel):
    name: str
    macros: dict  # Example: {"calories": 500, "protein": 30, "carbs": 50, "fats": 20}


class MealDetails(BaseModel):
    items: list[MealItem]  # Example: [{"name": "item1", "macros": {...}}]


class MealPlan(BaseModel):
    meals: dict[str, MealDetails]  # Example: {"Breakfast": {...}, "Lunch": {...}}


class TargetMacros(BaseModel):
    calories: float
    protein: float
    carbs: float
    fats: float


class RecommendationInput(BaseModel):
    meal_plan: MealPlan
    target_macros: dict[
        str, TargetMacros
    ]  # Example: {"Breakfast": {...}, "Lunch": {...}}


@app.get("/")
def read_root():
    return {"message": "Welcome to the Meal Plan and Recommendation API"}


# Meal Generation API
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


# Recommendation API using rule-based engine
@app.post("/generate_recommendations")
def generate_recommendations(recommendation_input: RecommendationInput):
    """Endpoint to generate meal recommendations based on input meal plan and target macros."""

    # Extract the meal plan and target macros
    meal_plan = recommendation_input.meal_plan
    target_macros = recommendation_input.target_macros

    # Initialize RuleBasedRecommendationEngine with the user's target macros
    rule_based_recommendation_engine = RuleBasedRecommendationEngine(
        df,
        {
            "calories": target_macros[
                "Breakfast"
            ].calories,  # Simplified to one meal for example
            "protein": target_macros["Breakfast"].protein,
            "carbs": target_macros["Breakfast"].carbs,
            "fats": target_macros["Breakfast"].fats,
        },
    )

    # Generate recommendations using rule-based engine
    recommendations = rule_based_recommendation_engine.generate_recommendations(
        meal_plan=meal_plan.meals
    )

    if not recommendations:
        raise HTTPException(status_code=400, detail="Recommendation generation failed.")

    return recommendations
