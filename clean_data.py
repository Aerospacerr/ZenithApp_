import pandas as pd
import os
from sklearn.cluster import KMeans


class DataCleaner:
    def __init__(self, input_file, output_file, n_clusters=5):
        self.input_file = input_file
        self.output_file = output_file
        self.n_clusters = n_clusters

    def categorize_units(self, unit):
        """Categorize the units into Base Units, Count Units, etc."""
        base_units = ["G", "g", "ML", "ml"]
        count_units = [
            "SLICE",
            "MUFFIN",
            "BAGEL",
            "BAR",
            "PATTY",
            "SCOOP",
            "PIECE",
            "PCS",
            "SERVE",
        ]
        serving_units = [
            "SLICES",
            "PIECES",
            "RASHERS",
            "SERVE",
            "CAPSULES",
            "COOKIES",
            "PCS",
            "SQUARES",
        ]
        container_units = ["CUP", "TBSP", "TSP", "TEASPOON", "OZ", "CAN", "PACK", "BAG"]

        if unit in base_units:
            return "Base Units"
        elif unit in count_units:
            return "Count Units"
        elif unit in serving_units:
            return "Serving Units"
        elif unit in container_units:
            return "Container Units"
        else:
            return "Unknown"

    def clean_data(self):
        # Load the CSV file
        df = pd.read_csv(self.input_file)

        # Data cleaning operations
        df.drop(
            columns=[
                "Unnamed: 2",
                "Unnamed: 12",
                "Unnamed: 13",
                "Unnamed: 14",
                "Unnamed: 15",
                "BRAND",
            ],
            inplace=True,
        )

        # Categorize the units
        df["unit_category"] = df["UNIT"].apply(self.categorize_units)

        numeric_columns = [
            "PROTEIN",
            "NET CARBS",
            "DIETARY FIBRE",
            "TOTAL SUGARS",
            "FATS",
            "CALORIES",
        ]
        df[numeric_columns] = (
            df[numeric_columns]
            .replace(" g", "", regex=True)
            .apply(pd.to_numeric, errors="coerce")
        )

        df.dropna(subset=["FOOD ITEM", "CATEGORY"], inplace=True)

        # Fill missing values only for numeric columns with their respective medians
        for col in numeric_columns:
            df[col] = df[col].fillna(df[col].median())

        # Perform K-Means clustering on nutritional data
        kmeans = KMeans(n_clusters=self.n_clusters, random_state=42)
        df["Cluster"] = kmeans.fit_predict(df[numeric_columns])

        # Ensure the output directory exists
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)

        # Save the cleaned data to a new CSV file in the data folder
        df.to_csv(self.output_file, index=False)
        print(f"Data cleaned and saved to {self.output_file}")


if __name__ == "__main__":
    input_file = "data/Verified Food Database BACKUP 11_8_24 - FoodList.csv"  # Replace with your actual input file path
    output_file = (
        "data/cleaned_food_data_v2.csv"  # Save the cleaned data to the data/ folder
    )
    cleaner = DataCleaner(input_file, output_file, n_clusters=10)
    cleaner.clean_data()
