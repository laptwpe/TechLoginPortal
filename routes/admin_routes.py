import os
import logging
from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime

from app import db
from models import User, Announcement, Event, Course, Material, Assignment, AssignmentSubmission
from forms.admin_forms import (
    AdminUserForm, 
    AdminEditUserForm, 
    DeleteUserForm,
    AnnouncementForm,
    EventForm,
    CourseForm,
    MaterialForm,
    AssignmentForm,
    GradeSubmissionForm
)

# Admin required decorator
def admin_required(f):
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin():
            flash('عذراً، يجب أن تكون مشرفاً للوصول إلى هذه الصفحة.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Teacher required decorator
def teacher_required(f):
    @login_required
    def decorated_function(*args, **kwargs):
        if not (current_user.is_admin() or current_user.is_teacher()):
            flash('عذراً، يجب أن تكون معلماً أو مشرفاً للوصول إلى هذه الصفحة.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Admin Dashboard
@admin_required
def admin_dashboard():
    return render_template('admin/dashboard.html')

# User Management
@admin_required
def admin_users():
    users = User.query.all()
    add_user_form = AdminUserForm()
    edit_user_form = AdminEditUserForm(original_username='', original_email='')
    delete_user_form = DeleteUserForm()
    
    return render_template('admin/users.html', 
                          users=users, 
                          add_user_form=add_user_form, 
                          edit_user_form=edit_user_form, 
                          delete_user_form=delete_user_form)

@admin_required
def admin_add_user():
    form = AdminUserForm()
    
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data),
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            student_id=form.student_id.data,
            department=form.department.data,
            role=form.role.data
        )
        
        try:
            db.session.add(user)
            db.session.commit()
            flash(f'تم إنشاء المستخدم {user.username} بنجاح!', 'success')
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error adding user: {str(e)}")
            flash('حدث خطأ أثناء إضافة المستخدم. الرجاء المحاولة مرة أخرى.', 'danger')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{getattr(form, field).label.text}: {error}', 'danger')
    
    return redirect(url_for('admin_users'))

@admin_required
def admin_edit_user():
    form = AdminEditUserForm(original_username='', original_email='')
    user_id = request.form.get('user_id')
    
    if not user_id:
        flash('معرف المستخدم مفقود', 'danger')
        return redirect(url_for('admin_users'))
    
    user = User.query.get_or_404(user_id)
    form = AdminEditUserForm(original_username=user.username, original_email=user.email)
    
    if form.validate_on_submit():
        user.username = form.username.data
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        user.student_id = form.student_id.data
        user.department = form.department.data
        user.role = form.role.data
        
        if form.reset_password.data and form.password.data:
            user.password_hash = generate_password_hash(form.password.data)
        
        try:
            db.session.commit()
            flash(f'تم تحديث معلومات المستخدم {user.username} بنجاح!', 'success')
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error updating user: {str(e)}")
            flash('حدث خطأ أثناء تحديث معلومات المستخدم. الرجاء المحاولة مرة أخرى.', 'danger')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{getattr(form, field).label.text}: {error}', 'danger')
    
    return redirect(url_for('admin_users'))

@admin_required
def admin_delete_user():
    form = DeleteUserForm()
    
    if form.validate_on_submit():
        user_id = form.user_id.data
        user = User.query.get_or_404(user_id)
        
        # Prevent deleting own account
        if user.id == current_user.id:
            flash('لا يمكنك حذف حسابك الخاص!', 'danger')
            return redirect(url_for('admin_users'))
        
        try:
            db.session.delete(user)
            db.session.commit()
            flash(f'تم حذف المستخدم {user.username} بنجاح!', 'success')
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error deleting user: {str(e)}")
            flash('حدث خطأ أثناء حذف المستخدم. الرجاء المحاولة مرة أخرى.', 'danger')
    
    return redirect(url_for('admin_users'))

# Announcements Management
@admin_required
def admin_announcements():
    announcements = Announcement.query.order_by(Announcement.created_at.desc()).all()
    form = AnnouncementForm()
    
    return render_template('admin/announcements.html', announcements=announcements, form=form)

@admin_required
def admin_add_announcement():
    form = AnnouncementForm()
    
    if form.validate_on_submit():
        announcement = Announcement(
            title=form.title.data,
            content=form.content.data,
            important=form.important.data,
            author_id=current_user.id
        )
        
        try:
            db.session.add(announcement)
            db.session.commit()
            flash('تم نشر الإعلان بنجاح!', 'success')
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error adding announcement: {str(e)}")
            flash('حدث خطأ أثناء نشر الإعلان. الرجاء المحاولة مرة أخرى.', 'danger')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{getattr(form, field).label.text}: {error}', 'danger')
    
    return redirect(url_for('admin_announcements'))

@admin_required
def admin_edit_announcement(announcement_id):
    announcement = Announcement.query.get_or_404(announcement_id)
    form = AnnouncementForm()
    
    if form.validate_on_submit():
        announcement.title = form.title.data
        announcement.content = form.content.data
        announcement.important = form.important.data
        announcement.updated_at = datetime.utcnow()
        
        try:
            db.session.commit()
            flash('تم تحديث الإعلان بنجاح!', 'success')
            return redirect(url_for('admin_announcements'))
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error updating announcement: {str(e)}")
            flash('حدث خطأ أثناء تحديث الإعلان. الرجاء المحاولة مرة أخرى.', 'danger')
    
    form.title.data = announcement.title
    form.content.data = announcement.content
    form.important.data = announcement.important
    
    return render_template('admin/edit_announcement.html', form=form, announcement=announcement)

@admin_required
def admin_delete_announcement(announcement_id):
    announcement = Announcement.query.get_or_404(announcement_id)
    
    try:
        db.session.delete(announcement)
        db.session.commit()
        flash('تم حذف الإعلان بنجاح!', 'success')
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting announcement: {str(e)}")
        flash('حدث خطأ أثناء حذف الإعلان. الرجاء المحاولة مرة أخرى.', 'danger')
    
    return redirect(url_for('admin_announcements'))

# Events Management
@admin_required
def admin_events():
    events = Event.query.order_by(Event.start_time).all()
    form = EventForm()
    
    return render_template('admin/events.html', events=events, form=form)

@admin_required
def admin_add_event():
    form = EventForm()
    
    if form.validate_on_submit():
        event = Event(
            title=form.title.data,
            description=form.description.data,
            location=form.location.data,
            start_time=form.start_time.data,
            end_time=form.end_time.data,
            organizer_id=current_user.id
        )
        
        try:
            db.session.add(event)
            db.session.commit()
            flash('تم إضافة الحدث بنجاح!', 'success')
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error adding event: {str(e)}")
            flash('حدث خطأ أثناء إضافة الحدث. الرجاء المحاولة مرة أخرى.', 'danger')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{getattr(form, field).label.text}: {error}', 'danger')
    
    return redirect(url_for('admin_events'))

@admin_required
def admin_edit_event(event_id):
    event = Event.query.get_or_404(event_id)
    form = EventForm()
    
    if form.validate_on_submit():
        event.title = form.title.data
        event.description = form.description.data
        event.location = form.location.data
        event.start_time = form.start_time.data
        event.end_time = form.end_time.data
        event.updated_at = datetime.utcnow()
        
        try:
            db.session.commit()
            flash('تم تحديث الحدث بنجاح!', 'success')
            return redirect(url_for('admin_events'))
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error updating event: {str(e)}")
            flash('حدث خطأ أثناء تحديث الحدث. الرجاء المحاولة مرة أخرى.', 'danger')
    
    form.title.data = event.title
    form.description.data = event.description
    form.location.data = event.location
    form.start_time.data = event.start_time
    form.end_time.data = event.end_time
    
    return render_template('admin/edit_event.html', form=form, event=event)

@admin_required
def admin_delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    
    try:
        db.session.delete(event)
        db.session.commit()
        flash('تم حذف الحدث بنجاح!', 'success')
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting event: {str(e)}")
        flash('حدث خطأ أثناء حذف الحدث. الرجاء المحاولة مرة أخرى.', 'danger')
    
    return redirect(url_for('admin_events'))

# Course Management
@admin_required
def admin_courses():
    courses = Course.query.all()
    form = CourseForm()
    
    # Get all teachers and admins for instructor selection
    teachers = User.query.filter(User.role.in_(['teacher', 'admin'])).all()
    form.instructor_id.choices = [(teacher.id, teacher.full_name() or teacher.username) for teacher in teachers]
    
    return render_template('admin/courses.html', courses=courses, form=form)

@admin_required
def admin_add_course():
    form = CourseForm()
    
    # Get all teachers and admins for instructor selection
    teachers = User.query.filter(User.role.in_(['teacher', 'admin'])).all()
    form.instructor_id.choices = [(teacher.id, teacher.full_name() or teacher.username) for teacher in teachers]
    
    if form.validate_on_submit():
        course = Course(
            code=form.code.data,
            name=form.name.data,
            description=form.description.data,
            department=form.department.data,
            semester=form.semester.data,
            instructor_id=form.instructor_id.data
        )
        
        try:
            db.session.add(course)
            db.session.commit()
            flash(f'تم إضافة المادة الدراسية {course.code}: {course.name} بنجاح!', 'success')
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error adding course: {str(e)}")
            flash('حدث خطأ أثناء إضافة المادة الدراسية. الرجاء المحاولة مرة أخرى.', 'danger')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{getattr(form, field).label.text}: {error}', 'danger')
    
    return redirect(url_for('admin_courses'))

@admin_required
def admin_edit_course(course_id):
    course = Course.query.get_or_404(course_id)
    form = CourseForm()
    
    # Get all teachers and admins for instructor selection
    teachers = User.query.filter(User.role.in_(['teacher', 'admin'])).all()
    form.instructor_id.choices = [(teacher.id, teacher.full_name() or teacher.username) for teacher in teachers]
    
    if form.validate_on_submit():
        course.code = form.code.data
        course.name = form.name.data
        course.description = form.description.data
        course.department = form.department.data
        course.semester = form.semester.data
        course.instructor_id = form.instructor_id.data
        
        try:
            db.session.commit()
            flash(f'تم تحديث المادة الدراسية {course.code}: {course.name} بنجاح!', 'success')
            return redirect(url_for('admin_courses'))
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error updating course: {str(e)}")
            flash('حدث خطأ أثناء تحديث المادة الدراسية. الرجاء المحاولة مرة أخرى.', 'danger')
    
    form.code.data = course.code
    form.name.data = course.name
    form.description.data = course.description
    form.department.data = course.department
    form.semester.data = course.semester
    form.instructor_id.data = course.instructor_id
    
    return render_template('admin/edit_course.html', form=form, course=course)

@admin_required
def admin_delete_course(course_id):
    course = Course.query.get_or_404(course_id)
    
    try:
        db.session.delete(course)
        db.session.commit()
        flash(f'تم حذف المادة الدراسية {course.code}: {course.name} بنجاح!', 'success')
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting course: {str(e)}")
        flash('حدث خطأ أثناء حذف المادة الدراسية. الرجاء المحاولة مرة أخرى.', 'danger')
    
    return redirect(url_for('admin_courses'))

# Teacher Management
@admin_required
def admin_teachers():
    teachers = User.query.filter(User.role == 'teacher').all()
    return render_template('admin/teachers.html', teachers=teachers)

# Assignment Management
@teacher_required
def admin_assignments():
    if current_user.is_admin():
        assignments = Assignment.query.all()
        courses = Course.query.all()
    else:
        # Teachers can only see assignments for courses they teach
        teacher_courses = Course.query.filter_by(instructor_id=current_user.id).all()
        course_ids = [course.id for course in teacher_courses]
        assignments = Assignment.query.filter(Assignment.course_id.in_(course_ids)).all()
        courses = teacher_courses
    
    form = AssignmentForm()
    form.course_id.choices = [(course.id, f"{course.code}: {course.name}") for course in courses]
    
    return render_template('admin/assignments.html', assignments=assignments, form=form)

@teacher_required
def admin_add_assignment():
    form = AssignmentForm()
    
    if current_user.is_admin():
        courses = Course.query.all()
    else:
        # Teachers can only add assignments to courses they teach
        courses = Course.query.filter_by(instructor_id=current_user.id).all()
    
    form.course_id.choices = [(course.id, f"{course.code}: {course.name}") for course in courses]
    
    if form.validate_on_submit():
        assignment = Assignment(
            title=form.title.data,
            description=form.description.data,
            due_date=form.due_date.data,
            total_points=form.total_points.data,
            course_id=form.course_id.data,
            creator_id=current_user.id
        )
        
        try:
            db.session.add(assignment)
            db.session.commit()
            flash(f'تم إضافة الواجب {assignment.title} بنجاح!', 'success')
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error adding assignment: {str(e)}")
            flash('حدث خطأ أثناء إضافة الواجب. الرجاء المحاولة مرة أخرى.', 'danger')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{getattr(form, field).label.text}: {error}', 'danger')
    
    return redirect(url_for('admin_assignments'))

@teacher_required
def admin_edit_assignment(assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)
    
    # Check if user has permission to edit this assignment
    if not current_user.is_admin() and assignment.course.instructor_id != current_user.id:
        flash('ليس لديك صلاحية لتعديل هذا الواجب', 'danger')
        return redirect(url_for('admin_assignments'))
    
    form = AssignmentForm()
    
    if current_user.is_admin():
        courses = Course.query.all()
    else:
        courses = Course.query.filter_by(instructor_id=current_user.id).all()
    
    form.course_id.choices = [(course.id, f"{course.code}: {course.name}") for course in courses]
    
    if form.validate_on_submit():
        assignment.title = form.title.data
        assignment.description = form.description.data
        assignment.due_date = form.due_date.data
        assignment.total_points = form.total_points.data
        assignment.course_id = form.course_id.data
        
        try:
            db.session.commit()
            flash(f'تم تحديث الواجب {assignment.title} بنجاح!', 'success')
            return redirect(url_for('admin_assignments'))
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error updating assignment: {str(e)}")
            flash('حدث خطأ أثناء تحديث الواجب. الرجاء المحاولة مرة أخرى.', 'danger')
    
    form.title.data = assignment.title
    form.description.data = assignment.description
    form.due_date.data = assignment.due_date
    form.total_points.data = assignment.total_points
    form.course_id.data = assignment.course_id
    
    return render_template('admin/edit_assignment.html', form=form, assignment=assignment)

@teacher_required
def admin_delete_assignment(assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)
    
    # Check if user has permission to delete this assignment
    if not current_user.is_admin() and assignment.course.instructor_id != current_user.id:
        flash('ليس لديك صلاحية لحذف هذا الواجب', 'danger')
        return redirect(url_for('admin_assignments'))
    
    try:
        db.session.delete(assignment)
        db.session.commit()
        flash(f'تم حذف الواجب {assignment.title} بنجاح!', 'success')
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting assignment: {str(e)}")
        flash('حدث خطأ أثناء حذف الواجب. الرجاء المحاولة مرة أخرى.', 'danger')
    
    return redirect(url_for('admin_assignments'))

# Materials Management
@teacher_required
def admin_materials():
    if current_user.is_admin():
        materials = Material.query.all()
        courses = Course.query.all()
    else:
        # Teachers can only see materials for courses they teach
        teacher_courses = Course.query.filter_by(instructor_id=current_user.id).all()
        course_ids = [course.id for course in teacher_courses]
        materials = Material.query.filter(Material.course_id.in_(course_ids)).all()
        courses = teacher_courses
    
    form = MaterialForm()
    form.course_id.choices = [(course.id, f"{course.code}: {course.name}") for course in courses]
    
    return render_template('admin/materials.html', materials=materials, form=form)

@teacher_required
def admin_add_material():
    form = MaterialForm()
    
    if current_user.is_admin():
        courses = Course.query.all()
    else:
        # Teachers can only add materials to courses they teach
        courses = Course.query.filter_by(instructor_id=current_user.id).all()
    
    form.course_id.choices = [(course.id, f"{course.code}: {course.name}") for course in courses]
    
    if form.validate_on_submit():
        material = Material(
            title=form.title.data,
            description=form.description.data,
            material_type=form.material_type.data,
            external_link=form.external_link.data,
            course_id=form.course_id.data
        )
        
        if form.material_file.data:
            # Save the uploaded file
            filename = secure_filename(form.material_file.data.filename)
            # Create uploads directory if it doesn't exist
            os.makedirs('static/uploads/materials', exist_ok=True)
            file_path = os.path.join('static/uploads/materials', filename)
            form.material_file.data.save(file_path)
            material.file_path = file_path
        
        try:
            db.session.add(material)
            db.session.commit()
            flash(f'تم إضافة المادة التعليمية {material.title} بنجاح!', 'success')
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error adding material: {str(e)}")
            flash('حدث خطأ أثناء إضافة المادة التعليمية. الرجاء المحاولة مرة أخرى.', 'danger')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{getattr(form, field).label.text}: {error}', 'danger')
    
    return redirect(url_for('admin_materials'))

@teacher_required
def admin_edit_material(material_id):
    material = Material.query.get_or_404(material_id)
    
    # Check if user has permission to edit this material
    if not current_user.is_admin() and material.course.instructor_id != current_user.id:
        flash('ليس لديك صلاحية لتعديل هذه المادة التعليمية', 'danger')
        return redirect(url_for('admin_materials'))
    
    form = MaterialForm()
    
    if current_user.is_admin():
        courses = Course.query.all()
    else:
        courses = Course.query.filter_by(instructor_id=current_user.id).all()
    
    form.course_id.choices = [(course.id, f"{course.code}: {course.name}") for course in courses]
    
    if form.validate_on_submit():
        material.title = form.title.data
        material.description = form.description.data
        material.material_type = form.material_type.data
        material.external_link = form.external_link.data
        material.course_id = form.course_id.data
        
        if form.material_file.data:
            # Save the uploaded file
            filename = secure_filename(form.material_file.data.filename)
            # Create uploads directory if it doesn't exist
            os.makedirs('static/uploads/materials', exist_ok=True)
            file_path = os.path.join('static/uploads/materials', filename)
            form.material_file.data.save(file_path)
            material.file_path = file_path
        
        try:
            db.session.commit()
            flash(f'تم تحديث المادة التعليمية {material.title} بنجاح!', 'success')
            return redirect(url_for('admin_materials'))
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error updating material: {str(e)}")
            flash('حدث خطأ أثناء تحديث المادة التعليمية. الرجاء المحاولة مرة أخرى.', 'danger')
    
    form.title.data = material.title
    form.description.data = material.description
    form.material_type.data = material.material_type
    form.external_link.data = material.external_link
    form.course_id.data = material.course_id
    
    return render_template('admin/edit_material.html', form=form, material=material)

@teacher_required
def admin_delete_material(material_id):
    material = Material.query.get_or_404(material_id)
    
    # Check if user has permission to delete this material
    if not current_user.is_admin() and material.course.instructor_id != current_user.id:
        flash('ليس لديك صلاحية لحذف هذه المادة التعليمية', 'danger')
        return redirect(url_for('admin_materials'))
    
    try:
        # If there's a file, delete it
        if material.file_path and os.path.exists(material.file_path):
            os.remove(material.file_path)
        
        db.session.delete(material)
        db.session.commit()
        flash(f'تم حذف المادة التعليمية {material.title} بنجاح!', 'success')
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting material: {str(e)}")
        flash('حدث خطأ أثناء حذف المادة التعليمية. الرجاء المحاولة مرة أخرى.', 'danger')
    
    return redirect(url_for('admin_materials'))

# System Settings
@admin_required
def admin_settings():
    # TODO: Implement system settings
    return render_template('admin/settings.html')