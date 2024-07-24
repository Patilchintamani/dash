from flask import Flask, request, render_template_string
import pandas as pd
import io
import base64
import matplotlib
matplotlib.use('Agg')  # Use the 'Agg' backend for non-interactive plotting
import matplotlib.pyplot as plt
import seaborn as sns

app = Flask(__name__)

# Global variable to store data
data = None

@app.route('/')
def index():
    return '''
    <html>
    <head><title>Upload Your Dataset</title></head>
    <body>
        <h1>Upload Your Business Dataset</h1>
        <form action="/upload" method="post" enctype="multipart/form-data">
            <input type="file" name="file" accept=".csv, .xlsx">
            <input type="submit" value="Upload">
        </form>
    </body>
    </html>
    '''

@app.route('/upload', methods=['POST'])
def upload_file():
    global data
    if 'file' not in request.files:
        return "No file uploaded", 400
    
    file = request.files['file']
    
    if file.filename == '':
        return "No selected file", 400
    
    if file and (file.filename.endswith('.csv') or file.filename.endswith('.xlsx')):
        try:
            # Determine file type and read the file into a DataFrame
            if file.filename.endswith('.csv'):
                data = pd.read_csv(file, on_bad_lines='skip')
            elif file.filename.endswith('.xlsx'):
                data = pd.read_excel(file, engine='openpyxl')
            
            # Strip any leading/trailing whitespace from column names
            data.columns = data.columns.str.strip()
            
            # Get column names for attribute selection
            columns = data.columns.tolist()
            
            # Render attribute selection page
            html = f'''
            <html>
            <head><title>Select Attributes</title></head>
            <body>
                <h1>Select Attributes for Analysis</h1>
                <form action="/analyze" method="post">
                    {''.join([f'<input type="checkbox" name="attributes" value="{col}"> {col}<br>' for col in columns])}
                    <input type="submit" value="Analyze">
                </form>
            </body>
            </html>
            '''
            return render_template_string(html)
        except (pd.errors.ParserError, ValueError) as e:
            return f"Error parsing file: {str(e)}", 400
    else:
        return "Invalid file type. Please upload a CSV or Excel file.", 400

@app.route('/analyze', methods=['POST'])
def analyze():
    global data
    if data is None:
        return "No data available. Please upload a dataset first.", 400
    
    selected_attributes = request.form.getlist('attributes')
    
    if not selected_attributes:
        return "No attributes selected.", 400
    
    insights = []
    plots = []
    explanations = []

    for attribute in selected_attributes:
        if attribute not in data.columns:
            return f"Attribute '{attribute}' not found in the dataset.", 400

        if pd.api.types.is_numeric_dtype(data[attribute]):
            desc = data[attribute].describe()
            insights.append(f"<h3>Summary of {attribute}</h3>{desc.to_frame().to_html()}")
            
            plt.figure(figsize=(10, 6))
            sns.histplot(data[attribute], kde=True)
            plt.title(f'Distribution of {attribute}')
            plt.xlabel(attribute)
            plt.ylabel('Frequency')
            img = io.BytesIO()
            plt.savefig(img, format='png')
            img.seek(0)
            img_base64 = base64.b64encode(img.getvalue()).decode()
            plt.close()
            plots.append(f'<img src="data:image/png;base64,{img_base64}" alt="{attribute} distribution"/>')
            
            # Generate explanation
            explanation = generate_numeric_explanation(attribute, data[attribute])
            explanations.append(explanation)
        
        else:
            counts = data[attribute].value_counts()
            insights.append(f"<h3>Value Counts for {attribute}</h3>{counts.to_frame().to_html()}")
            
            plt.figure(figsize=(10, 6))
            sns.countplot(y=data[attribute], order=data[attribute].value_counts().index)
            plt.title(f'Distribution of {attribute}')
            plt.xlabel('Count')
            plt.ylabel(attribute)
            img = io.BytesIO()
            plt.savefig(img, format='png')
            img.seek(0)
            img_base64 = base64.b64encode(img.getvalue()).decode()
            plt.close()
            plots.append(f'<img src="data:image/png;base64,{img_base64}" alt="{attribute} distribution"/>')
            
            # Generate explanation
            explanation = generate_categorical_explanation(attribute, counts)
            explanations.append(explanation)
    
    html = f'''
    <html>
    <head><title>Analysis Results</title></head>
    <body>
        <h1>Analysis Results</h1>
        {"".join(insights)}
        <h2>Visualizations</h2>
        {"".join(plots)}
        <h2>Explanations</h2>
        {"".join(explanations)}
        <br><br>
        <a href="/">Upload another file</a>
    </body>
    </html>
    '''
    return render_template_string(html)

def generate_numeric_explanation(attribute, data):
    explanation = f"<h3>What we learned about {attribute}</h3>"
    explanation += f"The average value of <b>{attribute}</b> is {data.mean():.2f}, which is typical for this attribute. "
    explanation += f"The values range from {data.min()} to {data.max()}. "
    explanation += f"Most of the data points are around {data.median():.2f}, indicating a typical value for this attribute. "
    explanation += f"From the histogram, you can see how the values are distributed. "
    if data.std() > data.mean() / 2:
        explanation += f"There is a lot of variability in the data, meaning the values are spread out. "
    else:
        explanation += f"The data is relatively consistent, with values close to the average. "
    return explanation

def generate_categorical_explanation(attribute, counts):
    explanation = f"<h3>What we learned about {attribute}</h3>"
    explanation += f"The most common value is <b>{counts.idxmax()}</b> with {counts.max()} occurrences. "
    explanation += f"There are {counts.count()} unique values, indicating diversity in this attribute. "
    explanation += f"From the count plot, you can see how frequently each value appears. "
    explanation += f"This helps in understanding the popularity of different categories. "
    return explanation

if __name__ == '__main__':
    app.run(debug=True)
