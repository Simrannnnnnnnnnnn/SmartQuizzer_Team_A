import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from dotenv import load_dotenv

# 1. Load Environment Variables
load_dotenv()

# 2. Initialize Flask App
app = Flask(__name__)

# 3. Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-123')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///smartquizzer.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 4. Initialize Extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login' 

# 5. Import Routes from the 'app' folder
# This matches your structure: app/routes.py
from app import routes

# 6. Database Table Creation
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)