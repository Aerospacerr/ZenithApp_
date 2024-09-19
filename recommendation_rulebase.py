import pandas as pd


class RecommendationEngine:
    def __init__(self, df, target_nutrients):
        self.df = df
        self.target_nutrients = target_nutrients

    def post_genetic_algorithm_nutrient_calculation(self, meal_plan):
        """Calculate the total shortfall or excess for each macro nutrient after normalizing by the target values."""
        total_shortfall_excess = {
            "calories": 0,
            "protein": 0,
            "carbs": 0,
            "fats": 0,
        }

        for meal, details in meal_plan.items():
            total_shortfall_excess["calories"] += details.macros.calories
            total_shortfall_excess["protein"] += details.macros.protein
            total_shortfall_excess["carbs"] += details.macros.carbs
            total_shortfall_excess["fats"] += details.macros.fats

        total_shortfall_excess["calories"] = (
            100
            * (total_shortfall_excess["calories"] - self.target_nutrients["calories"])
            / self.target_nutrients["calories"]
        )

        total_shortfall_excess["protein"] = (
            100
            * (total_shortfall_excess["protein"] - self.target_nutrients["protein"])
            / self.target_nutrients["protein"]
        )

        total_shortfall_excess["carbs"] = (
            100
            * (total_shortfall_excess["carbs"] - self.target_nutrients["carbs"])
            / self.target_nutrients["carbs"]
        )

        total_shortfall_excess["fats"] = (
            100
            * (total_shortfall_excess["fats"] - self.target_nutrients["fats"])
            / self.target_nutrients["fats"]
        )

        return total_shortfall_excess

    def identify_critical_nutrient(self, total_shortfall_excess):
        """Determine which nutrient is most out of balance after normalization."""
        critical_nutrient = max(
            total_shortfall_excess, key=lambda k: abs(total_shortfall_excess[k])
        )
        return critical_nutrient

    def search_alternatives(self, food_name, nutrient_priority, top_n=5):
        """Search alternatives for a given food item within the same cluster, and then from other clusters."""
        carb_column = "NET CARBS"  # Corrected column name for carbs
        cluster_column = "Cluster_Number"  # Column to reference the cluster
        reverse_cluster_column = "Reverse_Cluster_Number"

        # Find the target food item
        target_food = self.df[self.df["FOOD ITEM"] == food_name].iloc[0]
        target_cluster = target_food[cluster_column]
        reverse_target_cluster = target_food[reverse_cluster_column]

        # Calculate similarity (based on nutrient profiles) within the same cluster
        similarities_within_cluster = []
        similarities_outside_cluster = []

        for _, row in self.df.iterrows():
            if row["FOOD ITEM"] != food_name:  # Exclude the same food item
                similarity = 0

                # Calculate similarity based on nutrient_priority
                similarity += abs(target_food["PROTEIN"] - row["PROTEIN"]) * (
                    -1 if row["PROTEIN"] > target_food["PROTEIN"] else 1
                )
                similarity += abs(target_food[carb_column] - row[carb_column]) * (
                    1 if row[carb_column] > target_food[carb_column] else -1
                )
                similarity += abs(target_food["FATS"] - row["FATS"]) * (
                    1 if row["FATS"] > target_food["FATS"] else -1
                )

                # First, group results by cluster
                # if row[cluster_column] == target_cluster:
                if row[reverse_target_cluster] == reverse_target_cluster:
                    similarities_within_cluster.append((row["FOOD ITEM"], similarity))
                else:
                    similarities_outside_cluster.append((row["FOOD ITEM"], similarity))

        # Sort similarities
        similarities_within_cluster.sort(key=lambda x: x[1], reverse=False)
        similarities_outside_cluster.sort(key=lambda x: x[1])

        # Return top N alternatives, with priority to the same cluster
        alternatives = similarities_within_cluster[
            :2
        ]  # + similarities_outside_cluster[:3]

        return alternatives[:top_n]  # Return the top N most similar food items

    def generate_recommendations(self, meal_plan, threshold=10):
        """Generate a list of recommendations for items to remove or replace in the meal plan."""
        all_recommendations = []

        # Calculate the total shortfall or excess for each nutrient
        total_shortfall_excess = self.post_genetic_algorithm_nutrient_calculation(
            meal_plan
        )

        # Identify the critical nutrient
        critical_nutrient = self.identify_critical_nutrient(total_shortfall_excess)

        for meal_name, meal_details in meal_plan.items():
            for item in meal_details.items:  # Access the items using dot notation
                if critical_nutrient in item.macros:
                    # Get food alternatives with focus on the critical nutrient
                    alternatives = self.search_alternatives(
                        food_name=item.name, nutrient_priority=critical_nutrient
                    )

                    # Add to recommendations
                    all_recommendations.append(
                        {
                            "meal": meal_name,
                            "item": item.name,
                            "issue": f"Optimize {critical_nutrient.capitalize()}",
                            "alternatives": alternatives,
                        }
                    )

        return all_recommendations
