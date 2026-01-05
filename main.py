import os
import json
from flask import Flask
from flask_login import LoginManager
from dotenv import load_dotenv
from backend.models import db, User  # Correctly pointing to backend

load_dotenv()

# 1. Update Flask to find your new frontend folder
app = Flask(__name__, 
            template_folder=os.path.join('frontend', 'templates'),
            static_folder=os.path.join('frontend', 'static'))

# --- CONFIGURATION ---
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-123')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///smartquizzer.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Setup for PDF uploads
base_dir = os.path.abspath(os.path.dirname(__file__))
app.config['UPLOAD_FOLDER'] = os.path.join(base_dir, 'uploads')
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# --- DATABASE & LOGIN INITIALIZATION ---
db.init_app(app) 

login_manager = LoginManager(app)
login_manager.login_view = 'routes.login'

# --- JINJA CUSTOM FILTERS ---
@app.template_filter('from_json')
def from_json_filter(value):
    try:
        return json.loads(value)
    except (ValueError, TypeError):
        return {}

# --- BLUEPRINT REGISTRATION ---
# 2. Changed from 'app.routes' to 'backend.routes'
from backend.routes import routes_bp
app.register_blueprint(routes_bp)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# --- DB CREATION ---
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)