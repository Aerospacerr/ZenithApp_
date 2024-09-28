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
                # Safely access the macros dictionary assuming it's a dictionary
                macros = details.get("macros", {})
                total_shortfall_excess["calories"] += macros.get("calories", 0)
                total_shortfall_excess["protein"] += macros.get("protein", 0)
                total_shortfall_excess["carbs"] += macros.get("carbs", 0)
                total_shortfall_excess["fats"] += macros.get("fats", 0)
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

    # def generate_recommendations(self, meal_plan, threshold=10):
    #     """Generate a list of recommendations for items to remove or replace in the meal plan."""
    #     all_recommendations = []

    #     logging.debug("Starting recommendation generation for meal plan")

    #     try:
    #         # Calculate the total shortfall or excess for each nutrient
    #         total_shortfall_excess = self.post_genetic_algorithm_nutrient_calculation(
    #             meal_plan
    #         )
    #         logging.debug(
    #             "Total shortfall/excess calculated: %s", total_shortfall_excess
    #         )

    #         # Identify the critical nutrient
    #         critical_nutrient = self.identify_critical_nutrient(total_shortfall_excess)
    #         logging.debug("Critical nutrient: %s", critical_nutrient)

    #         for meal_name, meal_details in meal_plan.items():
    #             for item in meal_details.items:  # Access the items using dot notation
    #                 logging.debug("Evaluating item %s in meal %s", item.name, meal_name)
    #                 if critical_nutrient in item.macros.dict():
    #                     # Get food alternatives with focus on the critical nutrient
    #                     alternatives = self.search_alternatives(
    #                         food_name=item.name, nutrient_priority=critical_nutrient
    #                     )

    #                     # Add to recommendations
    #                     all_recommendations.append(
    #                         {
    #                             "meal": meal_name,
    #                             "item": item.name,
    #                             "issue": f"Optimize {critical_nutrient.capitalize()}",
    #                             "alternatives": alternatives,
    #                         }
    #                     )
    #         logging.debug("Generated recommendations: %s", all_recommendations)

    #     except Exception as e:
    #         logging.error("Error during recommendation generation: %s", e)
    #         raise

    #     return all_recommendations

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
                for item in meal_details[
                    "items"
                ]:  # Adjust this line to access the items correctly
                    logging.debug(
                        "Evaluating item %s in meal %s", item["name"], meal_name
                    )

                    if (
                        critical_nutrient in item["macros"]
                    ):  # Adjust to access macros as a dictionary
                        # Get food alternatives with focus on the critical nutrient
                        alternatives = self.search_alternatives(
                            food_name=item["name"], nutrient_priority=critical_nutrient
                        )

                        if alternatives:
                            deviations = (
                                []
                            )  # List to store deviations for all alternatives
                            for alternative in alternatives:
                                # Calculate nutrient values for each alternative
                                recommended_nutrients = (
                                    self.calculate_nutrient_per_portion(
                                        self.df[
                                            self.df["FOOD ITEM"] == alternative[0]
                                        ].iloc[0],
                                        item["macros"][
                                            "calories"
                                        ],  # Keep the original item's calories
                                        item,
                                    )
                                )

                                # Calculate deviation from the original food
                                deviation = self.calculate_nutrient_deviation(
                                    item["macros"], recommended_nutrients
                                )
                                deviations.append(
                                    {
                                        "alternative": alternative[0],
                                        "deviation": deviation,
                                    }
                                )

                            # Add to recommendations with deviations for all alternatives
                            all_recommendations.append(
                                {
                                    "meal": meal_name,
                                    "item": item["name"],
                                    "issue": f"Optimize {critical_nutrient.capitalize()}",
                                    "alternatives": deviations,  # Add deviations for all alternatives
                                }
                            )

            logging.debug("Generated recommendations: %s", all_recommendations)

        except Exception as e:
            logging.error("Error during recommendation generation: %s", e)
            raise

        return all_recommendations

    def calculate_nutrient_per_portion(
        self, alternative, original_calories, original_food
    ):
        """
        Calculate the nutrient values for the recommended food item based on the same calorie content.
        """
        # Get the calories per 100g for the alternative
        alternative_calories_per_100g = float(alternative["CALORIES"])

        # Calculate the quantity of the alternative needed to match the original food's calories
        # (original_calories / alternative_calories_per_100g) * 100 gives us the required grams
        if alternative_calories_per_100g == 0:
            raise ValueError(
                f"Alternative food {alternative['FOOD ITEM']} has zero calories."
            )

        new_quantity = (original_calories / alternative_calories_per_100g) * 100

        # Now scale the other nutrients based on the new_quantity
        return {
            "quantity": f"{new_quantity:.2f} g",  # Adjusted quantity for the same calories
            "calories": original_calories,  # Keep the calories the same as the original food
            "protein": (float(alternative["PROTEIN"]) * new_quantity) / 100,
            "carbs": (float(alternative["NET CARBS"]) * new_quantity) / 100,
            "fats": (float(alternative["FATS"]) * new_quantity) / 100,
            "sugars": (
                (float(alternative["TOTAL SUGARS"]) * new_quantity) / 100
                if "TOTAL SUGARS" in alternative
                else 0
            ),
            "fiber": (
                (float(alternative["DIETARY FIBRE"]) * new_quantity) / 100
                if "DIETARY FIBRE" in alternative
                else 0
            ),
        }

    def calculate_nutrient_deviation(self, original_nutrients, recommended_nutrients):
        """
        Calculate the deviation between original and recommended food nutrients.
        """
        deviation = {
            "calories": recommended_nutrients["calories"]
            - original_nutrients["calories"],
            "protein": recommended_nutrients["protein"] - original_nutrients["protein"],
            "carbs": recommended_nutrients["carbs"] - original_nutrients["carbs"],
            "fats": recommended_nutrients["fats"] - original_nutrients["fats"],
            "sugars": recommended_nutrients.get("sugars", 0)
            - original_nutrients.get("sugars", 0),
            "fiber": recommended_nutrients.get("fiber", 0)
            - original_nutrients.get("fiber", 0),
        }

        return deviation
