import json, os, io, time
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import or_
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from dotenv import load_dotenv

from backend.models import User, Question, QuizResult, TopicMastery, MistakeBank, Bookmark, db
from backend.services import extract_text_from_image, extract_text_from_pdf
from backend.llm_client import LLMClient

load_dotenv()
routes_bp = Blueprint('routes', __name__)
llm = LLMClient(api_key=os.getenv("GROQ_API_KEY"))

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
# DASHBOARD
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

# ==========================================
# GENERATION ENGINE
# ==========================================

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
            content = extract_text_from_image(request.files.get('image_file'))
            mastery_label = 'Image Review'
        elif source_type == 'text':
            content = request.form.get('raw_text')
            mastery_label = 'Text Review'
        elif source_type == 'topic':
            content = f"Topic focus: {request.form.get('topic_name')}"
            mastery_label = 'Topic Review'

        raw_qs = llm.generate_questions(content, count)
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
            'active_questions': q_ids,
            'is_mistake_review': False,
            'current_idx': 0,
            'score': 0,
            'quiz_topic': mastery_label,
            'quiz_goal': quiz_goal,
            'user_answers': [], 
            'time_limit': (count * 30),
            'start_time': time.time()
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
    if session.get('is_mistake_review'):
        question = MistakeBank.query.get_or_404(q_id)
    else:
        question = Question.query.get_or_404(q_id)
    
    # Safely handle JSON parsing
    try:
        options_data = json.loads(question.options_json) if isinstance(question.options_json, str) else question.options_json
    except Exception as e:
        print(f"Error parsing options: {e}")
        options_data = {}

    rem_time = 0
    if session.get('quiz_goal') == 'quiz':
        elapsed = time.time() - session.get('start_time', 0)
        rem_time = max(0, int(session.get('time_limit', 30) - elapsed))

    return render_template('quiz.html', 
                           question=question, 
                           options=options_data,
                           remaining_time=rem_time,
                           current_num=session.get('current_idx', 0) + 1,
                           total_num=len(session.get('active_questions', [])))

@routes_bp.route('/submit_answer/<int:q_id>', methods=['POST'])
@login_required
def submit_answer(q_id):
    if session.get('is_mistake_review'):
        question = MistakeBank.query.get_or_404(q_id)
    else:
        question = Question.query.get_or_404(q_id)

    user_ans = request.form.get('answer', '').strip()
    confidence = request.form.get('confidence', 'medium')
    is_correct = (user_ans.lower() == str(question.correct_answer).lower())

    # Update User Answers for Detailed Review
    if 'user_answers' not in session:
        session['user_answers'] = []
    
    temp_answers = session['user_answers']
    temp_answers.append({
        'question': question.question_text,
        'user_ans': user_ans,
        'correct_ans': question.correct_answer,
        'is_correct': is_correct,
        'explanation': question.explanation
    })
    session['user_answers'] = temp_answers

    # Spaced Repetition Logic
    days_to_add = 1
    if is_correct:
        if confidence == 'high': days_to_add = 7
        elif confidence == 'medium': days_to_add = 3
    
    next_review_date = datetime.utcnow() + timedelta(days=days_to_add)

    # Mastery Logic
    topic = session.get('quiz_topic', 'Topic Review')
    m = TopicMastery.query.filter_by(user_id=current_user.id, topic_name=topic).first()
    
    if m is None:
        m = TopicMastery(user_id=current_user.id, topic_name=topic, total_count=1, correct_count=0)
        db.session.add(m)
    else:
        m.total_count = (m.total_count or 0) + 1

    if is_correct:
        m.correct_count = (m.correct_count or 0) + 1
        session['score'] = session.get('score', 0) + 1
        # If it was a mistake review, remove it from the bank upon success
        if session.get('is_mistake_review'):
            db.session.delete(question) 
    else:
        # Add to Mistake Bank if it's a new error
        if not session.get('is_mistake_review'):
            new_mistake = MistakeBank(
                user_id=current_user.id, 
                question_text=question.question_text,
                options_json=question.options_json, 
                correct_answer=question.correct_answer,
                explanation=question.explanation, 
                topic=topic,
                next_review=next_review_date,
                confidence_level=confidence,
                total_count=1
            )
            db.session.add(new_mistake)

    db.session.commit()
    session.modified = True 
    
    session['current_idx'] = session.get('current_idx', 0) + 1
    q_list = session.get('active_questions', [])
    
    if session['current_idx'] < len(q_list):
        return redirect(url_for('routes.quiz_page', q_id=q_list[session['current_idx']]))
    return redirect(url_for('routes.results'))

# ==========================================
# ELI5 SIMPLIFIER
# ==========================================

@routes_bp.route('/simplify', methods=['POST'])
@login_required
def simplify():
    data = request.json
    original_text = data.get('explanation', '')
    prompt = f"Explain the following academic concept like I'm 5 years old using a funny analogy: {original_text}"
    try:
        completion = llm.client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
        )
        return jsonify({"simplified": completion.choices[0].message.content})
    except:
        return jsonify({"simplified": "AI error. Try again."}), 500

# ==========================================
# RESULTS & REPORTS
# ==========================================

@routes_bp.route('/results')
@login_required
def results():
    score = session.get('score', 0)
    active_qs = session.get('active_questions', [])
    total = len(active_qs)
    accuracy = (score / total * 100) if total > 0 else 0

    if accuracy >= 80:
        recommendation = "Outstanding! You've mastered these concepts. Ready for a harder challenge?"
    elif accuracy >= 50:
        recommendation = "Solid performance. Review the explanations for missed items to reach 100%."
    else:
        recommendation = "Don't get discouraged! Re-read the source material and try Revision Mode."

    new_res = QuizResult(user_id=current_user.id, score=score, total_questions=total)
    db.session.add(new_res)
    current_user.streak_count = (current_user.streak_count or 0) + 1
    db.session.commit()

    history_results = QuizResult.query.filter_by(user_id=current_user.id)\
        .order_by(QuizResult.date_taken.asc()).limit(10).all()
    
    history_labels = [r.date_taken.strftime("%b %d") for r in history_results]
    history_scores = [int((r.score/r.total_questions)*100) if r.total_questions > 0 else 0 for r in history_results]

    session['last_result_id'] = new_res.id 
    mastery_data = TopicMastery.query.filter_by(user_id=current_user.id).all()

    return render_template('results.html', 
                           score=score, 
                           total=total, 
                           accuracy=accuracy, 
                           recommendation=recommendation,
                           mastery_data=mastery_data,
                           history_labels=history_labels,
                           history_scores=history_scores)

@routes_bp.route('/download_report/<int:res_id>')
@login_required
def download_report(res_id):
    result = QuizResult.query.get_or_404(res_id)
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, 750, "Quiz Performance Report")
    p.setFont("Helvetica", 12)
    p.drawString(100, 720, f"User: {current_user.username}")
    p.drawString(100, 700, f"Date: {result.date_taken.strftime('%Y-%m-%d %H:%M')}")
    p.drawString(100, 680, f"Score: {result.score} / {result.total_questions}")
    p.drawString(100, 660, f"Accuracy: {(result.score/result.total_questions*100):.1f}%")
    p.showPage()
    p.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"Report_{res_id}.pdf", mimetype='application/pdf')

# ==========================================
# MISC & REVIEW
# ==========================================

@routes_bp.route('/review_mistakes')
@login_required
def review_mistakes():
    now = datetime.utcnow()
    # Pull mistakes due for review
    mistakes = MistakeBank.query.filter(
        MistakeBank.user_id == current_user.id,
        MistakeBank.next_review <= now
    ).all()
    
    # Fallback if none are "due" yet so user can still practice
    if not mistakes:
        mistakes = MistakeBank.query.filter_by(user_id=current_user.id).limit(10).all()
    
    if not mistakes:
        flash("Your Mistake Bank is empty!", "success")
        return redirect(url_for('routes.dashboard'))
    
    m_ids = [m.id for m in mistakes]
    session.update({
        'active_questions': m_ids, 
        'is_mistake_review': True, 
        'current_idx': 0, 
        'score': 0, 
        'quiz_goal': 'revision',
        'quiz_topic': 'Mistake Review',
        'user_answers': []
    })
    return redirect(url_for('routes.quiz_page', q_id=m_ids[0]))
@routes_bp.route('/library')
@login_required
def library():
    # 1. Only get the 50 most recent questions to prevent the page from freezing
    questions = Question.query.filter_by(user_id=current_user.id)\
                        .order_by(Question.id.desc())\
                        .limit(50).all()
    
    # 2. Parse the options safely before sending to the template
    for q in questions:
        if q.options_json:
            try:
                # If it's already a dict, use it; otherwise, parse it
                if isinstance(q.options_json, str):
                    q.options = json.loads(q.options_json)
                else:
                    q.options = q.options_json
            except Exception:
                q.options = {"Error": "Could not load options"}
        else:
            q.options = {}
            
    return render_template('library.html', questions=questions)