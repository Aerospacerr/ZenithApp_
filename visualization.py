import altair as alt
import pandas as pd


def create_macros_chart(macros, meal_name):
    """Function to create a bar chart for macronutrients (excluding calories)."""
    macros_filtered = {k: v for k, v in macros.items() if k != "calories"}
    macros_df = pd.DataFrame.from_dict(
        macros_filtered, orient="index", columns=["Value"]
    )
    macros_df.reset_index(inplace=True)
    macros_df.columns = ["Macronutrient", "Value"]

    chart = (
        alt.Chart(macros_df)
        .mark_bar()
        .encode(x=alt.X("Macronutrient", sort=None), y="Value", color="Macronutrient")
        .properties(
            title=f"{meal_name} Macronutrient Breakdown",
            width=alt.Step(50),  # controls the width of bar.
        )
    )

    return chart
