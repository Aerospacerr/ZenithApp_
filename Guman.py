import pandas as pd
import pulp

# Load food data
food_df = pd.read_csv("data/foods.csv")

# Define nutrient targets for lunch (50% of total calories)
target_nutrients = {
    "Protein": 155 * 0.5,  # 77.5 g
    "Carbs": 528 * 0.5,  # 264 g
    "Fats": 95 * 0.5,  # 47.5 g
    "Calories": 3587 * 0.5,  # 1793.5 kcal
}

# Initialize the LP problem
prob = pulp.LpProblem("Nutrient_Adjustment_Lunch", pulp.LpMinimize)

# Define variables for each food item
food_vars = {
    food: pulp.LpVariable(f"Qty_{food}", lowBound=20, cat="Continuous")
    for food in food_df["Food"]
}

# Define deviation variables
deviation = {
    nutrient: pulp.LpVariable(f"Deviation_{nutrient}", lowBound=0, cat="Continuous")
    for nutrient in target_nutrients
}

# Objective Function: Minimize total deviation
prob += pulp.lpSum([deviation[nutrient] for nutrient in deviation]), "Total_Deviation"

# Add nutrient constraints with deviation
for nutrient in target_nutrients:
    nutrient_value = target_nutrients[nutrient]
    prob += (
        pulp.lpSum(
            [
                (row[nutrient] / 100) * food_vars[row["Food"]]
                for index, row in food_df.iterrows()
            ]
        )
        - nutrient_value
        <= deviation[nutrient],
        f"{nutrient}_Upper_Deviation",
    )
    prob += (
        nutrient_value
        - pulp.lpSum(
            [
                (row[nutrient] / 100) * food_vars[row["Food"]]
                for index, row in food_df.iterrows()
            ]
        )
        <= deviation[nutrient],
        f"{nutrient}_Lower_Deviation",
    )

# Solve the problem
prob.solve()

# Check and display results
if pulp.LpStatus[prob.status] == "Optimal":
    print("Optimal Solution Found with Minimal Deviation:")
    print(
        f"{'Food Item':<15} {'Quantity (g)':<15} {'Protein (g)':<15} {'Carbs (g)':<15} {'Fats (g)':<15} {'Calories (kcal)':<20}"
    )
    print("=" * 100)
    total_calories = 0
    totoal_protein = 0
    total_carbs = 0
    total_fats = 0
    for index, row in food_df.iterrows():
        food = row["Food"]
        qty = food_vars[food].varValue
        if qty > 0:
            protein = (row["Protein"] / 100) * qty
            carbs = (row["Carbs"] / 100) * qty
            fats = (row["Fats"] / 100) * qty
            calories = (row["Calories"] / 100) * qty
            total_calories += calories
            totoal_protein += protein
            total_carbs += carbs
            total_fats += fats
            print(
                f"{food:<15} {qty:<15.2f} {protein:<15.2f} {carbs:<15.2f} {fats:<15.2f} {calories:<20.2f}"
            )
    print("-" * 100)
    print(
        f"{'Total':<15} {'':<15} {totoal_protein:<15.2f} {total_carbs:<15.2f} {total_fats:<15.2f} {total_calories:<15.2f}"
    )
    print("\nNutrient Deviations:")
    for nutrient, dev_var in deviation.items():
        print(f"{nutrient}: {dev_var.varValue:.2f}")
else:
    print("No optimal solution found. Consider adjusting constraints or targets.")
