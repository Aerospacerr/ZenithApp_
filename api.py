from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict

app = FastAPI()


# Define a request model for user input
class UserInput(BaseModel):
    name: str
    age: int
    weight: float
    height: float
    activity_level: str
    meals: Dict[str, float]


@app.post("/generate-meal-plan/")
def generate_meal_plan(user_input: UserInput):
    # This function would ideally call your existing meal generation logic
    # For now, let's return the input data as a placeholder
    return {"message": "Meal plan generated successfully!", "data": user_input.dict()}


# Additional API endpoints can be added here
