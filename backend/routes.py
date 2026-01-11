import json, os, io, time, base64
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import or_
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from dotenv import load_dotenv
from groq import Groq
from PIL import Image

# Model imports
from backend.models import User, Question, QuizResult, TopicMastery, MistakeBank, Bookmark, db
from backend.services import extract_text_from_pdf
from backend.llm_client import LLMClient

load_dotenv()
routes_bp = Blueprint('routes', __name__)

# Initialize Clients
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
llm = LLMClient(api_key=os.getenv("GROQ_API_KEY"))

# ==========================================
# HELPER: VISION OCR (Fixed Model)
# ==========================================
def extract_text_via_groq_vision(file_storage):
    if not file_storage:
        return ""
    try:
        file_storage.seek(0)
        img = Image.open(file_storage)
        img.thumbnail((1600, 1600)) 
        img_byte_arr = io.BytesIO()
        img = img.convert("RGB")
        img.save(img_byte_arr, format='JPEG', quality=85) 
        image_bytes = img_byte_arr.getvalue()
        encoded_image = base64.b64encode(image_bytes).decode('utf-8')
        
        # CHANGED: Using the Compound model which supports Vision
        response = client.chat.completions.create(
            model="groq/compound", 
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Please extract all text from this image. Format it clearly for study notes."},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"}
                        }
                    ]
                }
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Vision API Error: {e}")
        return ""
# ==========================================
# AUTHENTICATION
# ==========================================

@routes_bp.route('/')
def index():
    return render_template('landing.html')

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
            return redirect(url_for('routes.dashboard'))
        flash("Invalid credentials.", "danger")
    return render_template('login.html')

@routes_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        if User.query.filter((User.email == email) | (User.username == username)).first():
            flash("User already exists!", "danger")
            return redirect(url_for('routes.signup'))
        new_user = User(email=email, username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash("Account created!", "success")
        return redirect(url_for('routes.login'))
    return render_template('signup.html')

@routes_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('routes.login'))

# ==========================================
# STUDY HUB
# ==========================================

@routes_bp.route('/study-hub', methods=['GET', 'POST'])
@login_required
def study_hub():
    if request.method == 'POST':
        source_type = request.form.get('source_type')
        content = ""
        if source_type == 'pdf':
            content = extract_text_from_pdf(request.files.get('pdf_file'))
        elif source_type == 'text':
            content = request.form.get('raw_text')
        elif source_type == 'topic':
            content = f"Generate study materials for: {request.form.get('topic_name')}"

        if not content:
            flash("Please provide content to learn!", "warning")
            return redirect(url_for('routes.study_hub'))

        study_bundle = llm.generate_study_material(content)
        return render_template('study_hub_result.html', data=study_bundle)
    return render_template('study_hub.html')

# ==========================================
# DASHBOARD & RESULTS
# ==========================================

@routes_bp.route('/dashboard')
@login_required
def dashboard():
    allowed_topics = ['PDF Review', 'Image Review', 'Text Review', 'Topic Review']
    topic_mastery = TopicMastery.query.filter(
        TopicMastery.user_id == current_user.id,
        TopicMastery.topic_name.in_(allowed_topics)
    ).all()
    mistake_count = MistakeBank.query.filter_by(user_id=current_user.id).count()
    results_list = QuizResult.query.filter_by(user_id=current_user.id).order_by(QuizResult.date_taken.desc()).all()
    correct_total = sum([r.score for r in results_list]) if results_list else 0
    total_q = sum([r.total_questions for r in results_list]) if results_list else 0
    
    return render_template('dashboard.html', 
                           fun_fact=llm.get_fun_fact(),
                           correct_total=correct_total, 
                           incorrect_total=total_q - correct_total,
                           topic_mastery=topic_mastery,
                           mistake_count=mistake_count,
                           streak=current_user.streak_count or 0)

@routes_bp.route('/handle_generation', methods=['POST'])
@login_required
def handle_generation():
    source_type = request.form.get('source_type')
    quiz_goal = request.form.get('quiz_goal', 'revision').lower().strip()
    count = int(request.form.get('count', 5))
    content, mastery_label = "", ""

    try:
        if source_type == 'pdf':
            content = extract_text_from_pdf(request.files.get('pdf_file'))
            mastery_label = 'PDF Review'
        elif source_type == 'image':
            content = extract_text_via_groq_vision(request.files.get('image_file'))
            mastery_label = 'Image Review'
        elif source_type == 'text':
            content = request.form.get('raw_text')
            mastery_label = 'Text Review'
        elif source_type == 'topic':
            content = f"Topic focus: {request.form.get('topic_name')}"
            mastery_label = 'Topic Review'

        if not content:
            flash("No content found.", "warning")
            return redirect(url_for('routes.dashboard'))

        # Inside handle_generation route:
        raw_qs = llm.generate_questions(content, count, source_type=source_type)
        q_ids = []
        for q in raw_qs:
            new_q = Question(
                question_text=q.get('question_text'),
                options_json=json.dumps(q.get('options', {})),
                correct_answer=q.get('correct_answer'),
                explanation=q.get('explanation'),
                difficulty_level=q.get('difficulty', 'Medium'),
                user_id=current_user.id
            )
            db.session.add(new_q)
            db.session.flush()
            q_ids.append(new_q.id)
        
        db.session.commit()
        session.update({
            'active_questions': q_ids, 'is_mistake_review': False,
            'current_idx': 0, 'score': 0, 'quiz_topic': mastery_label,
            'quiz_goal': quiz_goal, 'user_answers': [], 
            'time_limit': (count * 30), 'start_time': time.time()
        })
        return redirect(url_for('routes.quiz_page', q_id=q_ids[0]))
    except Exception as e:
        db.session.rollback()
        flash(f"Error: {str(e)}", "danger")
        return redirect(url_for('routes.dashboard'))

# ==========================================
# QUIZ EXECUTION
# ==========================================

@routes_bp.route('/quiz/<int:q_id>')
@login_required
def quiz_page(q_id):
    question = MistakeBank.query.get_or_404(q_id) if session.get('is_mistake_review') else Question.query.get_or_404(q_id)
    try:
        options_data = json.loads(question.options_json) if isinstance(question.options_json, str) else question.options_json
    except:
        options_data = {}
    
    rem_time = 0
    if session.get('quiz_goal') == 'quiz':
        elapsed = time.time() - session.get('start_time', 0)
        rem_time = max(0, int(session.get('time_limit', 30) - elapsed))

    return render_template('quiz.html', question=question, options=options_data, remaining_time=rem_time,
                           current_num=session.get('current_idx', 0) + 1, total_num=len(session.get('active_questions', [])))

@routes_bp.route('/submit_answer/<int:q_id>', methods=['POST'])
@login_required
def submit_answer(q_id):
    question = MistakeBank.query.get_or_404(q_id) if session.get('is_mistake_review') else Question.query.get_or_404(q_id)
    user_ans = request.form.get('answer', '').strip()
    is_correct = (user_ans.lower() == str(question.correct_answer).lower())

    if 'user_answers' not in session: session['user_answers'] = []
    session['user_answers'].append({'question': question.question_text, 'is_correct': is_correct})

    if is_correct:
        session['score'] = session.get('score', 0) + 1
        if session.get('is_mistake_review'): db.session.delete(question)
    else:
        if not session.get('is_mistake_review'):
            new_mistake = MistakeBank(user_id=current_user.id, question_text=question.question_text, 
                                      options_json=question.options_json, correct_answer=question.correct_answer,
                                      explanation=question.explanation, topic=session.get('quiz_topic'))
            db.session.add(new_mistake)

    db.session.commit()
    session['current_idx'] = session.get('current_idx', 0) + 1
    q_list = session.get('active_questions', [])
    if session['current_idx'] < len(q_list):
        return redirect(url_for('routes.quiz_page', q_id=q_list[session['current_idx']]))
    return redirect(url_for('routes.results'))

@routes_bp.route('/review_mistakes') # This name must match url_for('routes.review_mistakes')
@login_required
def review_mistakes():
    now = datetime.utcnow()
    mistakes = MistakeBank.query.filter(MistakeBank.user_id == current_user.id, MistakeBank.next_review <= now).all()
    
    if not mistakes:
        mistakes = MistakeBank.query.filter_by(user_id=current_user.id).limit(10).all()
    
    if not mistakes:
        flash("No mistakes to review yet! Keep practicing.", "info")
        return redirect(url_for('routes.dashboard'))
    
    m_ids = [m.id for m in mistakes]
    session.update({
        'active_questions': m_ids, 
        'is_mistake_review': True, 
        'current_idx': 0, 
        'score': 0, 
        'quiz_topic': 'Mistake Review'
    })
    return redirect(url_for('routes.quiz_page', q_id=m_ids[0]))
    
@routes_bp.route('/results')
@login_required
def results():
    score, total = session.get('score', 0), len(session.get('active_questions', []))
    new_res = QuizResult(user_id=current_user.id, score=score, total_questions=total)
    db.session.add(new_res)
    db.session.commit()
    return render_template('results.html', score=score, total=total, accuracy=(score/total*100 if total > 0 else 0))

# ==========================================
# DOWNLOAD REPORT (Fixed ReportLab Logic)
# ==========================================

@routes_bp.route('/download_report/<int:res_id>')
@login_required
def download_report(res_id):
    result = QuizResult.query.get_or_404(res_id)
    if result.user_id != current_user.id:
        return redirect(url_for('routes.dashboard'))

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.setFont("Helvetica-Bold", 24)
    p.drawString(100, 750, "Quiz Performance Report")
    p.setFont("Helvetica", 14)
    p.drawString(100, 700, f"User: {current_user.username}")
    p.drawString(100, 680, f"Score: {result.score} / {result.total_questions}")
    p.showPage()
    p.save()
    buffer.seek(0)
    return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=f"Report_{res_id}.pdf")

@routes_bp.route('/library')
@login_required
def library():
    questions = Question.query.filter_by(user_id=current_user.id).order_by(Question.id.desc()).limit(50).all()
    for q in questions:
        q.options = json.loads(q.options_json) if isinstance(q.options_json, str) else q.options_json
    return render_template('library.html', questions=questions)
