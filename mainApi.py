from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from meal_generator import MealGenerator
from recommendation_rulebase import (
    RecommendationEngine as RuleBasedRecommendationEngine,
)
from user import User
import pandas as pd
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

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


# Updated Pydantic Models for Recommendation
class Macros(BaseModel):
    calories: float
    protein: float
    carbs: float
    fats: float


class MealItem(BaseModel):
    name: str
    macros: Macros  # Using explicit Macros model to ensure structure


class MealDetails(BaseModel):
    items: list[MealItem]
    macros: Macros  # Store aggregated macros per meal


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

    logging.debug("Generating meal plan for user: %s", user_input.name)

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

    logging.debug(
        "User's target nutrients: Calories=%s, Protein=%s, Carbs=%s, Fats=%s",
        user.calories,
        user.protein,
        user.carbs,
        user.fats,
    )

    # Step 3: Initialize MealGenerator
    meal_generator = MealGenerator(user, meal_selection.meals, df)

    # Step 4: Generate the full meal plan
    meal_plan = meal_generator.generate_full_plan(meal_selection.user_selected_items)

    if not meal_plan:
        logging.error("Meal plan generation failed for user: %s", user_input.name)
        raise HTTPException(status_code=400, detail="Meal plan generation failed.")

    logging.debug("Generated meal plan: %s", meal_plan)

    return meal_plan


# Recommendation API using rule-based engine
@app.post("/generate_recommendations")
def generate_recommendations(recommendation_input: RecommendationInput):
    """Endpoint to generate meal recommendations based on input meal plan and target macros."""

    logging.debug(
        "Generating recommendations for meal plan: %s", recommendation_input.meal_plan
    )

    # Extract the meal plan and target macros
    meal_plan = recommendation_input.meal_plan
    target_macros = recommendation_input.target_macros

    logging.debug("Target macros: %s", target_macros)

    # Initialize RuleBasedRecommendationEngine with the user's target macros for all meals
    rule_based_recommendation_engine = RuleBasedRecommendationEngine(
        df,
        {
            "calories": sum([target.calories for target in target_macros.values()]),
            "protein": sum([target.protein for target in target_macros.values()]),
            "carbs": sum([target.carbs for target in target_macros.values()]),
            "fats": sum([target.fats for target in target_macros.values()]),
        },
    )

    # Generate recommendations using rule-based engine
    try:
        recommendations = rule_based_recommendation_engine.generate_recommendations(
            meal_plan=meal_plan.meals
        )
    except Exception as e:
        logging.error("Error generating recommendations: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")

    if not recommendations:
        logging.error("Recommendation generation failed for meal plan: %s", meal_plan)
        raise HTTPException(status_code=400, detail="Recommendation generation failed.")

    logging.debug("Generated recommendations: %s", recommendations)

    return recommendations
