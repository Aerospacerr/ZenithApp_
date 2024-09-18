import streamlit as st
import pandas as pd
import os
import altair as alt

from user import User
from meal_generator import MealGenerator
from recommendation import RecommendationEngine
from data_handler import DataHandler
from user_input import get_user_input
from visualization import create_macros_chart


# Function to save user input and meal plan to a CSV file
def save_to_csv(file_path, user_info, meal_plan):
    # Ensure the directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Check if the CSV file exists, create it with headers if it doesn't
    if not os.path.isfile(file_path):
        with open(file_path, "w") as f:
            f.write(
                "Name,Age,Weight,Height,Activity Level,Calories,Protein,Carbs,Fats,Meal,Food Items,Calories per Meal,Protein per Meal,Carbs per Meal,Fats per Meal\n"
            )

    # Append the user info and meal plan to the CSV file
    with open(file_path, "a") as f:
        for meal, details in meal_plan.items():
            food_items = "; ".join(
                [f"{item['quantity']} of {item['name']}" for item in details["items"]]
            )
            f.write(
                f"{user_info['Name']},{user_info['Age']},{user_info['Weight']},{user_info['Height']},{user_info['Activity Level']},"
                f"{user_info['Calories']},{user_info['Protein']},{user_info['Carbs']},{user_info['Fats']},"
                f"{meal},{food_items},{details['macros']['calories']:.1f},{details['macros']['protein']:.1f},{details['macros']['carbs']:.1f},{details['macros']['fats']:.1f}\n"
            )


def main():
    # Step 1: Load the cleaned data from the data/ folder
    data_handler = DataHandler(file_path="data/cleaned_food_data.csv")
    data_handler.load_data()
    df_cleaned = data_handler.get_data()

    # Initialize session state for meal plan, user, and recommendations
    if "final_plan" not in st.session_state:
        st.session_state.final_plan = None
    if "user" not in st.session_state:
        st.session_state.user = None
    if "removal_recommendations" not in st.session_state:
        st.session_state.removal_recommendations = None
    if "item_recommendations" not in st.session_state:
        st.session_state.item_recommendations = None

    # Get user input
    name, age, weight, height, activity_level, meals, user_selected_items = (
        get_user_input(df_cleaned)
    )

    # Check if the user has selected any items
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
        st.write(user.display_user_info())

        # Step 3: Generate the meal plan using user-selected foods
        meal_generator = MealGenerator(user, meals, df_cleaned)
        final_plan = meal_generator.generate_full_plan(user_selected_items)

        # Store the final plan in session state
        st.session_state.final_plan = final_plan

        # Clear previous recommendations
        st.session_state.removal_recommendations = None
        st.session_state.item_recommendations = None

    # Display the generated meal plan if it exists in session state
    if st.session_state.final_plan:
        st.markdown("### Meal Plan in JSON Format")
        st.json(st.session_state.final_plan)

        st.markdown("## 🍽️ Generated Meal Plan")
        calories_data = []

        for meal, details in st.session_state.final_plan.items():
            st.markdown(f"### {meal}")
            st.markdown("**Food Items (with quantities):**")
            for item in details["items"]:
                st.write(f"{item['name']} - {item['quantity']}")

            # Store the data for the calories chart
            calories_data.append(
                {"Meal": meal, "Calories": details["macros"]["calories"]}
            )

            # Create and display macronutrient chart for each meal (excluding calories)
            macros_chart = create_macros_chart(details["macros"], meal)
            st.altair_chart(macros_chart, use_container_width=True)

        # Calories Chart
        if calories_data:
            st.markdown("### Calories Breakdown by Meal")
            calories_df = pd.DataFrame(calories_data)
            calories_chart = (
                alt.Chart(calories_df)
                .mark_bar()
                .encode(x=alt.X("Meal", sort=None), y="Calories", color="Meal")
                .properties(width=alt.Step(60))
            )
            st.altair_chart(calories_chart, use_container_width=True)

    # Initialize the recommendation engine with the DataFrame
    recommendation_engine = RecommendationEngine(df_cleaned)

    # Buttons for recommendation actions
    if st.button("Identify Items for Removal") and st.session_state.final_plan:
        removal_recommendations = {}
        for meal, details in st.session_state.final_plan.items():
            target_macros = {
                "calories": st.session_state.user.calories * meals[meal],
                "protein": st.session_state.user.protein * meals[meal],
                "carbs": st.session_state.user.carbs * meals[meal],
                "fats": st.session_state.user.fats * meals[meal],
            }
            removal_recommendations[meal] = recommendation_engine.recommend_removal(
                details, target_macros
            )

        st.session_state.removal_recommendations = removal_recommendations

    if st.session_state.removal_recommendations:
        st.markdown("### Items Recommended for Removal")
        for meal, recommendations in st.session_state.removal_recommendations.items():
            st.markdown(f"**{meal}**")
            for rec in recommendations:
                st.markdown(f"- **Remove {rec['item']}** because: {rec['reason']}")

    if st.button("Generate Item Recommendations") and st.session_state.final_plan:
        item_recommendations = {}
        for meal, details in st.session_state.final_plan.items():
            target_macros = {
                "calories": st.session_state.user.calories * meals[meal],
                "protein": st.session_state.user.protein * meals[meal],
                "carbs": st.session_state.user.carbs * meals[meal],
                "fats": st.session_state.user.fats * meals[meal],
            }
            item_recommendations[meal] = recommendation_engine.generate_recommendations(
                details, target_macros
            )

        st.session_state.item_recommendations = item_recommendations

    if st.session_state.item_recommendations:
        st.markdown("### Recommended Items for Replacement")
        for meal, recommendations in st.session_state.item_recommendations.items():
            st.markdown(f"**{meal}**")
            for rec in recommendations:
                st.markdown(
                    f"- **Replace {rec['item']}** with **{rec['replacement']}** because: {rec['reason']}"
                )


if __name__ == "__main__":
    main()
