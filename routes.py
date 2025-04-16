import os
from flask import render_template, url_for, flash, redirect, request, abort
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import secrets

from app import app, db
from forms import LoginForm, RegistrationForm, PasswordResetRequestForm, PasswordResetForm, UserProfileForm, ChangePasswordForm
from models import User, Announcement, Event, Course, Enrollment

# Import admin routes
from routes.admin_routes import (
    admin_dashboard, admin_users, admin_add_user, admin_edit_user, admin_delete_user,
    admin_announcements, admin_add_announcement, admin_edit_announcement, admin_delete_announcement,
    admin_events, admin_add_event, admin_edit_event, admin_delete_event,
    admin_courses, admin_add_course, admin_edit_course, admin_delete_course,
    admin_teachers, admin_assignments, admin_add_assignment, admin_edit_assignment, admin_delete_assignment,
    admin_materials, admin_add_material, admin_edit_material, admin_delete_material,
    admin_settings
)

# Register admin routes
app.add_url_rule('/admin', view_func=admin_dashboard)
app.add_url_rule('/admin/dashboard', view_func=admin_dashboard)
app.add_url_rule('/admin/users', view_func=admin_users)
app.add_url_rule('/admin/users/add', view_func=admin_add_user, methods=['POST'])
app.add_url_rule('/admin/users/edit', view_func=admin_edit_user, methods=['POST'])
app.add_url_rule('/admin/users/delete', view_func=admin_delete_user, methods=['POST'])
app.add_url_rule('/admin/announcements', view_func=admin_announcements)
app.add_url_rule('/admin/announcements/add', view_func=admin_add_announcement, methods=['POST'])
app.add_url_rule('/admin/announcements/edit/<int:announcement_id>', view_func=admin_edit_announcement, methods=['GET', 'POST'])
app.add_url_rule('/admin/announcements/delete/<int:announcement_id>', view_func=admin_delete_announcement)
app.add_url_rule('/admin/events', view_func=admin_events)
app.add_url_rule('/admin/events/add', view_func=admin_add_event, methods=['POST'])
app.add_url_rule('/admin/events/edit/<int:event_id>', view_func=admin_edit_event, methods=['GET', 'POST'])
app.add_url_rule('/admin/events/delete/<int:event_id>', view_func=admin_delete_event)
app.add_url_rule('/admin/courses', view_func=admin_courses)
app.add_url_rule('/admin/courses/add', view_func=admin_add_course, methods=['POST'])
app.add_url_rule('/admin/courses/edit/<int:course_id>', view_func=admin_edit_course, methods=['GET', 'POST'])
app.add_url_rule('/admin/courses/delete/<int:course_id>', view_func=admin_delete_course)
app.add_url_rule('/admin/teachers', view_func=admin_teachers)
app.add_url_rule('/admin/assignments', view_func=admin_assignments)
app.add_url_rule('/admin/assignments/add', view_func=admin_add_assignment, methods=['POST'])
app.add_url_rule('/admin/assignments/edit/<int:assignment_id>', view_func=admin_edit_assignment, methods=['GET', 'POST'])
app.add_url_rule('/admin/assignments/delete/<int:assignment_id>', view_func=admin_delete_assignment)
app.add_url_rule('/admin/materials', view_func=admin_materials)
app.add_url_rule('/admin/materials/add', view_func=admin_add_material, methods=['POST'])
app.add_url_rule('/admin/materials/edit/<int:material_id>', view_func=admin_edit_material, methods=['GET', 'POST'])
app.add_url_rule('/admin/materials/delete/<int:material_id>', view_func=admin_delete_material)
app.add_url_rule('/admin/settings', view_func=admin_settings)

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
    
    form = LoginForm()
    
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
    form = UserProfileForm(original_username=current_user.username)
    
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
    form = ChangePasswordForm()
    
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
    
    form = PasswordResetRequestForm()
    
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
    
    form = RegistrationForm()
    
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