import streamlit as st
from user import User
from meal_generator import MealGenerator
import pandas as pd
import os
import altair as alt


# DataHandler class with added error handling for missing files
class DataHandler:
    def __init__(self, file_path):
        self.file_path = file_path
        self.df_cleaned = None

    def load_data(self):
        """Load the cleaned CSV file from the specified path."""
        if not os.path.exists(self.file_path):
            st.error(f"File not found: {self.file_path}. Please check the file path.")
            st.stop()

        try:
            self.df_cleaned = pd.read_csv(self.file_path)
        except Exception as e:
            st.error(f"Error loading data: {e}")
            st.stop()

    def get_data(self):
        """Return the loaded DataFrame."""
        if self.df_cleaned is None:
            raise ValueError(
                "Data not loaded. Call load_data() before accessing the data."
            )
        return self.df_cleaned


# Function to get user input from Streamlit UI
def get_user_input(df_cleaned):
    st.title("🍽️ Personalized Meal Planner")

    st.markdown("### Enter Your Details")
    name = st.text_input("Enter your name", "John Doe")
    age = st.number_input("Enter your age", min_value=0, max_value=100, value=30)
    weight = st.number_input(
        "Enter your weight (in kg)", min_value=0.0, max_value=200.0, value=70.0
    )
    height = st.number_input(
        "Enter your height (in cm)", min_value=0.0, max_value=250.0, value=175.0
    )
    activity_level = st.selectbox(
        "Select your activity level", ["sedentary", "active", "very_active"]
    )

    st.markdown("### Meal Distribution")
    st.write("Enter the percentage of daily calories for each meal.")
    breakfast = st.slider("Breakfast (%)", min_value=0, max_value=100, value=30) / 100
    lunch = st.slider("Lunch (%)", min_value=0, max_value=100, value=40) / 100
    dinner = st.slider("Dinner (%)", min_value=0, max_value=100, value=30) / 100

    # Ensure the total distribution adds up to 100%
    if (breakfast + lunch + dinner) != 1.0:
        st.error(
            "The total percentage for all meals must equal 100%. Please adjust the sliders."
        )
        st.stop()

    meals = {"Breakfast": breakfast, "Lunch": lunch, "Dinner": dinner}

    # User-selected food items for each meal
    st.markdown("### Select Food Items for Each Meal")
    food_items = df_cleaned["FOOD ITEM"].unique()

    user_selected_items = {
        "Breakfast": st.multiselect("Breakfast Items", options=food_items),
        "Lunch": st.multiselect("Lunch Items", options=food_items),
        "Dinner": st.multiselect("Dinner Items", options=food_items),
    }

    return name, age, weight, height, activity_level, meals, user_selected_items


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


# Function to create a bar chart for macronutrients (excluding calories)
def create_macros_chart(macros, meal_name):
    # Exclude calories from the data
    macros_filtered = {k: v for k, v in macros.items() if k != "calories"}
    macros_df = pd.DataFrame.from_dict(
        macros_filtered, orient="index", columns=["Value"]
    )
    macros_df.reset_index(inplace=True)
    macros_df.columns = ["Macronutrient", "Value"]

    chart = (
        alt.Chart(macros_df)
        .mark_bar()
        .encode(x=alt.X("Macronutrient", sort=None), y="Value", color="Macronutrient")
        .properties(
            title=f"{meal_name} Macronutrient Breakdown",
            width=alt.Step(50),  # controls the width of bar.
        )
    )

    return chart


# Main function to run the Streamlit app
def main():
    # Step 1: Load the cleaned data from the data/ folder
    data_handler = DataHandler(file_path="data/cleaned_food_data.csv")
    data_handler.load_data()
    df_cleaned = data_handler.get_data()

    # Get user input
    name, age, weight, height, activity_level, meals, user_selected_items = (
        get_user_input(df_cleaned)
    )

    # Step 2: Create a user and calculate their macros
    user = User(
        name=name, age=age, weight=weight, height=height, activity_level=activity_level
    )
    user.calculate_macros()
    st.markdown("### User Information")
    st.write(user.display_user_info())

    # Step 3: Generate the meal plan using user-selected foods
    meal_generator = MealGenerator(user, meals, df_cleaned)
    final_plan = meal_generator.generate_full_plan(user_selected_items)

    # Button to display the meal plan as JSON (Now placed above the graphs)
    if st.button("Show Meal Plan as JSON"):
        st.markdown("### Meal Plan in JSON Format")
        st.json(final_plan)

    # Display the generated meal plan
    st.markdown("## 🍽️ Generated Meal Plan")
    calories_data = []

    for meal, details in final_plan.items():
        st.markdown(f"### {meal}")
        st.markdown("**Food Items (with quantities):**")
        for item in details["items"]:
            st.write(f"{item['name']} - {item['quantity']}")

        # Store the data for the calories chart
        calories_data.append({"Meal": meal, "Calories": details["macros"]["calories"]})

        # Create and display macronutrient chart for each meal (excluding calories)
        macros_chart = create_macros_chart(details["macros"], meal)
        st.altair_chart(macros_chart, use_container_width=True)

    # Calories Chart
    st.markdown("### Calories Breakdown by Meal")
    calories_df = pd.DataFrame(calories_data)
    calories_chart = (
        alt.Chart(calories_df)
        .mark_bar()
        .encode(x=alt.X("Meal", sort=None), y="Calories", color="Meal")
        .properties(width=alt.Step(60))
    )
    st.altair_chart(calories_chart, use_container_width=True)

    # Optionally save the meal plan to a CSV file
    if st.button("Save Meal Plan"):
        user_info = user.display_user_info()
        user_info.update(
            {
                "Age": age,
                "Weight": weight,
                "Height": height,
                "Activity Level": activity_level,
            }
        )
        save_to_csv("ZenithApp/data/user_meal_plans.csv", user_info, final_plan)
        st.success("Meal plan saved successfully!")


# Run the Streamlit app
if __name__ == "__main__":
    main()
