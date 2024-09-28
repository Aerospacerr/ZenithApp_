import random
import numpy as np
from genetic_algo import GeneticAlgorithm
from user import User
import streamlit as st
import re


class MealGenerator:
    def __init__(self, user, meals, df):
        self.user = user
        self.meals = meals  # e.g., {"Breakfast": 0.3, "Lunch": 0.4, "Dinner": 0.3}
        self.df = df
        self.final_meal_plan = {}

    def sum_selected_items(self, selected_items):
        """Sum up the nutritional values of the user-selected food items."""
        food_items = []
        for item in selected_items:
            row = self.df[self.df["FOOD ITEM"] == item]
            if row.empty:
                continue
            row = row.iloc[0]
            food_items.append(
                {
                    "name": row["FOOD ITEM"],
                    "category": row["CATEGORY"],  # Include the category
                    "protein": float(row["PROTEIN"]),  # Ensure conversion to float
                    "carbs": float(row["NET CARBS"]),  # Ensure conversion to float
                    "fats": float(row["FATS"]),  # Ensure conversion to float
                    "calories": float(row["CALORIES"]),  # Ensure conversion to float
                    "sugars": float(row["TOTAL SUGARS"]),  # Include sugars
                    "fiber": float(row["DIETARY FIBRE"]),  # Include dietary fiber
                    "unit_category": row["unit_category"],  # Pass unit_category
                    "quantity": float(row["QUANTITY"]),
                    "unit": row.get("UNIT", "unit"),  # Get unit or use a default value
                }
            )

        if not food_items:
            return None, "No food items selected."

        return food_items, None

    def generate_meal(self, meal_name, selected_items):
        """Generate a meal using the genetic algorithm."""
        food_items, error_message = self.sum_selected_items(selected_items)
        if error_message:
            self.final_meal_plan[meal_name] = {
                "items": [],
                "macros": {},
                "message": error_message,
            }
            return

        # Define target nutrients for the meal
        target_nutrients = {
            "calories": self.user.calories * self.meals[meal_name],
            "protein": self.user.protein * self.meals[meal_name],
            "carbs": self.user.carbs * self.meals[meal_name],
            "fats": self.user.fats * self.meals[meal_name],
        }

        # Initialize and run the genetic algorithm
        ga = GeneticAlgorithm(food_items, target_nutrients)
        best_solution, best_fitness_score = ga.run()

        # Calculate the nutritional values of the best solution
        best_calories, best_protein, best_carbs, best_fats = ga.calculate_nutrients(
            best_solution
        )

        # Format the best meal plan
        meal_items = [
            {
                "name": food_items[i]["name"],
                "quantity": (
                    f"{best_solution[i]:.2f} g"
                    if food_items[i]["unit_category"] == "Base Units"
                    else f"{best_solution[i]}*({int(food_items[i]['quantity'])} {food_items[i]['unit']})"
                ),
                "macros": {
                    "calories": (
                        food_items[i]["calories"]
                        * (best_solution[i] / food_items[i]["quantity"])
                        if food_items[i]["unit_category"] == "Base Units"
                        else food_items[i]["calories"] * best_solution[i]
                    ),
                    "protein": (
                        food_items[i]["protein"]
                        * (best_solution[i] / food_items[i]["quantity"])
                        if food_items[i]["unit_category"] == "Base Units"
                        else food_items[i]["protein"] * best_solution[i]
                    ),
                    "carbs": (
                        food_items[i]["carbs"]
                        * (best_solution[i] / food_items[i]["quantity"])
                        if food_items[i]["unit_category"] == "Base Units"
                        else food_items[i]["carbs"] * best_solution[i]
                    ),
                    "fats": (
                        food_items[i]["fats"]
                        * (best_solution[i] / food_items[i]["quantity"])
                        if food_items[i]["unit_category"] == "Base Units"
                        else food_items[i]["fats"] * best_solution[i]
                    ),
                    "sugars": (
                        food_items[i]["sugars"]
                        * (best_solution[i] / food_items[i]["quantity"])
                        if food_items[i]["unit_category"] == "Base Units"
                        else food_items[i]["sugars"] * best_solution[i]
                    ),
                    "fiber": (
                        food_items[i]["fiber"]
                        * (best_solution[i] / food_items[i]["quantity"])
                        if food_items[i]["unit_category"] == "Base Units"
                        else food_items[i]["fiber"] * best_solution[i]
                    ),
                },
            }
            for i in range(len(food_items))
        ]

        self.final_meal_plan[meal_name] = {
            "items": meal_items,
            "macros": {
                "calories": best_calories,
                "protein": best_protein,
                "carbs": best_carbs,
                "fats": best_fats,
                "sugars": sum(item["macros"]["sugars"] for item in meal_items),
                "fiber": sum(item["macros"]["fiber"] for item in meal_items),
            },
            "fitness_score": best_fitness_score,
        }

    def generate_full_plan(self, user_selected_items):
        """Generate the full meal plan using the genetic algorithm."""
        for meal, selected_items in user_selected_items.items():
            self.generate_meal(meal, selected_items)
        return self.final_meal_plan

    # Function to extract numeric portion from a string like "120.15 g"
    def extract_numeric_value(self, quantity_str):
        """Extract numeric value from the portion string."""
        match = re.match(r"([\d.]+)", quantity_str)
        if match:
            return float(match.group(1))
        else:
            raise ValueError(f"Cannot extract numeric value from '{quantity_str}'")

    # Function to calculate nutrients per portion
    def calculate_nutrient_per_portion(
        self, alternative, original_portion, original_food
    ):
        """Calculate the nutrient values for the recommended food item based on the original food portion size."""
        quantity_numeric = self.extract_numeric_value(
            original_food["quantity"]
        )  # Extract numeric part

        return {
            "quantity": quantity_numeric,
            "calories": float(alternative["CALORIES"]) * original_portion / 100,
            "protein": float(alternative["PROTEIN"]) * original_portion / 100,
            "carbs": float(alternative["NET CARBS"]) * original_portion / 100,
            "fats": float(alternative["FATS"]) * original_portion / 100,
        }

    # Function to calculate the difference between target and actual macros
    def calculate_macro_differences(self, target_macros, actual_macros):
        differences = {}
        for meal_name, actual in actual_macros.items():
            target = target_macros.get(meal_name, {})
            differences[meal_name] = {
                "calories_diff": target["calories"] - actual["calories"],
                "protein_diff": target["protein"] - actual["protein"],
                "carbs_diff": target["carbs"] - actual["carbs"],
                "fats_diff": target["fats"] - actual["fats"],
            }
        return differences

        # Function to calculate adjusted macros for each meal

    def calculate_adjusted_macros(self):
        """Calculate the adjusted macros for each meal based on user-selected percentages."""
        adjusted_macros = {}
        for meal, percentage in self.meals.items():
            adjusted_macros[meal] = {
                "calories": self.user.calories * percentage,
                "protein": self.user.protein * percentage,
                "carbs": self.user.carbs * percentage,
                "fats": self.user.fats * percentage,
            }
        return adjusted_macros
