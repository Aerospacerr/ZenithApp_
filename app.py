import streamlit as st
import pandas as pd
import os
from user import User
from meal_generator import MealGenerator
from recommendation_rulebase import (
    RecommendationEngine as RuleBasedRecommendationEngine,
)
from data_handler import DataHandler
from user_input import get_user_input
from visualization import create_macros_chart


def main():
    # Step 1: Load the cleaned data from the data/ folder
    data_handler = DataHandler(file_path="data/updated_food_data_with_clusters.csv")
    data_handler.load_data()
    df_cleaned = data_handler.get_data()

    # Initialize session state for meal plan, user, and recommendations
    if "final_plan" not in st.session_state:
        st.session_state.final_plan = None
    if "user" not in st.session_state:
        st.session_state.user = None
    if "recommendations_v2" not in st.session_state:
        st.session_state.recommendations_v2 = None

    # Get user input
    name, age, weight, height, activity_level, meals, user_selected_items = (
        get_user_input(df_cleaned)
    )

    if not any(user_selected_items.values()):
        st.warning(
            "Please select food items for at least one meal before generating the meal plan."
        )
        return

    # Button to generate the meal plan
    if st.button("Generate Meal Plan"):
        # Step 2: Create a user and calculate their macros
        user = User(
            name=name,
            age=age,
            weight=weight,
            height=height,
            activity_level=activity_level,
        )
        user.calculate_macros()
        st.session_state.user = user  # Store the user object in session state
        st.markdown("### User Information")
        st.json(user.display_user_info())  # Display user info as JSON

        # Step 3: Generate the meal plan using user-selected foods
        meal_generator = MealGenerator(user, meals, df_cleaned)
        final_plan = meal_generator.generate_full_plan(user_selected_items)
        st.session_state.final_plan = final_plan

        # Display meal plan
        if final_plan:
            st.markdown("## Generated Meal Plan")
            st.json(final_plan)

    if st.session_state.final_plan and st.button("Generate Recommendations"):
        st.write("Generating recommendations...")

        # Initialize the Recommendation Engine
        rule_based_recommendation_engine = RuleBasedRecommendationEngine(
            df_cleaned,
            {
                "calories": st.session_state.user.calories,
                "protein": st.session_state.user.protein,
                "carbs": st.session_state.user.carbs,
                "fats": st.session_state.user.fats,
            },
        )

        # Generate recommendations based on the meal plan
        recommendations = rule_based_recommendation_engine.generate_recommendations(
            st.session_state.final_plan
        )

        if not recommendations:
            st.write("No recommendations found.")
        else:
            st.write("Recommendations:")
            st.session_state.recommendations_v2 = recommendations

            # Display recommendations
            meal_generator = MealGenerator(st.session_state.user, meals, df_cleaned)

            for recommendation in recommendations:
                meal = recommendation.get("meal", "N/A")
                item = recommendation.get("item", "N/A")
                issue = recommendation.get("issue", "N/A")
                alternatives = recommendation.get("alternatives", [])

                st.markdown(f"### Meal: {meal}")
                st.markdown(f"**Most Deviated Item**: {item}")
                st.markdown(f"**Issue**: {issue}")

                if alternatives:
                    st.markdown(
                        "**Consider these alternatives with calculated nutrients for the same calorie content:**"
                    )

                    original_food = next(
                        (
                            x
                            for x in st.session_state.final_plan[meal]["items"]
                            if x["name"] == item
                        ),
                        None,
                    )

                    if original_food:
                        original_calories = original_food["macros"]["calories"]

                        for alt in alternatives:
                            alt_food_name = alt["alternative"]
                            alt_quantity = alt["quantity"]
                            deviation = alt["deviation"]

                            # Adjust quantity to match original food's calorie content
                            alt_food_data = df_cleaned[
                                df_cleaned["FOOD ITEM"] == alt_food_name
                            ].iloc[0]

                            # Calculate the new portion size to match the original food's calories
                            alt_nutrients = (
                                meal_generator.calculate_nutrient_per_portion(
                                    alt_food_data, original_calories, original_food
                                )
                            )

                            # Display alternative food, quantity, and nutrient deviations
                            st.markdown(f"**Alternative:** {alt_food_name}")
                            st.write(f"Quantity: {alt_nutrients['quantity']}")
                            st.write("**Nutrient Deviations**:")
                            st.json(deviation)
                else:
                    st.markdown("No alternatives available.")


if __name__ == "__main__":
    main()
