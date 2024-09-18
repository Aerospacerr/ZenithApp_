from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from recommendation import RecommendationEngine
import pandas as pd

# Load your food data
df = pd.read_csv("updated_food_data_with_clusters.csv")

app = FastAPI()


# Pydantic Models to define request body structure
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


@app.post("/generate_recommendations")
def generate_recommendations(recommendation_input: RecommendationInput):
    """Endpoint to generate meal recommendations based on input meal plan and target macros."""

    # Initialize RecommendationEngine
    recommendation_engine = RecommendationEngine(df)

    # Extract the meal plan and target macros
    meal_plan = recommendation_input.meal_plan
    target_macros = recommendation_input.target_macros

    # Generate recommendations
    recommendations = recommendation_engine.generate_recommendations(
        meal_plan=meal_plan.meals, target_macros=target_macros
    )

    if not recommendations:
        raise HTTPException(status_code=400, detail="Recommendation generation failed.")

    return recommendations
