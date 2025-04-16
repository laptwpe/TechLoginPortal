import os
import logging
from datetime import datetime

from flask import Flask, render_template, url_for, flash, redirect, request, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy
db = SQLAlchemy(model_class=Base)

# Create the Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Configure database - using PostgreSQL if available, otherwise SQLite
if os.environ.get('DATABASE_URL'):
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
else:
    # Use SQLite for development
    database_path = os.path.join(app.root_path, 'instance', 'techstudents.db')
    os.makedirs(os.path.dirname(database_path), exist_ok=True)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_path}'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database with app
db.init_app(app)

# Setup proxy fix for proper URL generation behind proxy
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'الرجاء تسجيل الدخول للوصول إلى هذه الصفحة.'
login_manager.login_message_category = 'info'

# Import models after db initialization
from models import User, Announcement, Event, Course, Enrollment

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Import forms after app initialization
import forms

# Create database tables within app context
with app.app_context():
    db.create_all()
    
    # Check if test users exist
    admin_user = User.query.filter_by(username='admin').first()
    student_user = User.query.filter_by(username='student').first()
    
    # Create admin test user if doesn't exist
    if not admin_user:
        admin = User(
            username='admin',
            email='admin@example.com',
            password_hash=generate_password_hash('admin123'),
            first_name='مدير',
            last_name='النظام',
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()
        print("Admin test user created")
    
    # Create student test user if doesn't exist
    if not student_user:
        student = User(
            username='student',
            email='student@example.com',
            password_hash=generate_password_hash('password123'),
            first_name='طالب',
            last_name='تجريبي',
            student_id='S12345',
            department='علوم الحاسب',
            role='student'
        )
        db.session.add(student)
        db.session.commit()
        print("Student test user created")

# Routes
@app.route('/')
def index():
    # Redirect to dashboard if user is already logged in
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    # Otherwise show the login page
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Redirect to dashboard if user is already logged in
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = forms.LoginForm()
    
    if form.validate_on_submit():
        # Check if input is email or username
        user = None
        if '@' in form.username_or_email.data:
            user = User.query.filter_by(email=form.username_or_email.data.lower()).first()
        else:
            user = User.query.filter_by(username=form.username_or_email.data).first()
        
        # Verify user and password
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember.data)
            
            # Redirect to requested page or default to dashboard
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            else:
                if user.is_admin():
                    return redirect(url_for('admin_dashboard'))
                return redirect(url_for('dashboard'))
        else:
            flash('Login failed. Please check your username/email and password.', 'danger')
    
    return render_template('login.html', title='Login', form=form)

@app.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Admin users should be redirected to admin dashboard
    if current_user.is_admin():
        return redirect(url_for('admin_dashboard'))
    
    # Get latest announcements
    announcements = Announcement.query.order_by(Announcement.created_at.desc()).limit(5).all()
    
    # Get upcoming events
    upcoming_events = Event.query.filter(Event.start_time >= datetime.utcnow()).order_by(Event.start_time).limit(5).all()
    
    # Get user's courses
    if current_user.is_teacher():
        # Teachers see courses they teach
        courses = current_user.courses.all()
    else:
        # Students see courses they're enrolled in
        enrollments = current_user.enrollments.all()
        course_ids = [enrollment.course_id for enrollment in enrollments]
        courses = Course.query.filter(Course.id.in_(course_ids)).all() if course_ids else []
    
    return render_template('dashboard.html', 
                          title='Dashboard',
                          announcements=announcements,
                          upcoming_events=upcoming_events,
                          courses=courses)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = forms.UserProfileForm(original_username=current_user.username)
    
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.student_id = form.student_id.data
        current_user.department = form.department.data
        
        db.session.commit()
        flash('Your profile has been updated.', 'success')
        return redirect(url_for('profile'))
    
    # Pre-populate form fields with current user data
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.first_name.data = current_user.first_name
        form.last_name.data = current_user.last_name
        form.student_id.data = current_user.student_id
        form.department.data = current_user.department
    
    return render_template('profile.html', title='Profile', form=form)

@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = forms.ChangePasswordForm()
    
    if form.validate_on_submit():
        # Verify current password
        if check_password_hash(current_user.password_hash, form.current_password.data):
            current_user.password_hash = generate_password_hash(form.password.data)
            db.session.commit()
            flash('Your password has been updated.', 'success')
            return redirect(url_for('profile'))
        else:
            flash('Current password is incorrect.', 'danger')
    
    return render_template('change_password.html', title='Change Password', form=form)

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = forms.PasswordResetRequestForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            # Here you would normally send a password reset email
            # For this example, we'll just display a flash message
            flash('Instructions to reset your password have been sent to your email.', 'info')
            return redirect(url_for('login'))
        else:
            flash('No account found with that email address.', 'warning')
    
    return render_template('password_reset_request.html', title='Reset Password', form=form)

# Testing route - create a test user
@app.route('/create-test-user')
def create_test_user():
    admin_exists = User.query.filter_by(username='admin').first()
    student_exists = User.query.filter_by(username='student').first()
    
    if not admin_exists:
        admin = User(
            username='admin',
            email='admin@example.com',
            password_hash=generate_password_hash('admin123'),
            first_name='مدير',
            last_name='النظام',
            role='admin'
        )
        db.session.add(admin)
    
    if not student_exists:
        student = User(
            username='student',
            email='student@example.com',
            password_hash=generate_password_hash('password123'),
            first_name='طالب',
            last_name='تجريبي',
            student_id='S12345',
            department='علوم الحاسب',
            role='student'
        )
        db.session.add(student)
    
    db.session.commit()
    flash('Test users created: admin/admin123 and student/password123', 'success')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = forms.RegistrationForm()
    
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data.lower(),
            password_hash=generate_password_hash(form.password.data),
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            student_id=form.student_id.data,
            department=form.department.data,
            role='student'  # Default role is student
        )
        
        db.session.add(user)
        db.session.commit()
        
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', title='Register', form=form)

# Import admin routes after app is defined to avoid circular imports
from admin_routes import register_admin_routes
register_admin_routes(app)