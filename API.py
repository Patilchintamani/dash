from flask import Flask, jsonify, request, redirect
import pymongo
import bcrypt
from flask_cors import CORS
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
import os
import logging
from werkzeug.security import generate_password_hash
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
#####
import io
import base64
import matplotlib
matplotlib.use('Agg')  # Use the 'Agg' backend for non-interactive plotting
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd



app = Flask(__name__)
CORS(app)

# Global variable to store data
data = None


# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'pravindpatil22112000')
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', 'mtesting488@gmail.com')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', 'axxb wowq cboc fiog')
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

# MongoDB Configuration
mongo_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
client = MongoClient(mongo_uri)

try:
    db = client['user_database']
    users_collection = db['users']
    # Check if the connection is successful
    client.admin.command('ping')
    print("MongoDB connection successful.")
except ConnectionFailure as e:
    print(f"Error connecting to MongoDB: {e}")
    db = None
    users_collection = None

mail = Mail(app)
s = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# Setting up logging
logging.basicConfig(level=logging.DEBUG)

@app.route('/')
def home():
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        user = users_collection.find_one({"username": username})
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
            return jsonify({"message": "Login successful!"}), 200
        else:
            return jsonify({"message": "Login failed. Please check your credentials and try again."}), 401
    else:
        return jsonify({"message": "Invalid method"}), 401

@app.route('/signup', methods=['POST'])
def signup():
    if request.method == 'POST':
        data = request.json
        username = data.get('username')
        email = data.get('email')
        mobileno = data.get('mobileno')
        password = data.get('password')
        
        if not username or not email or not mobileno or not password:
            return jsonify({"message": "All fields are required."}), 400
        
        existing_user = users_collection.find_one({"username": username})
        if existing_user:
            return jsonify({"message": "Username already exists. Please choose a different username."}), 400
        else:
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            new_user = {
                "username": username,
                "password": hashed_password,
                "mobNumber": mobileno,
                "email": email,
            }
            result = users_collection.insert_one(new_user)
            return jsonify({"message": "Signup successful!"}), 201

@app.route('/forget', methods=['GET', 'POST'])
def forget():
    if request.method == 'POST':
        try:
            data = request.get_json()
            email = data.get('email')
            if not email:
                return jsonify({"message": "Email is required", "status": "error"}), 400
            logging.debug(f"Password reset requested for email: {email}")
            
            token = s.dumps(email, salt='email-confirm')
            link = f'http://localhost:3000/src/screens/ResetPasswordCard.js?token={token}'
            
            msg = Message('Password Reset Request', sender=app.config['MAIL_USERNAME'], recipients=[email])
            msg.body = f'Your link to reset the password is {link}'
            mail.send(msg)
            logging.debug("Email sent successfully")
            return jsonify({"message": "The email has been sent!", "status": "success"})
        except Exception as e:
            logging.error(f"Error sending email: {e}")
            return jsonify({"message": "There was an error sending the email. Please try again later.", "status": "error"}), 500
    return jsonify({"message": "Forget password form", "status": "info"})

@app.route('/reset_password/<token>', methods=['POST'])
def reset_password(token):
    if request.method == 'POST':
        try:
            email = s.loads(token, salt='email-confirm', max_age=3600)
            logging.debug(f"Token valid for email: {email}")
            
            data = request.get_json()
            new_password = data.get('password')
            if not new_password:
                return jsonify({"message": "Password is required", "status": "error"}), 400
            
            hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256')
            logging.debug(f"Password hashed successfully for email: {email}")
            
            update_result = users_collection.update_one(
                {"email": email},
                {"$set": {"password": hashed_password}}
            )
            if update_result.modified_count == 1:
                logging.debug("Password updated successfully")
                return jsonify({"message": "Your password has been updated!", "status": "success"})
            else:
                user_exists = users_collection.find_one({"email": email})
                if not user_exists:
                    logging.error(f"User with email {email} does not exist")
                    return jsonify({"message": "User not found. Please try again.", "status": "error"}), 404
                else:
                    logging.error("Error updating the password in the database")
                    return jsonify({"message": "Error updating your password!", "status": "error"}), 500
        except SignatureExpired:
            logging.warning("Token expired")
            return jsonify({"message": "The token is expired!", "status": "error"}), 400
        except Exception as e:
            logging.error(f"Exception during password reset: {e}")
            return jsonify({"message": "Error during password reset!", "status": "error"}), 500
    return jsonify({"message": "Reset password form", "status": "info"})

@app.route('/change_password', methods=['POST'])
def change_password():
    try:
        data = request.get_json()
        email = data.get('email')
        current_password = data.get('current_password').encode('utf-8')
        new_password = data.get('new_password').encode('utf-8')

        user = users_collection.find_one({'email': email})
        if user:
            if bcrypt.checkpw(current_password, user['password']):
                hashed_new_password = bcrypt.hashpw(new_password, bcrypt.gensalt())
                result = users_collection.update_one(
                    {'email': email},
                    {'$set': {'password': hashed_new_password}}
                )
                if result.modified_count == 1:
                    return jsonify({'message': 'Password updated successfully.'}), 200
                else:
                    return jsonify({'error': 'Failed to update password.'}), 500
            else:
                return jsonify({'error': 'Current password is incorrect.'}), 400
        else:
            return jsonify({'error': 'User not found.'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_user', methods=['GET'])
def get_user():
    if db is None or users_collection is None:
        return jsonify({"error": "Database connection error"}), 500

    username = request.args.get('username')
    print(f"Username: {username}")
    
    # Check if username is provided
    if not username:
        return jsonify({"error": "Username is required"}), 400

    # Build query based on username
    query = {'username': username}

    # Find the user based on the query
    user = users_collection.find_one(query, projection={'email': 1, 'mobNumber': 1, '_id': 0})
    
    if user:
        return jsonify(user), 200
    else:
        return jsonify({"error": "User not found"}), 404

@app.route('/update_contact_info', methods=['POST'])
def update_contact_info():
    data = request.get_json()
    username = data.get('username')
    new_email = data.get('email')
    new_mobile_number = data.get('mobNumber')  # Changed from 'mobile_number' to 'mobNumber'
    
    if not username or not new_email or not new_mobile_number:
        return jsonify({"error": "Missing data"}), 400
    
    # Find the user by username
    user = users_collection.find_one({'username': username})
    if not user:
        return jsonify({"error": "Username not found"}), 404
    
    current_email = user.get('email')
    current_mobile_number = user.get('mobNumber')  # Changed from 'mobile_number' to 'mobNumber'
    
    # Check if the new data is different from the current data
    if (current_email == new_email and current_mobile_number == new_mobile_number):
        return jsonify({"message": "No changes to update"}), 400
    
    # Update the user's email and mobile number
    result = users_collection.update_one(
        {'username': username},
        {'$set': {'email': new_email, 'mobNumber': new_mobile_number}}  # Changed from 'mobile_number' to 'mobNumber'
    )
    
    if result.modified_count == 0:
        return jsonify({"error": "No changes made"}), 400
    
    return jsonify({"message": "Contact information updated successfully"}), 200
    ################################## Visualization Model ##################################


@app.route('/upload', methods=['POST'])
def upload_file():
    global data
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file and (file.filename.endswith('.csv') or file.filename.endswith('.xlsx')):
        try:
            if file.filename.endswith('.csv'):
                data = pd.read_csv(file, on_bad_lines='skip')
            elif file.filename.endswith('.xlsx'):
                data = pd.read_excel(file, engine='openpyxl')
            
            data.columns = data.columns.str.strip()
            columns = data.columns.tolist()
            preview = data.head().to_dict(orient='records')
            
            return jsonify({"message": "File uploaded successfully", "columns": columns, "preview": preview})
        except (pd.errors.ParserError, ValueError) as e:
            return jsonify({"error": f"Error parsing file: {str(e)}"}), 400
    else:
        return jsonify({"error": "Invalid file type. Please upload a CSV or Excel file."}), 400

@app.route('/attributes', methods=['GET'])
def attributes():
    global data
    if data is None:
        return jsonify({"error": "No data available. Please upload a dataset first."}), 400
    
    columns = data.columns.tolist()
    return jsonify({"columns": columns})

@app.route('/analyze', methods=['POST'])
def analyze():
    global data
    if data is None:
        return jsonify({"error": "No data available. Please upload a dataset first."}), 400
    
    selected_attributes = request.json.get('attributes')
    
    if not selected_attributes:
        return jsonify({"error": "No attributes selected."}), 400
    
    insights = []
    plots = []
    explanations = []

    for attribute in selected_attributes:
        if attribute not in data.columns:
            return jsonify({"error": f"Attribute '{attribute}' not found in the dataset."}), 400

        if pd.api.types.is_numeric_dtype(data[attribute]):
            # Generate numeric insights and plots
            desc = data[attribute].describe().to_dict()
            insights.append({"attribute": attribute, "summary": desc})
            
            # Histogram
            plt.figure(figsize=(10, 6))
            sns.histplot(data[attribute], kde=True)
            plt.title(f'Distribution of {attribute}')
            plt.xlabel(attribute)
            plt.ylabel('Frequency')
            img = io.BytesIO()
            plt.savefig(img, format='png')
            img.seek(0)
            img_base64 = base64.b64encode(img.getvalue()).decode('utf-8')
            image_url = (f'data:image/png;base64,{img_base64}')
            plt.close()
            plots.append({"attribute": attribute, "plot_type": "histogram", "image": image_url})
            
            # Line Chart (if applicable)
            if pd.api.types.is_datetime64_any_dtype(data[attribute]):
                plt.figure(figsize=(10, 6))
                data.set_index(attribute).plot(figsize=(10, 6))
                plt.title(f'Time Series of {attribute}')
                plt.xlabel('Date')
                plt.ylabel(attribute)
                img = io.BytesIO()
                plt.savefig(img, format='png')
                img.seek(0)
                img_base64 = base64.b64encode(img.getvalue()).decode('utf-8')
                image_url = (f'data:image/png;base64,{img_base64}')
                plt.close()
                plots.append({"attribute": attribute, "plot_type": "time_series", "image": image_url})
            
            # Explanation
            explanation = generate_numeric_explanation(attribute, data[attribute])
            explanations.append({"attribute": attribute, "explanation": explanation})
        
        else:
            # Generate categorical insights and plots
            counts = data[attribute].value_counts().to_dict()
            insights.append({"attribute": attribute, "counts": counts})
            
            # Bar Chart
            plt.figure(figsize=(10, 6))
            sns.countplot(data=data, x=attribute)
            plt.title(f'Counts of {attribute}')
            plt.xlabel(attribute)
            plt.ylabel('Count')
            img = io.BytesIO()
            plt.savefig(img, format='png')
            img.seek(0)
            img_base64 = base64.b64encode(img.getvalue()).decode('utf-8')
            image_url = (f'data:image/png;base64,{img_base64}')
            plt.close()
            plots.append({"attribute": attribute, "plot_type": "bar_chart", "image": image_url})

            # Pie Chart
            plt.figure(figsize=(10, 6))
            data[attribute].value_counts().plot.pie(autopct='%1.1f%%')
            plt.title(f'Proportions of {attribute}')
            plt.ylabel('')
            img = io.BytesIO()
            plt.savefig(img, format='png')
            img.seek(0)
            img_base64 = base64.b64encode(img.getvalue()).decode('utf-8')
            image_url = (f'data:image/png;base64,{img_base64}')
            plt.close()
            plots.append({"attribute": attribute, "plot_type": "pie_chart", "image": image_url})
            
            # Explanation
            explanation = generate_categorical_explanation(attribute, data[attribute])
            explanations.append({"attribute": attribute, "explanation": explanation})

    return jsonify({"insights": insights, "plots": plots, "explanations": explanations})

def generate_numeric_explanation(attribute, series):
    """Generate explanation for numeric attribute"""
    mean = series.mean()
    median = series.median()
    std = series.std()
    return f'The average value of {attribute} is {mean:.2f}. The median value is {median:.2f}, which is the midpoint of the data. The standard deviation is {std:.2f}, indicating the spread of the data around the mean.'

def generate_categorical_explanation(attribute, series):
    """Generate explanation for categorical attribute"""
    num_unique = series.nunique()
    return f'{attribute} has {num_unique} unique categories. The distribution shows how frequently each category occurs.'
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
