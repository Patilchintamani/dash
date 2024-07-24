import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from ydata_profiling import ProfileReport

class InsightGenerator:
    def __init__(self, file_path):
        self.data = pd.read_csv(file_path)
    
    def get_summary(self):
        profile = ProfileReport(self.data, explorative=True)
        return profile.to_html()

    def plot_numeric_data(self, attribute):
        if attribute not in self.data.columns:
            raise ValueError(f"{attribute} not found in dataset.")
        if not pd.api.types.is_numeric_dtype(self.data[attribute]):
            raise TypeError(f"{attribute} is not numeric.")

        plt.figure(figsize=(10, 6))
        sns.histplot(self.data[attribute], kde=True)
        plt.title(f"Distribution of {attribute}")
        plt.xlabel(attribute)
        plt.ylabel("Frequency")
        plt.show()
    
    def plot_categorical_data(self, attribute):
        if attribute not in self.data.columns:
            raise ValueError(f"{attribute} not found in dataset.")
        if pd.api.types.is_numeric_dtype(self.data[attribute]):
            raise TypeError(f"{attribute} is numeric.")

        plt.figure(figsize=(10, 6))
        sns.countplot(y=self.data[attribute], order=self.data[attribute].value_counts().index)
        plt.title(f"Distribution of {attribute}")
        plt.xlabel("Count")
        plt.ylabel(attribute)
        plt.show()

    def generate_insights(self, attributes):
        if not all(attr in self.data.columns for attr in attributes):
            raise ValueError("One or more attributes not found in dataset.")
        
        insights = []
        for attribute in attributes:
            if pd.api.types.is_numeric_dtype(self.data[attribute]):
                desc = self.data[attribute].describe()
                insights.append(f"Summary of {attribute}:\n{desc}\n")
                self.plot_numeric_data(attribute)
            else:
                counts = self.data[attribute].value_counts()
                insights.append(f"Value counts for {attribute}:\n{counts}\n")
                self.plot_categorical_data(attribute)
        
        return "\n".join(insights)

# Usage Example:
# generator = InsightGenerator('path_to_your_file.csv')
# print(generator.get_summary())
# generator.generate_insights(['numeric_attribute', 'categorical_attribute'])
