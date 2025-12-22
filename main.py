import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from dotenv import load_dotenv

# 1. Load Environment Variables
load_dotenv()

# 2. Initialize Flask App (Named 'app' for Gunicorn)
app = Flask(__name__)

# 3. Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-123')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///smartquizzer.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 4. Initialize Extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'routes.login' # Adjusted to use blueprint if you have one

# 5. Database Table Creation
with app.app_context():
    # Note: If your models are in a separate file, import them here
    # from models import User 
    db.create_all()

# 6. Import Routes
# These must be on their own lines
from routes import *

if __name__ == '__main__':
    app.run(debug=True)