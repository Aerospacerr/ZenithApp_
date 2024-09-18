import pandas as pd


class UnitCategorizer:
    def __init__(self, df):
        self.df = df

    def categorize_units(self):
        # Define the categories
        base_units = ["G", "g", "ML", "ml"]
        count_units = [
            "SLICE",
            "MUFFIN",
            "BAGEL",
            "BAR",
            "DATE",
            "PIZZA",
            "BURRITO",
            "BURGER",
            "HASHBROWN",
            "WRAP",
            "BISCUIT",
            "STICK",
            "POP",
            "ICE CREAM",
            "POT",
            "SQUARE",
            "LEMON",
            "MANDARIN",
            "ORANGE",
            "APPLE",
            "PATTY",
            "SACHET",
            "SAUSAGE",
            "SCHNITZEL",
            "BOWL",
            "COOKIE",
            "PILL",
            "TABLET",
            "SCOOP",
            "OLIVES",
            "LAMINGTON",
            "CRISP",
            "LOACKER",
            "BLOCK",
            "BERRY",
            "MINT",
            "APRICOT",
            "CHIP",
            "CHOCOLATE",
            "CRACKER",
            "FRECKLES",
            "BAR",
            "LUMPS",
            "SMARTIES",
            "FINGER",
            "CONE",
            "SUB",
        ]
        serving_units = [
            "SLICES",
            "PIECES",
            "RASHERS",
            "SERVE",
            "CAPSUALS",
            "COOKIES",
            "PCS",
            "PC",
            "SQUARES",
            "BUBBLES",
        ]
        container_units = ["CUP", "TBSP", "TSP", "TEASPOON", "OZ", "CAN", "PACK", "BAG"]
        size_modifiers = ["SMALL", "MEDIUM", "LARGE", "HALF"]
        specific_product_units = [
            "G (1SLICE)",
            "G (9 BEANS)",
            "G (RAW)",
            "G (3 SLICES)",
            "G (2 BISCUITS)",
            "OZ (1 BOTTLE)",
            "G (1 TIN)",
            "G (2.5 SERVES)",
            "G (2 SERVES)",
            "G (1 WRAP)",
            "G (4 SERVES)",
            "G (1 SERVE)",
            "G (COOKED)",
            "G (5 SERVES)",
            "G (ABOUT 2 CAKES)",
            "G (1 TUB)",
            "G (X1 FILLET)",
            "G (SMALL CAN)",
            "G (BIG CAN)",
            "G (IN OLIVE OIL)",
            "G (2 PATTYS)",
            "G (1 RISSOLE)",
            "G (2 RISSOLES)",
            "G (3 RISSOLES)",
            "G (4 RISSOLES)",
            "SACHET (28G)",
            "SERVE (35ML)",
            "SCOOP (5G)",
            "G (1 SCOOP)",
            "G (2 SCOOPS)",
            "SCOOP (32G)",
            "SCOOP (1 SERVE)",
            "G SERVE",
        ]
        nutritional_supplement_units = ["MG", "MCG"]
        special_cases = [
            "NO LIMIT (1 CUP)",
            "NO LIMIT (1 STALK, MEDIUM)",
            "NO LIMIT (1 STICK/PIECE/SLICE)",
            "NO LIMIT (1 HEAD)",
            "DINOSAURS (3 SERVES)",
        ]

        # Map the units to their categories
        def map_unit_category(unit):
            if unit in base_units:
                return "Base Units"
            elif unit in count_units:
                return "Count Units"
            elif unit in serving_units:
                return "Serving Units"
            elif unit in container_units:
                return "Container Units"
            elif unit in size_modifiers:
                return "Size Modifiers"
            elif unit in specific_product_units:
                return "Specific Product Units"
            elif unit in nutritional_supplement_units:
                return "Nutritional Supplement Units"
            elif unit in special_cases:
                return "Special Cases"
            else:
                return "Unknown"

        self.df["unit_category"] = self.df["UNIT"].apply(map_unit_category)
        return self.df


if __name__ == "__main__":
    # Load the cleaned data
    df_cleaned = pd.read_csv("data/cleaned_food_data.csv")

    # Categorize the units
    categorizer = UnitCategorizer(df_cleaned)
    df_categorized = categorizer.categorize_units()

    # Save the categorized data
    df_categorized.to_csv("data/categorized_food_data.csv", index=False)
    print("Units categorized and saved to data/categorized_food_data.csv")
