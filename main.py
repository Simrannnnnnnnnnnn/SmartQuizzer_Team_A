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
# SECRET_KEY is needed for sessions/logins
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-me')
# SQLite database path
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///smartquizzer.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 4. Initialize Extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# 5. Database Table Creation (Automatic for Render)
# This creates the .db file if it doesn't exist on the server
with app.app_context():
    # from models import User, Quiz  # Import your models here if they are in another file
    db.create_all()

# 6. Import Routes
# IMPORTANT: Put this at the bottom to avoid "circular imports"
# Ensure your routes.py uses @app.route
from routes import * if __name__ == '__main__':
    # Local development run
    app.run(debug=True)