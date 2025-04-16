from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, ValidationError
from models import User

class LoginForm(FlaskForm):
    username_or_email = StringField('اسم المستخدم أو البريد الإلكتروني', validators=[DataRequired()])
    password = PasswordField('كلمة المرور', validators=[DataRequired()])
    remember = BooleanField('تذكرني')
    submit = SubmitField('تسجيل الدخول')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('كلمة المرور الحالية', validators=[DataRequired()])
    password = PasswordField('كلمة المرور الجديدة', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('تأكيد كلمة المرور الجديدة', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('تغيير كلمة المرور')

class RegistrationForm(FlaskForm):
    username = StringField('اسم المستخدم', validators=[DataRequired(), Length(min=4, max=64)])
    email = StringField('البريد الإلكتروني', validators=[DataRequired(), Email()])
    password = PasswordField('كلمة المرور', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('تأكيد كلمة المرور', validators=[DataRequired(), EqualTo('password')])
    first_name = StringField('الاسم الأول', validators=[Optional(), Length(max=64)])
    last_name = StringField('الاسم الأخير', validators=[Optional(), Length(max=64)])
    student_id = StringField('الرقم الطلابي', validators=[Optional(), Length(max=20)])
    department = StringField('القسم أو التخصص', validators=[Optional(), Length(max=100)])
    submit = SubmitField('تسجيل')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('اسم المستخدم مستخدم بالفعل. الرجاء اختيار اسم آخر.')
            
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data.lower()).first()
        if user:
            raise ValidationError('البريد الإلكتروني مستخدم بالفعل. الرجاء استخدام بريد آخر.')

class PasswordResetRequestForm(FlaskForm):
    email = StringField('البريد الإلكتروني', validators=[DataRequired(), Email()])
    submit = SubmitField('طلب إعادة تعيين كلمة المرور')

class PasswordResetForm(FlaskForm):
    password = PasswordField('كلمة المرور الجديدة', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('تأكيد كلمة المرور', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('إعادة تعيين كلمة المرور')

class UserProfileForm(FlaskForm):
    username = StringField('اسم المستخدم', validators=[DataRequired(), Length(min=4, max=64)])
    first_name = StringField('الاسم الأول', validators=[Optional(), Length(max=64)])
    last_name = StringField('الاسم الأخير', validators=[Optional(), Length(max=64)])
    student_id = StringField('الرقم الطلابي', validators=[Optional(), Length(max=20)])
    department = StringField('القسم أو التخصص', validators=[Optional(), Length(max=100)])
    submit = SubmitField('تحديث الملف الشخصي')
    
    def __init__(self, original_username, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        
    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('اسم المستخدم مستخدم بالفعل. الرجاء اختيار اسم آخر.')