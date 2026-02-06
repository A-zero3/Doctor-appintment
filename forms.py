"""
Flask-WTF form classes for the Doctor Appointment System.
Registration, login, appointment booking, contact, and profile editing.
"""
from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, BooleanField, SubmitField, TextAreaField,
    SelectField, DateField, IntegerField
)
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, NumberRange
from datetime import date


class RegistrationForm(FlaskForm):
    """User registration: patient or doctor (doctor may require admin approval in production)."""
    username = StringField('Username', validators=[
        DataRequired(message='Username is required'),
        Length(min=3, max=80, message='Username must be between 3 and 80 characters')
    ])
    email = StringField('Email', validators=[
        DataRequired(message='Email is required'),
        Email(message='Please enter a valid email address')
    ])
    full_name = StringField('Full Name', validators=[
        DataRequired(message='Full name is required'),
        Length(max=120)
    ])
    phone_number = StringField('Phone Number', validators=[Optional(), Length(max=20)])
    date_of_birth = DateField('Date of Birth', validators=[Optional()], format='%Y-%m-%d')
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required'),
        Length(min=8, message='Password must be at least 8 characters'),
        EqualTo('confirm_password', message='Passwords must match')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired()])
    user_role = SelectField('Register as', choices=[
        ('patient', 'Patient'),
        ('doctor', 'Doctor (requires admin approval in production)')
    ], default='patient')
    submit = SubmitField('Register')


class LoginForm(FlaskForm):
    """Login form with username and password."""
    username = StringField('Username', validators=[DataRequired(message='Username is required')])
    password = PasswordField('Password', validators=[DataRequired(message='Password is required')])
    remember_me = BooleanField('Remember Me', default=False)
    submit = SubmitField('Log In')


class BookAppointmentForm(FlaskForm):
    """Appointment booking: doctor, date, time, reason for visit."""
    doctor_id = SelectField('Doctor', coerce=int, validators=[DataRequired(message='Please select a doctor')])
    appointment_date = DateField('Appointment Date', validators=[
        DataRequired(message='Please select a date')
    ], format='%Y-%m-%d')
    appointment_time = StringField('Time Slot', validators=[DataRequired(message='Please select a time')])
    reason_for_visit = TextAreaField('Reason for Visit', validators=[
        DataRequired(message='Please briefly describe your reason for the visit'),
        Length(max=1000)
    ])
    submit = SubmitField('Book Appointment')


class ContactForm(FlaskForm):
    """Contact page form: name, email, phone, subject, message."""
    name = StringField('Name', validators=[
        DataRequired(message='Name is required'),
        Length(max=120)
    ])
    email = StringField('Email', validators=[
        DataRequired(message='Email is required'),
        Email(message='Please enter a valid email address')
    ])
    phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    subject = StringField('Subject', validators=[
        DataRequired(message='Subject is required'),
        Length(max=200)
    ])
    message = TextAreaField('Message', validators=[
        DataRequired(message='Message is required'),
        Length(max=5000)
    ])
    submit = SubmitField('Send Message')


class ProfileEditForm(FlaskForm):
    """Patient/doctor profile edit: full name, email, phone (no password change here)."""
    full_name = StringField('Full Name', validators=[
        DataRequired(message='Full name is required'),
        Length(max=120)
    ])
    email = StringField('Email', validators=[
        DataRequired(message='Email is required'),
        Email(message='Please enter a valid email address')
    ])
    phone_number = StringField('Phone Number', validators=[Optional(), Length(max=20)])
    submit = SubmitField('Save Changes')


class DoctorNoteForm(FlaskForm):
    """Doctor adds or updates notes for an appointment."""
    notes = TextAreaField('Notes', validators=[Optional(), Length(max=2000)])
    submit = SubmitField('Save Notes')
