import streamlit as st


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
