"""
Authentication Forms
"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
import re


class LoginForm(FlaskForm):
    """Login form"""
    username = StringField('Username or Email', 
                          validators=[DataRequired(), Length(min=3, max=120)],
                          render_kw={'placeholder': 'Enter username or email'})
    password = PasswordField('Password', 
                            validators=[DataRequired()],
                            render_kw={'placeholder': 'Enter password'})
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Login')


class ChangePasswordForm(FlaskForm):
    """Change password form"""
    old_password = PasswordField('Current Password', 
                                validators=[DataRequired()],
                                render_kw={'placeholder': 'Enter current password'})
    new_password = PasswordField('New Password', 
                                validators=[DataRequired(), Length(min=8, max=128)],
                                render_kw={'placeholder': 'Enter new password'})
    confirm_password = PasswordField('Confirm New Password', 
                                    validators=[DataRequired(), EqualTo('new_password', message='Passwords must match')],
                                    render_kw={'placeholder': 'Confirm new password'})
    submit = SubmitField('Change Password')
    
    def validate_new_password(self, field):
        """Validate password strength"""
        password = field.data
        
        # Check for at least one uppercase letter
        if not re.search(r'[A-Z]', password):
            raise ValidationError('Password must contain at least one uppercase letter')
        
        # Check for at least one lowercase letter
        if not re.search(r'[a-z]', password):
            raise ValidationError('Password must contain at least one lowercase letter')
        
        # Check for at least one digit
        if not re.search(r'\d', password):
            raise ValidationError('Password must contain at least one number')
        
        # Check for at least one special character
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError('Password must contain at least one special character')


class ProfileForm(FlaskForm):
    """User profile form"""
    full_name = StringField('Full Name', 
                           validators=[Length(max=120)],
                           render_kw={'placeholder': 'Enter your full name'})
    department = StringField('Department', 
                            validators=[Length(max=100)],
                            render_kw={'placeholder': 'Enter your department'})
    theme = SelectField('Theme', 
                       choices=[('light', 'Light'), ('dark', 'Dark')],
                       default='light')
    language = SelectField('Language', 
                          choices=[('en', 'English'), ('bem', 'Bemba'), ('ny', 'Nyanja')],
                          default='en')
    timezone = SelectField('Timezone', 
                          choices=[('Africa/Lusaka', 'Africa/Lusaka (CAT)')],
                          default='Africa/Lusaka')
    notifications_enabled = BooleanField('Enable Notifications')
    submit = SubmitField('Update Profile')


class ForgotPasswordForm(FlaskForm):
    """Forgot password form"""
    email = StringField('Email', 
                       validators=[DataRequired(), Email(), Length(max=120)],
                       render_kw={'placeholder': 'Enter your email address'})
    submit = SubmitField('Send Reset Link')


class ResetPasswordForm(FlaskForm):
    """Reset password form"""
    password = PasswordField('New Password', 
                           validators=[DataRequired(), Length(min=8, max=128)],
                           render_kw={'placeholder': 'Enter new password'})
    confirm_password = PasswordField('Confirm Password', 
                                    validators=[DataRequired(), EqualTo('password', message='Passwords must match')],
                                    render_kw={'placeholder': 'Confirm new password'})
    submit = SubmitField('Reset Password')
    
    def validate_password(self, field):
        """Validate password strength"""
        password = field.data
        
        # Check for at least one uppercase letter
        if not re.search(r'[A-Z]', password):
            raise ValidationError('Password must contain at least one uppercase letter')
        
        # Check for at least one lowercase letter
        if not re.search(r'[a-z]', password):
            raise ValidationError('Password must contain at least one lowercase letter')
        
        # Check for at least one digit
        if not re.search(r'\d', password):
            raise ValidationError('Password must contain at least one number')
        
        # Check for at least one special character
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError('Password must contain at least one special character')


class TwoFactorForm(FlaskForm):
    """Two-factor authentication form"""
    code = StringField('Verification Code', 
                      validators=[DataRequired(), Length(min=6, max=6)],
                      render_kw={'placeholder': 'Enter 6-digit code'})
    submit = SubmitField('Verify')