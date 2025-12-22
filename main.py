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
app.config['UPLOAD_FOLDER'] = 'uploads' # Added because your routes use this

# Ensure upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# 4. Initialize Extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'routes.login' # Updated to match blueprint name

# 5. IMPORT AND REGISTER BLUEPRINT
# We import routes_bp from the app folder
from app.routes import routes_bp
app.register_blueprint(routes_bp)

# 6. User Loader (Required for Flask-Login)
from app.models import User
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 7. Database Table Creation
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)