from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField, IntegerField, HiddenField, DateTimeField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, ValidationError
from models import User

class AdminUserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[EqualTo('password')])
    first_name = StringField('First Name', validators=[Optional(), Length(max=64)])
    last_name = StringField('Last Name', validators=[Optional(), Length(max=64)])
    student_id = StringField('Student ID', validators=[Optional(), Length(max=20)])
    department = StringField('Department', validators=[Optional(), Length(max=100)])
    role = SelectField('Role', choices=[('student', 'طالب'), ('teacher', 'معلم'), ('admin', 'مشرف')])
    submit = SubmitField('Submit')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username is already taken. Please choose a different one.')
            
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data.lower()).first()
        if user:
            raise ValidationError('Email is already registered. Please use a different one.')

class AdminEditUserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    first_name = StringField('First Name', validators=[Optional(), Length(max=64)])
    last_name = StringField('Last Name', validators=[Optional(), Length(max=64)])
    student_id = StringField('Student ID', validators=[Optional(), Length(max=20)])
    department = StringField('Department', validators=[Optional(), Length(max=100)])
    role = SelectField('Role', choices=[('student', 'طالب'), ('teacher', 'معلم'), ('admin', 'مشرف')])
    reset_password = BooleanField('Reset Password')
    password = PasswordField('New Password', validators=[Optional(), Length(min=8)])
    confirm_password = PasswordField('Confirm New Password', validators=[EqualTo('password')])
    submit = SubmitField('Save Changes')
    
    def __init__(self, original_username, original_email, *args, **kwargs):
        super(AdminEditUserForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email
        
    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Username is already taken. Please choose a different one.')
                
    def validate_email(self, email):
        if email.data.lower() != self.original_email.lower():
            user = User.query.filter_by(email=email.data.lower()).first()
            if user:
                raise ValidationError('Email is already registered. Please use a different one.')

class DeleteUserForm(FlaskForm):
    user_id = HiddenField('User ID', validators=[DataRequired()])
    submit = SubmitField('Delete')

class AnnouncementForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=150)])
    content = TextAreaField('Content', validators=[DataRequired()])
    important = BooleanField('Mark as Important')
    submit = SubmitField('Submit')

class EventForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=150)])
    description = TextAreaField('Description', validators=[DataRequired()])
    location = StringField('Location', validators=[DataRequired(), Length(max=200)])
    start_time = DateTimeField('Start Time', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    end_time = DateTimeField('End Time', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    submit = SubmitField('Submit')

class CourseForm(FlaskForm):
    code = StringField('Course Code', validators=[DataRequired(), Length(max=20)])
    name = StringField('Course Name', validators=[DataRequired(), Length(max=150)])
    description = TextAreaField('Description', validators=[Optional()])
    department = StringField('Department', validators=[Optional(), Length(max=100)])
    semester = StringField('Semester', validators=[Optional(), Length(max=50)])
    instructor_id = SelectField('Instructor', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Submit')

class MaterialForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=150)])
    description = TextAreaField('Description', validators=[Optional()])
    material_file = FileField('Upload File', validators=[Optional(), FileAllowed(['pdf', 'docx', 'pptx', 'txt', 'jpg', 'png', 'zip'], 'Only specific file types are allowed!')])
    external_link = StringField('External Link', validators=[Optional(), Length(max=500)])
    material_type = SelectField('Material Type', choices=[
        ('pdf', 'PDF Document'),
        ('document', 'Word Document'),
        ('presentation', 'Presentation'),
        ('video', 'Video Link'),
        ('link', 'External Link'),
        ('other', 'Other')
    ])
    course_id = SelectField('Course', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Submit')

class AssignmentForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=150)])
    description = TextAreaField('Description', validators=[DataRequired()])
    due_date = DateTimeField('Due Date', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    total_points = IntegerField('Total Points', default=100, validators=[DataRequired()])
    course_id = SelectField('Course', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Submit')

class AssignmentSubmissionForm(FlaskForm):
    submission_text = TextAreaField('Submission Text', validators=[Optional()])
    submission_file = FileField('Upload File', validators=[Optional(), FileAllowed(['pdf', 'docx', 'txt', 'zip'], 'Only specific file types are allowed!')])
    submit = SubmitField('Submit Assignment')

class GradeSubmissionForm(FlaskForm):
    score = IntegerField('Score', validators=[DataRequired()])
    feedback = TextAreaField('Feedback', validators=[Optional()])
    submit = SubmitField('Submit Grade')