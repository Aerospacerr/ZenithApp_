class RecommendationEngine:
    def __init__(self, df):
        self.df = df

    def calculate_differences(self, item, target_macros):
        """Calculate the absolute differences between the item's macros and the target macros."""
        differences = {
            "calories": item["macros"].get("calories", 0) - target_macros["calories"],
            "protein": item["macros"].get("protein", 0) - target_macros["protein"],
            "carbs": item["macros"].get("carbs", 0) - target_macros["carbs"],
            "fats": item["macros"].get("fats", 0) - target_macros["fats"],
        }
        return differences

    def calculate_percentages(self, differences, target_macros):
        """Calculate the percentage deviations from the target macros."""
        percentages = {
            "calories": (differences["calories"] / target_macros["calories"]) * 100,
            "protein": (differences["protein"] / target_macros["protein"]) * 100,
            "carbs": (differences["carbs"] / target_macros["carbs"]) * 100,
            "fats": (differences["fats"] / target_macros["fats"]) * 100,
        }
        return percentages

    def determine_removal_reason(self, differences, percentages, item, threshold=20):
        """Determine the reason for recommending the removal of an item based on differences and percentage deviation."""
        reason = []

        # Check calories
        if percentages["calories"] > threshold:
            reason.append(
                f"{item['name']} has {percentages['calories']:.2f}% too many calories."
            )
        elif percentages["calories"] < -threshold:
            reason.append(
                f"{item['name']} has {percentages['calories']:.2f}% too few calories."
            )
        else:
            reason.append(
                f"{item['name']} has the right amount of calories with a difference of {differences['calories']:.2f} kcal."
            )

        # Check protein
        if percentages["protein"] > threshold:
            reason.append(
                f"{item['name']} provides {percentages['protein']:.2f}% too much protein."
            )
        elif percentages["protein"] < -threshold:
            reason.append(
                f"{item['name']} provides {percentages['protein']:.2f}% too little protein."
            )
        else:
            reason.append(
                f"{item['name']} provides the right amount of protein with a difference of {differences['protein']:.2f}g."
            )

        # Check carbs
        if percentages["carbs"] > threshold:
            reason.append(
                f"{item['name']} has {percentages['carbs']:.2f}% too many carbs."
            )
        elif percentages["carbs"] < -threshold:
            reason.append(
                f"{item['name']} has {percentages['carbs']:.2f}% too few carbs."
            )
        else:
            reason.append(
                f"{item['name']} has the right amount of carbs with a difference of {differences['carbs']:.2f}g."
            )

        # Check fats
        if percentages["fats"] > threshold:
            reason.append(
                f"{item['name']} has {percentages['fats']:.2f}% too much fat."
            )
        elif percentages["fats"] < -threshold:
            reason.append(
                f"{item['name']} has {percentages['fats']:.2f}% too little fat."
            )
        else:
            reason.append(
                f"{item['name']} has the right amount of fat with a difference of {differences['fats']:.2f}g."
            )

        # Return the joined reason string
        return " ".join(reason)

    def check_item_removal(self, item, target_macros, threshold=20):
        """Check if an item should be removed based on its deviation from the target macros."""
        # Calculate the differences
        differences = self.calculate_differences(item, target_macros)

        # Calculate the percentage deviation
        percentages = self.calculate_percentages(differences, target_macros)

        # Determine the reason for removal
        removal_reason = self.determine_removal_reason(
            differences, percentages, item, threshold
        )
        return removal_reason

    def recommend_removal(self, meal_details, target_macros, threshold=20):
        """Recommend items to remove or adjust in the meal plan."""
        recommendations = []
        for item in meal_details["items"]:
            removal_reason = self.check_item_removal(item, target_macros, threshold)
            if removal_reason:
                recommendations.append({"item": item["name"], "reason": removal_reason})
        return recommendations

    def recommend_replacement(self, item, target_macros, threshold=20):
        """Recommend an alternative item from the database to replace the one being removed."""
        differences = self.calculate_differences(item, target_macros)

        # Filter the dataset to only include items that are similar in type to the one being removed
        similar_items = self.df[self.df["CATEGORY"] == item["category"]]

        best_replacement = None
        best_fit_score = float("inf")

        for _, row in similar_items.iterrows():
            row_item = {
                "name": row["FOOD ITEM"],
                "macros": {
                    "calories": row["CALORIES"],
                    "protein": row["PROTEIN"],
                    "carbs": row["NET CARBS"],
                    "fats": row["FATS"],
                },
            }
            row_differences = self.calculate_differences(row_item, target_macros)
            row_fit_score = sum(abs(v) for v in row_differences.values())

            if row_fit_score < best_fit_score:
                best_fit_score = row_fit_score
                best_replacement = row_item

        return best_replacement

    def generate_recommendations(self, meal_plan, target_macros, threshold=20):
        """Generate a list of recommendations for items to remove or replace in the meal plan."""
        recommendations = self.recommend_removal(meal_plan, target_macros, threshold)

        for meal, items in recommendations.items():
            for rec in items:
                item_to_remove = rec["item"]
                for details in meal_plan[meal]["items"]:
                    if details["name"] == item_to_remove:
                        best_replacement = self.recommend_replacement(
                            details, target_macros[meal], threshold
                        )
                        if best_replacement:
                            rec["replacement"] = best_replacement["name"]

        return recommendations
