from insight_generator import InsightGenerator

# Path to your dataset
file_path = 'C:\pymodule\sample1.csv'

try:
    # Initialize the InsightGenerator with your dataset
    generator = InsightGenerator(file_path)
    print("InsightGenerator initialized successfully.")
except Exception as e:
    print(f"Error initializing InsightGenerator: {e}")
    exit()

try:
    # Generate and print the summary report
    summary = generator.get_summary()
    with open('summary_report.html', 'w') as f:
        f.write(summary)
    print("Summary report has been generated and saved as 'summary_report.html'.")
except Exception as e:
    print(f"Error generating summary report: {e}")

# Define the attributes you want to analyze
attributes = ['numeric_attribute1', 'categorical_attribute1']  # Replace with actual column names

try:
    # Generate and print insights for specific attributes
    insights = generator.generate_insights(attributes)
    print("Insights generated successfully.")
    print("Insights:")
    print(insights)
except Exception as e:
    print(f"Error generating insights: {e}")
