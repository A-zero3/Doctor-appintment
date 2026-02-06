"""
SQLAlchemy database models for the Doctor Appointment System.
Defines Users, Doctors, Appointments, and ContactSubmission with proper relationships.
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """
    User model: patients, doctors, and administrators.
    user_role: 'patient', 'doctor', or 'admin'.
    """
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    user_role = db.Column(db.String(20), nullable=False, default='patient')  # patient, doctor, admin
    full_name = db.Column(db.String(120), nullable=True)
    phone_number = db.Column(db.String(20), nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    account_creation = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)

    # One user (patient) can have many appointments
    appointments_as_patient = db.relationship(
        'Appointment', backref='patient_user', lazy='dynamic',
        foreign_keys='Appointment.patient_id', cascade='all, delete-orphan'
    )
    # One-to-one: a user who is a doctor has one Doctor profile
    doctor_profile = db.relationship(
        'Doctor', backref='user', uselist=False, lazy='joined',
        foreign_keys='Doctor.user_id', cascade='all, delete-orphan'
    )

    def get_id(self):
        """Flask-Login requires get_id to return a string."""
        return str(self.user_id)

    def set_password(self, password):
        """Hash and store password using Werkzeug."""
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        """Verify password against stored hash."""
        return check_password_hash(self.password_hash, password)

    @property
    def is_patient(self):
        return self.user_role == 'patient'

    @property
    def is_doctor(self):
        return self.user_role == 'doctor'

    @property
    def is_admin(self):
        return self.user_role == 'admin'


class Doctor(db.Model):
    """
    Doctor model: detailed info for medical professionals.
    Each doctor is linked to one User account via user_id.
    """
    __tablename__ = 'doctors'
    doctor_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False, unique=True)
    specialization = db.Column(db.String(100), nullable=False)  # Cardiology, Dermatology, etc.
    qualifications = db.Column(db.String(500), nullable=True)
    years_of_experience = db.Column(db.Integer, nullable=True)
    consultation_fee = db.Column(db.Numeric(10, 2), nullable=True)
    available_days = db.Column(db.String(200), nullable=True)  # e.g. "Mon,Tue,Wed,Thu,Fri"
    available_time_slots = db.Column(db.String(500), nullable=True)  # e.g. "09:00,10:00,11:00,14:00,15:00"
    about_text = db.Column(db.Text, nullable=True)
    profile_image_filename = db.Column(db.String(255), nullable=True)

    # One doctor has many appointments
    appointments = db.relationship(
        'Appointment', backref='doctor', lazy='dynamic',
        foreign_keys='Appointment.doctor_id', cascade='all, delete-orphan'
    )


class Appointment(db.Model):
    """
    Appointment model: connects patients with doctors.
    status: pending, confirmed, completed, cancelled.
    """
    __tablename__ = 'appointments'
    appointment_id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.doctor_id'), nullable=False)
    appointment_date = db.Column(db.Date, nullable=False)
    appointment_time = db.Column(db.String(20), nullable=False)  # e.g. "09:00"
    status = db.Column(db.String(20), nullable=False, default='pending')
    reason_for_visit = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)  # doctor notes after visit
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ContactSubmission(db.Model):
    """
    Contact form submissions for general inquiries (name, email, phone, subject, message).
    """
    __tablename__ = 'contact_submissions'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
