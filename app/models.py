from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
from . import db

# Note: Ensure db is imported from your __init__.py and not re-initialized here
# db = SQLAlchemy() 

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    streak_count = db.Column(db.Integer, default=0)
    last_quiz_date = db.Column(db.Date, nullable=True)
    # Streak tracking
    streak = db.Column(db.Integer, default=0)
    last_quiz_date = db.Column(db.Date, nullable=True) # Tracks the calendar day

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.Text, nullable=False)
    options_json = db.Column(db.Text, nullable=False) 
    correct_answer = db.Column(db.String(500), nullable=False) # Increased length for theory answers
    explanation = db.Column(db.Text)
    difficulty_level = db.Column(db.String(20), default="Medium")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class QuizResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    score = db.Column(db.Integer)
    total_questions = db.Column(db.Integer)
    category = db.Column(db.String(50)) # 'mcq', 'tf', 'mixed', 'theory'
    accuracy = db.Column(db.Float)      # Pre-calculated percentage for charts
    date_taken = db.Column(db.DateTime, default=datetime.utcnow)