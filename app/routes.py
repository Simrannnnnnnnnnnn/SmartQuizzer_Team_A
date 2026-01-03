import json, os, pypdf, io
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app, send_file
from flask_login import login_user, logout_user, login_required, current_user
from .models import User, Question, QuizResult, db
from app.llm_client import LLMClient
from dotenv import load_dotenv
from datetime import datetime, date, timedelta
from sqlalchemy import or_
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

load_dotenv()
routes_bp = Blueprint('routes', __name__)

API_KEY = os.getenv("GROQ_API_KEY")
llm = LLMClient(api_key=API_KEY)

@routes_bp.route('/')
def index():
    return render_template('landing.html')

@routes_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        if User.query.filter((User.email == email) | (User.username == username)).first():
            flash("User with this email or username already exists!", "danger")
            return redirect(url_for('routes.signup'))
        new_user = User(email=email, username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash("Account created! Please login.", "success")
        return redirect(url_for('routes.login'))
    return render_template('signup.html')

@routes_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('routes.dashboard'))
    if request.method == 'POST':
        login_id = request.form.get('login_id') 
        password = request.form.get('password')
        user = User.query.filter(or_(User.email == login_id, User.username == login_id)).first()
        if user and user.check_password(password):
            login_user(user)
            flash(f"Welcome back, {user.username}! ✨ Ready for a challenge?", "success")
            return redirect(url_for('routes.dashboard'))
        flash("Invalid credentials. Please try again.", "danger")
    return render_template('login.html')

@routes_bp.route('/dashboard')
@login_required
def dashboard():
    results = QuizResult.query.filter_by(user_id=current_user.id).order_by(QuizResult.date_taken.desc()).all()
    correct_total = sum([r.score for r in results]) if results else 0
    total_q = sum([r.total_questions for r in results]) if results else 0
    return render_template('dashboard.html', 
                           correct_total=correct_total, 
                           incorrect_total=total_q - correct_total,
                           results=results,
                           streak=current_user.streak_count or 0)

@routes_bp.route('/handle_generation', methods=['POST'])
@login_required
def handle_generation():
    source_type = request.form.get('source_type')
    quiz_format = request.form.get('quiz_format') 
    quiz_goal = request.form.get('quiz_goal')     
    count = int(request.form.get('count', 5))
    
    content = ""
    if source_type == 'topic':
        content = f"Topic: {request.form.get('topic_name')}"
    elif source_type == 'text':
        content = request.form.get('raw_text')
    elif source_type == 'pdf':
        file = request.files.get('pdf_file')
        if file:
            path = os.path.join(current_app.config['UPLOAD_FOLDER'], file.filename)
            file.save(path)
            reader = pypdf.PdfReader(path)
            content = " ".join([p.extract_text() for p in reader.pages if p.extract_text()])
            os.remove(path)

    raw_qs = llm.generate_questions(content, count, quiz_format=quiz_format)
    
    if not raw_qs:
        flash("AI failed to generate questions. Try adding more text!", "danger")
        return redirect(url_for('routes.dashboard'))

    q_ids = []
    for q in raw_qs:
        # SMART FIX: Check if THIS specific question has options, regardless of global format
        # This allows 'Mixed' mode to work correctly
        opts = q.get('options', {})
        
        new_q = Question(
            question_text=q.get('question_text'),
            options_json=json.dumps(opts),
            correct_answer=q.get('correct_answer'),
            explanation=q.get('explanation'),
            difficulty_level=q.get('difficulty', 'Medium'),
            user_id=current_user.id
        )
        db.session.add(new_q)
        db.session.flush()
        q_ids.append(new_q.id)
    db.session.commit()

    session['active_questions'] = q_ids
    session['user_answers'] = [] 
    session['quiz_goal'] = quiz_goal  
    session['quiz_format'] = quiz_format  
    session['current_idx'] = 0
    session['score'] = 0
    session.modified = True 

    if q_ids:
        return redirect(url_for('routes.quiz_page', q_id=q_ids[0]))
    return redirect(url_for('routes.dashboard'))

@routes_bp.route('/quiz/<int:q_id>')
@login_required
def quiz_page(q_id):
    question = Question.query.get_or_404(q_id)
    options = json.loads(question.options_json) if question.options_json else {}
    return render_template('quiz.html', 
                           question=question, 
                           options=options,
                           current_num=session.get('current_idx', 0) + 1,
                           total_num=len(session.get('active_questions', [])))

@routes_bp.route('/save_question/<int:q_id>', methods=['POST'])
@login_required
def save_question(q_id):
    return {"status": "success", "message": "Question tracked"}

@routes_bp.route('/submit_answer/<int:q_id>', methods=['POST'])
@login_required
def submit_answer(q_id):
    question = Question.query.get_or_404(q_id)
    user_ans = request.form.get('answer', '').strip()
    correct_ans = str(question.correct_answer).strip()
    
    is_correct = False
    options = json.loads(question.options_json) if question.options_json else {}
    
    # Grading logic that handles both MCQ and Short Answer
    if options:
        if user_ans.lower() == correct_ans.lower():
            is_correct = True
    else:
        # Keyword matching for short answers
        if user_ans.lower() and (user_ans.lower() in correct_ans.lower() or correct_ans.lower() in user_ans.lower()):
            is_correct = True

    if is_correct:
        session['score'] = session.get('score', 0) + 1

    review_list = session.get('user_answers', [])
    review_list.append({
        'question': question.question_text,
        'user_ans': user_ans,
        'correct_ans': correct_ans,
        'explanation': question.explanation,
        'is_correct': is_correct
    })
    session['user_answers'] = review_list
    session.modified = True

    q_list = session.get('active_questions', [])
    session['current_idx'] = session.get('current_idx', 0) + 1
    
    if session['current_idx'] < len(q_list):
        return redirect(url_for('routes.quiz_page', q_id=q_list[session['current_idx']]))
    else:
        # Streak Logic
        today = date.today()
        if current_user.last_quiz_date != today:
            if current_user.last_quiz_date == today - timedelta(days=1):
                current_user.streak_count += 1
            else:
                current_user.streak_count = 1
            current_user.last_quiz_date = today
        
        # Save Result
        total = len(q_list)
        final_score = session.get('score', 0)
        new_res = QuizResult(
            user_id=current_user.id,
            score=final_score,
            total_questions=total,
            accuracy=(final_score / total * 100) if total > 0 else 0,
            category=session.get('quiz_format', 'mixed')
        )
        db.session.add(new_res)
        db.session.commit()
        session['last_result_id'] = new_res.id 
        return redirect(url_for('routes.results'))

@routes_bp.route('/results')
@login_required
def results():
    score = session.get('score', 0)
    total = len(session.get('active_questions', []))
    accuracy = (score / total * 100) if total > 0 else 0
    
    if accuracy >= 85: recommendation = "🌟 Mastered! Great job."
    elif accuracy < 50: recommendation = "📚 Foundation Needed: Re-read the material."
    else: recommendation = "👍 Good progress! Keep practicing."

    history = QuizResult.query.filter_by(user_id=current_user.id).order_by(QuizResult.date_taken.asc()).limit(10).all()
    history_scores = [r.accuracy for r in history]
    history_labels = [f"Q{i+1}" for i in range(len(history))]

    return render_template('results.html', 
                           score=score, 
                           total=total, 
                           accuracy=accuracy, 
                           recommendation=recommendation,
                           history_scores=history_scores,
                           history_labels=history_labels)

@routes_bp.route('/library')
@login_required
def library():
    questions = Question.query.filter_by(user_id=current_user.id).order_by(Question.id.desc()).all()
    return render_template('library.html', questions=questions)

@routes_bp.route('/download_report/<int:res_id>')
@login_required
def download_report(res_id):
    res = QuizResult.query.get_or_404(res_id)
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.setFont("Helvetica-Bold", 20)
    p.drawCentredString(300, 750, "SmartQuizzer Performance Report")
    p.setFont("Helvetica", 12)
    p.drawString(100, 710, f"User: {current_user.username}")
    p.drawString(100, 695, f"Date: {res.date_taken.strftime('%Y-%m-%d %H:%M')}")
    p.line(100, 680, 500, 680)
    p.drawString(120, 610, f"• Total Questions: {res.total_questions}")
    p.drawString(120, 590, f"• Correct Answers: {res.score}")
    p.drawString(120, 570, f"• Overall Accuracy: {res.accuracy}%")
    p.showPage()
    p.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"Quiz_Report_{res_id}.pdf")

@routes_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Successfully logged out. See you next time!", "info")
    return redirect(url_for('routes.login'))