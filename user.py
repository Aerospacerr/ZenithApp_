class User:
    def __init__(self, name, age, weight, height, activity_level):
        self.name = name
        self.age = age
        self.weight = weight  # in kg
        self.height = height  # in cm
        self.activity_level = activity_level  # e.g., sedentary, active
        self.calories = 0
        self.protein = 0
        self.carbs = 0
        self.fats = 0

    def calculate_macros(self):
        # Basal Metabolic Rate (BMR) using Mifflin-St Jeor Equation
        bmr = 10 * self.weight + 6.25 * self.height - 5 * self.age + 5
        activity_factors = {"sedentary": 1.2, "active": 1.55, "very_active": 1.75}

        self.calories = bmr * activity_factors[self.activity_level]
        self.protein = 2 * self.weight  # 0.8g per kg of body weight (adjustable)
        self.fats = 0.25 * self.calories / 9  # 25% of calories from fats
        self.carbs = (
            self.calories - (self.protein * 4 + self.fats * 9)
        ) / 4  # rest from carbs

    def display_user_info(self):
        return {
            "Name": self.name,
            "Calories": self.calories,
            "Protein": self.protein,
            "Carbs": self.carbs,
            "Fats": self.fats,
        }
