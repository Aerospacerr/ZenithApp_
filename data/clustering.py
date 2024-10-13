import itertools
import pandas as pd

# Load your dataset
data = pd.read_csv(
    "/Users/emircan/Desktop/Case_Study/Upwork/Upwork/ZenithApp/data/cleaned_food_data.csv"
)

# Define the levels for Protein, Carbs, and Fats using quantiles
protein_quintiles = data["PROTEIN"].quantile([0.2, 0.4, 0.6, 0.8])
carbs_quintiles = data["NET CARBS"].quantile([0.2, 0.4, 0.6, 0.8])
fats_quintiles = data["FATS"].quantile([0.2, 0.4, 0.6, 0.8])


# Function to assign levels based on quintiles
def assign_level(value, quintiles):
    if value <= quintiles.iloc[0]:
        return "Very Low"
    elif value <= quintiles.iloc[1]:
        return "Low"
    elif value <= quintiles.iloc[2]:
        return "Medium"
    elif value <= quintiles.iloc[3]:
        return "High"
    else:
        return "Very High"


# Apply the level assignment for protein, carbs, and fats
data["Protein_Level"] = data["PROTEIN"].apply(assign_level, quintiles=protein_quintiles)
data["Carbs_Level"] = data["NET CARBS"].apply(assign_level, quintiles=carbs_quintiles)
data["Fats_Level"] = data["FATS"].apply(assign_level, quintiles=fats_quintiles)

# Now that we have the levels, combine them into 'Refined_Cluster_Description'
data["Refined_Cluster_Description"] = (
    data["Protein_Level"] + ", " + data["Carbs_Level"] + ", " + data["Fats_Level"]
)

# Define the levels
levels = ["Very Low", "Low", "Medium", "High", "Very High"]

# Generate all possible combinations for Protein, Carbs, and Fats
combinations = list(itertools.product(levels, levels, levels))


# Function to reverse each combination
def reverse_combination(combination):
    reverse_map = {
        "Very Low": "Very High",
        "Low": "High",
        "Medium": "Medium",
        "High": "Low",
        "Very High": "Very Low",
    }
    return tuple(reverse_map[level] for level in combination)


# Create reverse combinations
reverse_combinations = [reverse_combination(combo) for combo in combinations]

# Create a DataFrame for the combinations and reverse combinations
comb_df = pd.DataFrame(
    {
        "Cluster_Description": ["{}, {}, {}".format(*combo) for combo in combinations],
        "Reverse_Cluster": [
            "{}, {}, {}".format(*combo) for combo in reverse_combinations
        ],
    }
)

# Assign cluster numbers and reverse cluster numbers
comb_df["Cluster_Number"] = range(len(comb_df))
comb_df["Reverse_Cluster_Number"] = comb_df["Reverse_Cluster"].map(
    dict(zip(comb_df["Cluster_Description"], comb_df["Cluster_Number"]))
)

# Map the cluster numbers and reverse cluster numbers to the main dataset
data["Cluster_Number"] = data["Refined_Cluster_Description"].map(
    dict(zip(comb_df["Cluster_Description"], comb_df["Cluster_Number"]))
)
data["Reverse_Cluster_Number"] = data["Refined_Cluster_Description"].map(
    dict(zip(comb_df["Cluster_Description"], comb_df["Reverse_Cluster_Number"]))
)

# Save the updated dataset with cluster numbers and reverse cluster numbers
data.to_csv("updated_food_data_with_complete_clusters.csv", index=False)
