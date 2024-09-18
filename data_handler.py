import os
import pandas as pd
import streamlit as st


# DataHandler class with added error handling for missing files
class DataHandler:
    def __init__(self, file_path):
        self.file_path = file_path
        self.df_cleaned = None

    def load_data(self):
        """Load the cleaned CSV file from the specified path."""
        if not os.path.exists(self.file_path):
            st.error(f"File not found: {self.file_path}. Please check the file path.")
            st.stop()

        try:
            self.df_cleaned = pd.read_csv(self.file_path)
        except Exception as e:
            st.error(f"Error loading data: {e}")
            st.stop()

    def get_data(self):
        """Return the loaded DataFrame."""
        if self.df_cleaned is None:
            raise ValueError(
                "Data not loaded. Call load_data() before accessing the data."
            )
        return self.df_cleaned
