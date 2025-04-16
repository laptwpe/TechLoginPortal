import os
import logging

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy
db = SQLAlchemy(model_class=Base)

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # Needed for url_for to generate with https

# Configure the database (using SQLite for simplicity in this example)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///instance/techstudents.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize SQLAlchemy with the app
db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# Import models
from models import User, Announcement, Event, Course, Material, Assignment, AssignmentSubmission, Enrollment

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Import routes
with app.app_context():
    # Create tables
    db.create_all()
    
    # Import routes after app and db are fully setup
    from routes import index, login, logout, dashboard, profile, change_password, forgot_password, register, create_test_user
    from routes.admin_routes import (admin_dashboard, admin_users, admin_add_user, admin_edit_user, admin_delete_user,
                                     admin_announcements, admin_add_announcement, admin_edit_announcement, admin_delete_announcement,
                                     admin_events, admin_add_event, admin_edit_event, admin_delete_event,
                                     admin_courses, admin_add_course, admin_edit_course, admin_delete_course,
                                     admin_course_materials, admin_add_material, admin_edit_material, admin_delete_material,
                                     admin_course_assignments, admin_add_assignment, admin_edit_assignment, admin_delete_assignment,
                                     admin_view_submissions, admin_view_submission, admin_grade_submission)