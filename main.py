import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from dotenv import load_dotenv

# 1. Load Environment Variables
load_dotenv()
base_dir = os.path.abspath(os.path.dirname(__file__))

# 2. Initialize Flask App
app = Flask(__name__,
            template_folder =os.path.join(base_dir,'templates'), 
            static_folder = os.path.join(base_dir,'static'))

# 3. Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-123')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///smartquizzer.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(base_dir,'uploads') # Added because your routes use this

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view ='routes.login'
from app.routes import routes_bp
app.register_blueprint(routes_bp)

# Ensure upload folder exists


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