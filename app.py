from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'model'))

app = Flask(__name__)
app.secret_key = 'expense_tracker_secret_2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ─── Models ───────────────────────────────────────────────────────────────────

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expenses = db.relationship('Expense', backref='user', lazy=True, cascade='all, delete-orphan')

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    note = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

CATEGORIES = ['Food', 'Transport', 'Entertainment', 'Shopping', 'Bills', 'Health', 'Education', 'Other']

# ─── Auth ─────────────────────────────────────────────────────────────────────

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not username or not email or not password:
            return render_template('login.html', error='All fields are required.', mode='register')
        if User.query.filter_by(username=username).first():
            return render_template('login.html', error='Username already taken.', mode='register')
        if User.query.filter_by(email=email).first():
            return render_template('login.html', error='Email already registered.', mode='register')

        user = User(username=username, email=email, password=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        session['user_id'] = user.id
        session['username'] = user.username
        return redirect(url_for('dashboard'))

    return render_template('login.html', mode='register')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('dashboard'))
        return render_template('login.html', error='Invalid credentials.', mode='login')

    return render_template('login.html', mode='login')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# ─── Dashboard ────────────────────────────────────────────────────────────────

@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    now = datetime.utcnow()
    month_start = now.replace(day=1).date()

    expenses = Expense.query.filter_by(user_id=user_id).order_by(Expense.date.desc()).all()
    month_expenses = [e for e in expenses if e.date >= month_start]

    total_month = sum(e.amount for e in month_expenses)
    total_all = sum(e.amount for e in expenses)

    category_totals = {}
    for e in month_expenses:
        category_totals[e.category] = category_totals.get(e.category, 0) + e.amount

    recent = expenses[:5]
    return render_template(
        'dashboard.html',
        expenses=expenses,
        month_expenses=month_expenses,
        recent=recent,
        total_month=round(total_month, 2),
        total_all=round(total_all, 2),
        category_totals=category_totals,
        categories=CATEGORIES,
        username=session['username'],
        now=now
    )

# ─── Expense CRUD ─────────────────────────────────────────────────────────────

@app.route('/add_expense', methods=['POST'])
@login_required
def add_expense():
    title = request.form.get('title', '').strip()
    amount = request.form.get('amount', 0)
    category = request.form.get('category', 'Other')
    date_str = request.form.get('date', '')
    note = request.form.get('note', '').strip()

    try:
        amount = float(amount)
        date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else datetime.utcnow().date()
    except (ValueError, TypeError):
        return redirect(url_for('dashboard'))

    expense = Expense(
        user_id=session['user_id'],
        title=title,
        amount=amount,
        category=category,
        date=date,
        note=note
    )
    db.session.add(expense)
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/edit_expense/<int:expense_id>', methods=['POST'])
@login_required
def edit_expense(expense_id):
    expense = Expense.query.filter_by(id=expense_id, user_id=session['user_id']).first_or_404()
    expense.title = request.form.get('title', expense.title).strip()
    try:
        expense.amount = float(request.form.get('amount', expense.amount))
    except ValueError:
        pass
    expense.category = request.form.get('category', expense.category)
    date_str = request.form.get('date', '')
    if date_str:
        try:
            expense.date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    expense.note = request.form.get('note', expense.note).strip()
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/delete_expense/<int:expense_id>', methods=['POST'])
@login_required
def delete_expense(expense_id):
    expense = Expense.query.filter_by(id=expense_id, user_id=session['user_id']).first_or_404()
    db.session.delete(expense)
    db.session.commit()
    return redirect(url_for('dashboard'))

# ─── API Endpoints ────────────────────────────────────────────────────────────

@app.route('/api/chart_data')
@login_required
def chart_data():
    user_id = session['user_id']
    now = datetime.utcnow()
    month_start = now.replace(day=1).date()
    expenses = Expense.query.filter(
        Expense.user_id == user_id,
        Expense.date >= month_start
    ).all()

    category_totals = {}
    for e in expenses:
        category_totals[e.category] = category_totals.get(e.category, 0) + e.amount

    # Daily trend (last 30 days)
    thirty_days_ago = (now - timedelta(days=29)).date()
    all_recent = Expense.query.filter(
        Expense.user_id == user_id,
        Expense.date >= thirty_days_ago
    ).all()

    daily = {}
    for i in range(30):
        d = (now - timedelta(days=29-i)).date()
        daily[d.strftime('%b %d')] = 0
    for e in all_recent:
        key = e.date.strftime('%b %d')
        if key in daily:
            daily[key] += e.amount

    # Monthly trend (last 6 months)
    monthly = {}
    for i in range(6):
        m = (now.replace(day=1) - timedelta(days=i*28)).replace(day=1)
        key = m.strftime('%b %Y')
        monthly[key] = 0
    for e in Expense.query.filter_by(user_id=user_id).all():
        key = e.date.strftime('%b %Y')
        if key in monthly:
            monthly[key] += e.amount

    return jsonify({
        'category_labels': list(category_totals.keys()),
        'category_data': list(category_totals.values()),
        'daily_labels': list(daily.keys()),
        'daily_data': list(daily.values()),
        'monthly_labels': list(reversed(list(monthly.keys()))),
        'monthly_data': list(reversed(list(monthly.values())))
    })

@app.route('/api/ai_insights')
@login_required
def ai_insights():
    try:
        from train_model import analyze_spending, predict_expense
    except ImportError:
        import importlib.util, os
        spec = importlib.util.spec_from_file_location("train_model",
            os.path.join(os.path.dirname(__file__), 'model', 'train_model.py'))
        tm = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tm)
        analyze_spending = tm.analyze_spending
        predict_expense = tm.predict_expense

    user_id = session['user_id']
    expenses = Expense.query.filter_by(user_id=user_id).all()
    expenses_data = [{'amount': e.amount, 'category': e.category} for e in expenses]

    analysis = analyze_spending(expenses_data)

    next_month = datetime.utcnow().month % 12 + 1
    predictions = {}
    for cat in CATEGORIES[:6]:
        try:
            predictions[cat] = predict_expense(next_month, cat)
        except Exception:
            predictions[cat] = 0

    # Smart alerts
    alerts = []
    now = datetime.utcnow()
    month_start = now.replace(day=1).date()
    month_expenses = [e for e in expenses if e.date >= month_start]
    month_total = sum(e.amount for e in month_expenses)

    if month_total > 15000:
        alerts.append({'type': 'warning', 'message': f'Monthly spending ₹{month_total:,.0f} exceeds ₹15,000 threshold!'})
    if month_total > 25000:
        alerts.append({'type': 'danger', 'message': 'Critical: You\'ve exceeded ₹25,000 this month!'})

    cat_totals = {}
    for e in month_expenses:
        cat_totals[e.category] = cat_totals.get(e.category, 0) + e.amount
    for cat, total in cat_totals.items():
        if cat == 'Food' and total > 8000:
            alerts.append({'type': 'warning', 'message': f'Food spending ₹{total:,.0f} is very high this month.'})
        if cat == 'Entertainment' and total > 3000:
            alerts.append({'type': 'info', 'message': f'Entertainment spend ₹{total:,.0f} — consider a budget cap.'})

    if not alerts:
        alerts.append({'type': 'success', 'message': 'All spending within healthy limits. Keep it up!'})

    return jsonify({
        'analysis': analysis,
        'predictions': predictions,
        'alerts': alerts
    })

# ─── Run ──────────────────────────────────────────────────────────────────────

with app.app_context():
    db.create_all()
    # Train model on startup
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("train_model",
            os.path.join(os.path.dirname(__file__), 'model', 'train_model.py'))
        tm = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tm)
        tm.train_expense_model()
    except Exception as e:
        print(f"Model training skipped: {e}")

if __name__ == '__main__':
   import os
port = int(os.environ.get('PORT', 5000))
app.run(debug=False, host='0.0.0.0', port=port)