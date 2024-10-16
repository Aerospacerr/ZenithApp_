class User:
    def __init__(self, name, age, weight, height, activity_level, goal, gender):
        self.name = name
        self.age = age
        self.weight = weight  # in kg
        self.height = height  # in cm
        self.activity_level = activity_level.lower()  # e.g., sedentary, active
        self.goal = goal.lower()  # e.g., maintain, weight loss, fast weight gain
        self.gender = gender.lower()  # e.g., male, female
        self.calories = 0
        self.protein = 0
        self.carbs = 0
        self.fats = 0

    def calculate_macros(self):
        # Step 1: Basal Metabolic Rate (BMR) using Mifflin-St Jeor Equation
        if self.gender == "male":
            bmr = 10 * self.weight + 6.25 * self.height - 5 * self.age + 5
        elif self.gender == "female":
            bmr = 10 * self.weight + 6.25 * self.height - 5 * self.age - 161
        else:
            raise ValueError("Gender must be either 'male' or 'female'.")

        # Step 2: Total Calories based on activity level
        activity_factors = {
            "sedentary": 1.2,
            "light": 1.375,
            "moderate": 1.55,
            "active": 1.725,
            "very active": 1.9,
        }
        if self.activity_level not in activity_factors:
            raise ValueError(
                "Activity level must be one of: 'sedentary', 'light', 'moderate', 'active', 'very active'."
            )
        total_calories = bmr * activity_factors[self.activity_level]

        # Step 3: Adjust Calories As per Goal
        if self.goal == "maintain weight":
            adjusted_calories = total_calories
        elif self.goal == "weight loss":
            adjusted_calories = total_calories - 500
        elif self.goal == "fast weight loss":
            adjusted_calories = total_calories - 1000
        elif self.goal == "weight gain":
            adjusted_calories = total_calories + 500
        elif self.goal == "fast weight gain":
            adjusted_calories = total_calories + 1000
        else:
            raise ValueError(
                "Goal must be one of: 'maintain weight', 'weight loss', 'fast weight loss', 'weight gain', 'fast weight gain'."
            )

        self.calories = adjusted_calories

        # Step 4: Calculate Macronutrients
        # Protein: 2g per kg of body weight
        self.protein = 2 * self.weight  # in grams
        protein_calories = self.protein * 4

        # Fats Calculation
        if self.activity_level in ["sedentary", "light", "moderate"]:
            fats_calories = 0.15 * self.calories
        elif self.activity_level in ["active", "very active"]:
            fats_calories = (
                0.2 * self.calories if self.calories > 2500 else 0.15 * self.calories
            )
        self.fats = fats_calories / 9  # Convert to grams

        # Carbs Calculation
        carbs_calories = self.calories - protein_calories - fats_calories
        self.carbs = carbs_calories / 4  # Convert to grams

    def display_user_info(self):
        return {
            "Name": self.name,
            "Calories": round(self.calories, 2),
            "Protein (g)": round(self.protein, 2),
            "Carbs (g)": round(self.carbs, 2),
            "Fats (g)": round(self.fats, 2),
        }
