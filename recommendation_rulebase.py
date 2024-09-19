import pandas as pd
import logging


class RecommendationEngine:
    def __init__(self, df, target_nutrients):
        self.df = df
        self.target_nutrients = target_nutrients
        logging.debug(
            "Initialized RecommendationEngine with target nutrients: %s",
            target_nutrients,
        )

    def post_genetic_algorithm_nutrient_calculation(self, meal_plan):
        """Calculate the total shortfall or excess for each macro nutrient after normalizing by the target values."""
        total_shortfall_excess = {
            "calories": 0,
            "protein": 0,
            "carbs": 0,
            "fats": 0,
        }

        for meal, details in meal_plan.items():
            try:
                total_shortfall_excess["calories"] += details.macros.calories
                total_shortfall_excess["protein"] += details.macros.protein
                total_shortfall_excess["carbs"] += details.macros.carbs
                total_shortfall_excess["fats"] += details.macros.fats
            except AttributeError as e:
                logging.error("Meal plan structure invalid: %s", e)
                raise ValueError("Invalid meal plan structure") from e

        logging.debug(
            "Total shortfall/excess before normalization: %s", total_shortfall_excess
        )

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

        logging.debug(
            "Total shortfall/excess after normalization: %s", total_shortfall_excess
        )

        return total_shortfall_excess

    def identify_critical_nutrient(self, total_shortfall_excess):
        """Determine which nutrient is most out of balance after normalization."""
        critical_nutrient = max(
            total_shortfall_excess, key=lambda k: abs(total_shortfall_excess[k])
        )
        logging.debug("Identified critical nutrient: %s", critical_nutrient)
        return critical_nutrient

    def search_alternatives(self, food_name, nutrient_priority, top_n=5):
        """Search alternatives for a given food item within the same cluster, and then from other clusters."""
        logging.debug("Searching alternatives for food item: %s", food_name)

        carb_column = "NET CARBS"
        cluster_column = "Cluster_Number"
        reverse_cluster_column = "Reverse_Cluster_Number"

        # Find the target food item
        target_food = self.df[self.df["FOOD ITEM"] == food_name].iloc[0]
        target_cluster = target_food[cluster_column]
        reverse_target_cluster = target_food[reverse_cluster_column]

        similarities_within_cluster = []
        similarities_outside_cluster = []

        for _, row in self.df.iterrows():
            if row["FOOD ITEM"] != food_name:
                similarity = 0
                similarity += abs(target_food["PROTEIN"] - row["PROTEIN"]) * (
                    -1 if row["PROTEIN"] > target_food["PROTEIN"] else 1
                )
                similarity += abs(target_food[carb_column] - row[carb_column]) * (
                    1 if row[carb_column] > target_food[carb_column] else -1
                )

                similarity += abs(target_food["FATS"] - row["FATS"]) * (
                    1 if row["FATS"] > target_food["FATS"] else -1
                )

                if row[reverse_cluster_column] == reverse_target_cluster:
                    similarities_within_cluster.append((row["FOOD ITEM"], similarity))
                else:
                    similarities_outside_cluster.append((row["FOOD ITEM"], similarity))

        logging.debug(
            "Found %s alternatives within the same cluster",
            len(similarities_within_cluster),
        )
        logging.debug(
            "Found %s alternatives outside the cluster",
            len(similarities_outside_cluster),
        )

        # Sort similarities
        similarities_within_cluster.sort(key=lambda x: x[1], reverse=False)
        similarities_outside_cluster.sort(key=lambda x: x[1])

        # Return top N alternatives, with priority to the same cluster
        alternatives = (
            similarities_within_cluster[:2] + similarities_outside_cluster[:3]
        )
        logging.debug("Returning top %s alternatives for %s", top_n, food_name)

        return alternatives[:top_n]

    def generate_recommendations(self, meal_plan, threshold=10):
        """Generate a list of recommendations for items to remove or replace in the meal plan."""
        all_recommendations = []

        logging.debug("Starting recommendation generation for meal plan")

        try:
            # Calculate the total shortfall or excess for each nutrient
            total_shortfall_excess = self.post_genetic_algorithm_nutrient_calculation(
                meal_plan
            )
            logging.debug(
                "Total shortfall/excess calculated: %s", total_shortfall_excess
            )

            # Identify the critical nutrient
            critical_nutrient = self.identify_critical_nutrient(total_shortfall_excess)
            logging.debug("Critical nutrient: %s", critical_nutrient)

            for meal_name, meal_details in meal_plan.items():
                for item in meal_details.items:  # Access the items using dot notation
                    logging.debug("Evaluating item %s in meal %s", item.name, meal_name)
                    if critical_nutrient in item.macros.dict():
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
            logging.debug("Generated recommendations: %s", all_recommendations)

        except Exception as e:
            logging.error("Error during recommendation generation: %s", e)
            raise

        return all_recommendations
