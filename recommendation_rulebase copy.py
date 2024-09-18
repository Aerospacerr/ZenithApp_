import streamlit as st
from user import User


class RecommendationEngine:
    def __init__(self, df, target_nutrients):
        self.df = df
        self.target_nutrients = target_nutrients

    # #########################
    # def calculate_total_nutrients(meal_plan):
    #     total_nutrients = {
    #         "calories": 0,
    #         "protein": 0,
    #         "carbs": 0,
    #         "fats": 0,
    #     }

    #     for meal, details in meal_plan.items():
    #         total_nutrients["calories"] += details["macros"]["calories"]
    #         total_nutrients["protein"] += details["macros"]["protein"]
    #         total_nutrients["carbs"] += details["macros"]["carbs"]
    #         total_nutrients["fats"] += details["macros"]["fats"]

    #     return total_nutrients

    # def compare_nutrients(user_nutrients, meal_plan_nutrients):
    #     nutrient_status = {
    #         "calories": meal_plan_nutrients["calories"] - user_nutrients["calories"],
    #         "protein": meal_plan_nutrients["protein"] - user_nutrients["protein"],
    #         "carbs": meal_plan_nutrients["carbs"] - user_nutrients["carbs"],
    #         "fats": meal_plan_nutrients["fats"] - user_nutrients["fats"],
    #     }

    #     return nutrient_status

    # meal_plan_nutrients = calculate_total_nutrients(st.session_state.final_plan)

    # print(f"meal_plan_nutrients: {meal_plan_nutrients} \n")

    # nutrient_status = compare_nutrients(user_nutrients, meal_plan_nutrients)
    # print(f"nutrient_status: {nutrient_status} \n")

    # total_shortfall_excess = self.post_genetic_algorithm_nutrient_calculation(meal_plan)

    def post_genetic_algorithm_nutrient_calculation(self, meal_plan):
        """Calculate the total shortfall or excess for each macro nutrient after normalizing by the target values."""
        total_shortfall_excess = {
            "calories": 0,
            "protein": 0,
            "carbs": 0,
            "fats": 0,
        }

        for meal, details in meal_plan.items():
            # print(f"details calories: {details }")
            total_shortfall_excess["calories"] += details["macros"]["calories"]

            #
            total_shortfall_excess["protein"] += details["macros"]["protein"]  #
            total_shortfall_excess["carbs"] += details["macros"]["carbs"]  #
            total_shortfall_excess["fats"] += details["macros"]["fats"]  #

            print(f"food calories: {details['macros']['calories']}")
            print(f"target calorie: {self.target_nutrients['calories']}")

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

        print(f"meal: {meal}")
        print(f"total_shortfall_excess: {total_shortfall_excess}")

        return total_shortfall_excess

    def identify_critical_nutrient(self, shortfall_excess):
        """Determine which nutrient is most out of balance after normalization."""
        # Here, we're already working with normalized values, so we just need to pick the largest deviation
        critical_nutrient = max(
            shortfall_excess, key=lambda k: abs(shortfall_excess[k])
        )
        print(f"critical nutrient \n{critical_nutrient}")

        return critical_nutrient

    def content_based_filtering(self, food_name, nutrient_priority="protein", top_n=5):
        """Recommend similar food items based on nutrient profiles, prioritizing protein and reducing carbs and fats."""

        carb_column = "NET CARBS"

        target_food = self.df[self.df["FOOD ITEM"] == food_name].iloc[0]
        print(target_food)
        # Calculate similarity (based on nutrient profiles) with other foods
        similarities = []
        for _, row in self.df.iterrows():
            if row["FOOD ITEM"] != food_name:
                similarity = 0
                # Prioritize protein increase, and carbs/fats reduction
                similarity += abs(target_food["PROTEIN"] - row["PROTEIN"]) * (
                    -1 if row["PROTEIN"] > target_food["PROTEIN"] else 1
                )
                similarity += abs(target_food[carb_column] - row[carb_column]) * (
                    1 if row[carb_column] > target_food[carb_column] else -1
                )
                similarity += abs(target_food["FATS"] - row["FATS"]) * (
                    1 if row["FATS"] > target_food["FATS"] else -1
                )
                similarities.append((row["FOOD ITEM"], similarity))

        # Sort by similarity (lower values indicate more desirable)
        similarities.sort(key=lambda x: x[1])

        # Return top N similar food items
        return similarities[:top_n]

    def rule_based_recommendation_extended(
        self, meal_plan, threshold=10, nutrient_priority="protein"
    ):
        """Rule-Based Approaches: Prioritize protein, reduce carbs and fats."""
        recommendations = []

        # Extract total macros from the meal plan
        total_macros = meal_plan["macros"]

        # Analyze deviations for each item in the meal plan
        deviations = self.analyze_deviation(meal_plan["items"])

        # Check and recommend based on nutrient priority
        if total_macros["protein"] < self.target_nutrients["protein"]:
            for food_name, _ in deviations:
                high_protein_alternatives = self.content_based_filtering(
                    food_name, nutrient_priority="protein"
                )
                recommendations.append(
                    {
                        "meal": meal_plan,
                        "item": food_name,
                        "issue": "Increase Protein",
                        "alternatives": high_protein_alternatives,
                    }
                )

        # Always recommend reducing carbs and fats
        for food_name, _ in deviations:
            low_carb_fat_alternatives = self.content_based_filtering(
                food_name, nutrient_priority="carbs_fats"
            )
            recommendations.append(
                {
                    "meal": meal_plan,
                    "item": food_name,
                    "issue": "Reduce Carbs and Fats",
                    "alternatives": low_carb_fat_alternatives,
                }
            )

        return recommendations

    def analyze_deviation(self, meal_items):
        """Deviation Analysis to identify which food items contribute most to the deviations."""
        deviations = []
        try:
            for item in meal_items:
                calories_dev = abs(
                    item["macros"]["calories"] - self.target_nutrients["calories"]
                )
                protein_dev = abs(
                    item["macros"]["protein"] - self.target_nutrients["protein"]
                )
                carbs_dev = abs(
                    item["macros"]["carbs"] - self.target_nutrients["carbs"]
                )
                fats_dev = abs(item["macros"]["fats"] - self.target_nutrients["fats"])
                total_deviation = calories_dev + protein_dev + carbs_dev + fats_dev
                deviations.append((item["name"], total_deviation))
            deviations.sort(key=lambda x: x[1], reverse=True)
        except KeyError as e:
            print(f"KeyError encountered during deviation analysis: {e}")
        except Exception as e:
            print(f"An error occurred during deviation analysis: {e}")
        print(f"\n deviations\n{deviations}")

        return deviations

    def generate_recommendations(
        self, meal_plan, threshold=10, nutrient_priority="protein"
    ):
        """Generate a list of recommendations for items to remove or replace in the meal plan."""
        all_recommendations = []

        # Calculate the total shortfall or excess for each nutrient
        total_shortfall_excess = self.post_genetic_algorithm_nutrient_calculation(
            meal_plan
        )

        # Identify the critical nutrient
        critical_nutrient = self.identify_critical_nutrient(total_shortfall_excess)
        print(f"Critical nutrient identified: {critical_nutrient}")

        for meal_name, meal_details in meal_plan.items():
            recommendations = self.rule_based_recommendation_extended(
                meal_details, threshold, nutrient_priority
            )
            for rec in recommendations:
                rec["meal"] = (
                    meal_name  # Update to use meal_name instead of the full meal details
                )
            all_recommendations.extend(recommendations)

        return all_recommendations


def main():
    st.title("Meal Plan Recommendation System")

    # Initialize the recommendation engine
    rule_based_recommendation_engine = RecommendationEngine(df, target_nutrients)

    if "final_plan" not in st.session_state:
        st.write("No meal plan available.")
        return

    # Generate v2 recommendations
    recommendations_v2 = rule_based_recommendation_engine.generate_recommendations(
        meal_plan=st.session_state.final_plan, threshold=10, nutrient_priority="protein"
    )

    st.session_state.recommendations_v2 = recommendations_v2

    # Displaying the recommendations
    if recommendations_v2:
        st.write("Generated Recommendations:")

        # Create a dictionary to hold aggregated recommendations for each meal
        aggregated_recommendations = {"Breakfast": [], "Lunch": [], "Dinner": []}

        # Aggregate recommendations for each meal
        for rec in recommendations_v2:
            meal = rec["meal"]
            item = rec["item"]
            issue = rec["issue"]
            alternatives = rec["alternatives"]

            aggregated_recommendations[meal].append(
                {"item": item, "issue": issue, "alternatives": alternatives}
            )

        # Display aggregated recommendations
        for meal, recs in aggregated_recommendations.items():
            if recs:
                st.write(f"\n**Meal: {meal}**")
                for rec in recs:
                    item = rec["item"]
                    issue = rec["issue"]
                    alternatives = rec["alternatives"]
                    st.write(f"**{item}**: {issue}")

                    st.write("Consider these alternatives:")
                    for alt_food, similarity in alternatives:
                        st.write(f"- {alt_food} (Similarity score: {similarity:.2f})")
            else:
                st.write(f"\n**Meal: {meal}** - No recommendations")

    else:
        st.write("No recommendations were generated.")


if __name__ == "__main__":
    main()
