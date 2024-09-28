import streamlit as st
import pandas as pd
import os
import altair as alt
from user import User
from meal_generator import MealGenerator
from recommendation_rulebase import (
    RecommendationEngine as RuleBasedRecommendationEngine,
)
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
    data_handler = DataHandler(file_path="data/updated_food_data_with_clusters.csv")
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
    if "recommendations_v2" not in st.session_state:
        st.session_state.recommendations_v2 = None

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
        st.json(user.display_user_info())  # Display user info as JSON

        # Step 3: Generate the meal plan using user-selected foods
        meal_generator = MealGenerator(user, meals, df_cleaned)
        final_plan = meal_generator.generate_full_plan(user_selected_items)
        st.session_state.final_plan = final_plan

        # Calculate adjusted macros based on meal percentages
        adjusted_macros = meal_generator.calculate_adjusted_macros(user, meals)
        st.markdown("### Adjusted Macros per Meal (as JSON)")
        st.json(adjusted_macros)

        # Step 4: Calculate actual macros from the meal plan
        actual_macros = {}
        for meal_name, details in final_plan.items():
            actual_macros[meal_name] = details["macros"]

        # Step 5: Calculate macro differences
        macro_differences = meal_generator.calculate_macro_differences(
            adjusted_macros, actual_macros
        )
        st.markdown("### Macro Differences between Target and Generated Meal Plan")
        st.json(macro_differences)

        # Clear previous recommendations
        st.session_state.removal_recommendations = None
        st.session_state.item_recommendations = None
        st.session_state.recommendations_v2 = None

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
    if st.button("Generate Recommendations v2") and st.session_state.final_plan:
        st.write("Generating v2 recommendations...")

        # Initialize the Recommendation Engine with the cleaned data and user's target nutrients
        rule_based_recommendation_engine = RuleBasedRecommendationEngine(
            df_cleaned,
            {
                "calories": st.session_state.user.calories,
                "protein": st.session_state.user.protein,
                "carbs": st.session_state.user.carbs,
                "fats": st.session_state.user.fats,
            },
        )

        # Generate recommendations based on the final meal plan
        recommendations_v2 = rule_based_recommendation_engine.generate_recommendations(
            st.session_state.final_plan
        )

        if not recommendations_v2:
            st.write("No v2 recommendations generated.")
        else:
            st.write("V2 recommendations generated:")
            st.session_state.recommendations_v2 = recommendations_v2

            # Display recommendations with portion-adjusted nutrients
            st.markdown("## Recommendations per Meal")

            meal_generator = MealGenerator(
                st.session_state.user, meals, df_cleaned
            )  # Create meal_generator here

            for recommendation in recommendations_v2:
                meal = recommendation.get("meal", "N/A")
                item = recommendation.get("item", "N/A")
                issue = recommendation.get("issue", "N/A")
                alternatives = recommendation.get("alternatives", [])

                st.markdown(f"### Meal: {meal}")
                st.markdown(f"**Most Deviated Item**: {item}")
                st.markdown(f"**Issue**: {issue}")

                if alternatives:
                    st.markdown(
                        "**Consider these alternatives with calculated nutrients for the same portion size:**"
                    )
                    original_food = next(
                        (
                            x
                            for x in st.session_state.final_plan[meal]["items"]
                            if x["name"] == item
                        ),
                        None,
                    )
                    original_portion = float(original_food["quantity"].split()[0])

                    alt_food, similarity = alternatives[0]
                    alt_food_data = df_cleaned[
                        df_cleaned["FOOD ITEM"] == alt_food
                    ].iloc[0]
                    alt_nutrients = meal_generator.calculate_nutrient_per_portion(
                        alt_food_data, original_portion, original_food
                    )

                    deviation = (
                        rule_based_recommendation_engine.calculate_nutrient_deviation(
                            original_food["macros"], alt_nutrients
                        )
                    )

                    st.write(f"**{alt_food} (Similarity: {similarity:.2f})**")
                    st.json(alt_nutrients)
                    st.write("**Nutrient Deviations**:")
                    st.json(deviation)
                else:
                    st.markdown("No alternatives provided.")


if __name__ == "__main__":
    main()
