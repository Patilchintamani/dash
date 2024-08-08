from flask import Flask, request, send_file, jsonify, url_for
import pandas as pd
import os
import tempfile
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Initialize Flask application and CORS
app = Flask(__name__)
CORS(app)

# Use system temporary directory for uploads and cleaned files
UPLOAD_FOLDER = tempfile.gettempdir()  # System's temporary directory
CLEANED_FOLDER = tempfile.gettempdir()  # System's temporary directory

def clean_file(file_path):
    """Clean the file based on its extension and save the cleaned data."""
    print(f"Cleaning file: {file_path}")
    
    # Determine file extension and process accordingly
    if file_path.endswith('.xlsx'):
        df = pd.read_excel(file_path)
        # Example cleaning: Drop empty rows and columns
        df_cleaned = df.dropna(how='all').dropna(axis=1, how='all')
        output_file = os.path.join(CLEANED_FOLDER, os.path.basename(file_path).rsplit('.', 1)[0] + '_Cleaned.xlsx')
        print(f"Output file path for cleaned .xlsx: {output_file}")
        
        # Ensure the file is saved correctly
        with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
            df_cleaned.to_excel(writer, index=False)
            worksheet = writer.sheets['Sheet1']
            for column in df_cleaned:
                column_width = max(df_cleaned[column].astype(str).map(len).max(), len(column))
                col_idx = df_cleaned.columns.get_loc(column)
                worksheet.set_column(col_idx, col_idx, column_width)
                
    elif file_path.endswith('.csv'):
        df = pd.read_csv(file_path)
        # Example cleaning: Drop empty rows and columns
        df_cleaned = df.dropna(how='all').dropna(axis=1, how='all')
        output_file = os.path.join(CLEANED_FOLDER, os.path.basename(file_path).rsplit('.', 1)[0] + '_Cleaned.csv')
        print(f"Output file path for cleaned .csv: {output_file}")
        
        # Ensure the file is saved correctly
        df_cleaned.to_csv(output_file, index=False)
        
    else:
        raise ValueError("Unsupported file extension. Please use .xlsx or .csv")
    
    # Verify that the cleaned file exists
    if not os.path.exists(output_file):
        raise FileNotFoundError(f"Cleaned file not found: {output_file}")

    print(f"Cleaned file saved: {output_file}")
    return output_file

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file upload and cleaning."""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400
        
        # Save file to the temporary directory
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        print(f"File saved to temporary folder: {file_path}")
        
        # Clean the file
        cleaned_file_path = clean_file(file_path)
        
        # Generate download URL
        download_url = url_for('download_file', filename=os.path.basename(cleaned_file_path), _external=True)
        print(f"Cleaned file available at: {cleaned_file_path}")
        print(f"Download URL: {download_url}")
        return jsonify({"message": "File cleaned successfully", "download_url": download_url})
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        print(f"Error during file upload: {e}")
        return jsonify({"error": "An error occurred during file upload"}), 500

@app.route('/api/download/<filename>', methods=['GET'])
def download_file(filename):
    """Send the cleaned file to the user."""
    try:
        file_path = os.path.join(CLEANED_FOLDER, filename)
        print(f"Requested file path: {file_path}")
        
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return jsonify({"error": "File not found"}), 404
        
        print(f"File found: {file_path}, preparing to send file.")
        return send_file(file_path, as_attachment=True)
        
    except Exception as e:
        print(f"Error during file download: {e}")
        return jsonify({"error": f"An error occurred during file download: {e}"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
