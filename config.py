"""
Configuration settings for the Doctor Appointment System.
Uses environment variables for sensitive data; falls back to defaults for development.
"""
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class Config:
    """Base configuration."""
    # Secret key for session management - use env in production
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    # SQLite by default in instance folder; override with DATABASE_URL for production
    basedir = os.path.abspath(os.path.dirname(__file__))
    instance_path = os.path.join(basedir, 'instance')
    os.makedirs(instance_path, exist_ok=True)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(instance_path, 'doctor_appointment.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # File upload settings (e.g. doctor profile images)
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    # WTF CSRF
    WTF_CSRF_ENABLED = True
