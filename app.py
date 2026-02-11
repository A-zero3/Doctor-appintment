"""
Doctor Appointment System - Flask application entry point.
Handles all routes, authentication, and CRUD for appointments, doctors, and contact.
"""
import os
import uuid
from datetime import datetime, date, timedelta
from functools import wraps
from flask_wtf.csrf import CSRFProtect
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename

from config import Config
from models import db, User, Doctor, Appointment, ContactSubmission
from forms import (
    RegistrationForm, LoginForm, BookAppointmentForm, ContactForm,
    ProfileEditForm, DoctorNoteForm
)

app = Flask(__name__)
app.config.from_object(Config)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# Add this line:
csrf = CSRFProtect(app)


def allowed_file(filename):
    """Check if uploaded file has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def get_secure_filename_for_upload(original_filename):
    """Generate a unique, secure filename for uploads."""
    ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'jpg'
    return f"{uuid.uuid4().hex}.{ext}"


def patient_required(f):
    """Decorator: allow access only to authenticated patients."""
    @wraps(f)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in as a patient to access this page.', 'warning')
            return redirect(url_for('login', next=request.url))
        if current_user.user_role != 'patient':
            flash('This page is for patients only.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_view


def doctor_required(f):
    """Decorator: allow access only to authenticated doctors."""
    @wraps(f)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access the doctor dashboard.', 'warning')
            return redirect(url_for('login', next=request.url))
        if current_user.user_role != 'doctor':
            flash('You do not have permission to access the doctor dashboard.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_view


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login session management."""
    return User.query.get(int(user_id)) if user_id else None


# ---------- Public routes ----------

@app.route('/')
def index():
    """Home page: hero, intro, stats, featured doctors."""
    featured = Doctor.query.limit(4).all()
    return render_template('home.html', featured=featured)


@app.route('/doctors')
def doctors():
    """Doctors page: all doctors in a card grid, filterable by specialization."""
    specialization_filter = request.args.get('specialization', '').strip()
    search_query = request.args.get('q', '').strip()
    query = Doctor.query
    if specialization_filter:
        query = query.filter(Doctor.specialization == specialization_filter)
    if search_query:
        # Search by doctor name (via user) or specialization
        query = query.join(User, Doctor.user_id == User.user_id).filter(
            db.or_(
                User.full_name.ilike(f'%{search_query}%'),
                User.username.ilike(f'%{search_query}%'),
                Doctor.specialization.ilike(f'%{search_query}%')
            )
        )
    doctors_list = query.all()
    specializations = db.session.query(Doctor.specialization).distinct().all()
    specializations = [s[0] for s in specializations if s[0]]
    return render_template('doctors.html', doctors_list=doctors_list, specializations=specializations,
                           current_spec=specialization_filter, search_q=search_query)


@app.route('/about')
def about_page():
    """About page: practice history, mission, facilities, team."""
    return render_template('about.html')


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact page: form with name, email, phone, subject, message; store in DB."""
    form = ContactForm()
    if form.validate_on_submit():
        try:
            submission = ContactSubmission(
                name=form.name.data.strip(),
                email=form.email.data.strip(),
                phone=(form.phone.data or '').strip() or None,
                subject=form.subject.data.strip(),
                message=form.message.data.strip()
            )
            db.session.add(submission)
            db.session.commit()
            flash('Your message has been sent. We will get back to you soon.', 'success')
            return redirect(url_for('contact'))
        except Exception as e:
            db.session.rollback()
            app.logger.exception(e)
            flash('Something went wrong. Please try again.', 'danger')
    return render_template('contact.html', form=form)


# ---------- Auth: combined login / register ----------

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login: verify credentials and establish session."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard_redirect'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            user.last_login = datetime.utcnow()
            db.session.commit()
            login_user(user, remember=form.remember_me.data)
            next_page = request.form.get('next') or request.args.get('next') or url_for('index')
            flash(f'Welcome back, {user.full_name or user.username}!', 'success')
            return redirect(next_page)
        flash('Invalid username or password.', 'danger')
    return render_template('login.html', form=form, active_tab='login')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registration: create new patient or doctor account."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard_redirect'))
    form = RegistrationForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already taken.', 'danger')
            return render_template('login.html', form=LoginForm(), register_form=form, active_tab='register')
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered.', 'danger')
            return render_template('login.html', form=LoginForm(), register_form=form, active_tab='register')
        role = form.user_role.data if form.user_role.data in ('patient', 'doctor') else 'patient'
        user = User(
            username=form.username.data,
            email=form.email.data.strip(),
            full_name=form.full_name.data.strip(),
            phone_number=(form.phone_number.data or '').strip() or None,
            date_of_birth=form.date_of_birth.data,
            user_role=role
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        if role == 'doctor':
            # Create a minimal Doctor profile; admin can fill details or doctor can edit later
            doctor = Doctor(
                user_id=user.user_id,
                specialization='General Practice',
                available_days='Mon,Tue,Wed,Thu,Fri',
                available_time_slots='09:00,10:00,11:00,14:00,15:00',
                about_text='Doctor profile - update your details in the dashboard.'
            )
            db.session.add(doctor)
            db.session.commit()
        flash('Account created successfully. You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('login.html', form=LoginForm(), register_form=form, active_tab='register')


@app.route('/logout')
@login_required
def logout():
    """Log out the current user."""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


def dashboard_redirect():
    """Send user to the appropriate dashboard based on role."""
    if current_user.user_role == 'patient':
        return redirect(url_for('patient_dashboard'))
    if current_user.user_role == 'doctor':
        return redirect(url_for('doctor_dashboard'))
    return redirect(url_for('index'))


# ---------- Book Appointment (patient only) ----------

@app.route('/book', methods=['GET', 'POST'])
@login_required
@patient_required
def book_appointment():
    """Book appointment: doctor selection, date, time, reason. Only for patients."""
    min_date = (date.today() + timedelta(days=1)).isoformat()
    form = BookAppointmentForm()
    # Populate doctor choices from database
    form.doctor_id.choices = [(0, '-- Select a doctor --')] + [
        (d.doctor_id, f"Dr. {d.user.full_name or d.user.username} ({d.specialization})")
        for d in Doctor.query.all()
    ]

    preselected_doctor_id = request.args.get('doctor_id', type=int)
    if preselected_doctor_id and request.method == 'GET':
        doc = Doctor.query.get(preselected_doctor_id)
        if doc:
            form.doctor_id.data = preselected_doctor_id

    if form.validate_on_submit():
        doctor_id = form.doctor_id.data
        appointment_date = form.appointment_date.data
        appointment_time = form.appointment_time.data
        reason = form.reason_for_visit.data.strip()

        doctor = Doctor.query.get(doctor_id)
        if not doctor:
            flash('Invalid doctor selected.', 'danger')
            return render_template('book_appointment.html', form=form, min_date=min_date)

        # Server-side: check date is in future
        if appointment_date < date.today():
            flash('Appointment date must be in the future.', 'danger')
            return render_template('book_appointment.html', form=form, min_date=min_date)

        # Check doctor has that day and time
        days_str = (doctor.available_days or '').strip()
        slots_str = (doctor.available_time_slots or '').strip()
        day_name = appointment_date.strftime('%a')  # Mon, Tue, ...
        if day_name not in days_str or appointment_time not in [s.strip() for s in slots_str.split(',') if s.strip()]:
            flash('Selected date or time is not available for this doctor.', 'danger')
            return render_template('book_appointment.html', form=form, min_date=min_date)

        # Check slot not already taken
        existing = Appointment.query.filter_by(
            doctor_id=doctor_id,
            appointment_date=appointment_date,
            appointment_time=appointment_time
        ).filter(Appointment.status.in_(['pending', 'confirmed'])).first()
        if existing:
            flash('This time slot is no longer available. Please choose another.', 'danger')
            return render_template('book_appointment.html', form=form, min_date=min_date)

        # Check patient doesn't have another appointment at same time
        existing_patient = Appointment.query.filter_by(
            patient_id=current_user.user_id,
            appointment_date=appointment_date,
            appointment_time=appointment_time
        ).filter(Appointment.status.in_(['pending', 'confirmed'])).first()
        if existing_patient:
            flash('You already have an appointment at this date and time.', 'danger')
            return render_template('book_appointment.html', form=form, min_date=min_date)

        try:
            apt = Appointment(
                patient_id=current_user.user_id,
                doctor_id=doctor_id,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                status='pending',
                reason_for_visit=reason
            )
            db.session.add(apt)
            db.session.commit()
            flash('Your appointment has been booked successfully. You will receive a confirmation.', 'success')
            return redirect(url_for('patient_dashboard'))
        except Exception as e:
            db.session.rollback()
            app.logger.exception(e)
            flash('Could not create appointment. Please try again.', 'danger')

    return render_template('book_appointment.html', form=form, min_date=min_date)


# ---------- API: available time slots (for AJAX) ----------

@app.route('/api/doctors/<int:doctor_id>/available-slots')
def api_available_slots(doctor_id):
    """Return available time slots for a doctor on a given date (query param: date=YYYY-MM-DD)."""
    doctor = Doctor.query.get_or_404(doctor_id)
    date_str = request.args.get('date')
    if not date_str:
        return jsonify({'success': False, 'error': 'Missing date parameter'}), 400
    try:
        appointment_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid date format'}), 400
    if appointment_date < date.today():
        return jsonify({'success': True, 'slots': []})

    day_name = appointment_date.strftime('%a')
    days_str = (doctor.available_days or '').strip()
    if day_name not in days_str:
        return jsonify({'success': True, 'slots': []})

    all_slots = [s.strip() for s in (doctor.available_time_slots or '').split(',') if s.strip()]
    taken = set(
        a.appointment_time for a in
        Appointment.query.filter_by(
            doctor_id=doctor_id,
            appointment_date=appointment_date
        ).filter(Appointment.status.in_(['pending', 'confirmed'])).all()
    )
    available = [s for s in all_slots if s not in taken]
    return jsonify({'success': True, 'slots': available})


# ---------- Patient Dashboard ----------

@app.route('/dashboard')
@login_required
def patient_dashboard():
    """Patient dashboard: only for patients; shows upcoming/past appointments and profile."""
    if current_user.user_role != 'patient':
        return redirect(url_for('doctor_dashboard'))
    upcoming = Appointment.query.filter_by(patient_id=current_user.user_id).filter(
        Appointment.appointment_date >= date.today(),
        Appointment.status.in_(['pending', 'confirmed'])
    ).order_by(Appointment.appointment_date, Appointment.appointment_time).all()
    past = Appointment.query.filter_by(patient_id=current_user.user_id).filter(
        db.or_(
            Appointment.appointment_date < date.today(),
            Appointment.status.in_(['completed', 'cancelled'])
        )
    ).order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc()).all()
    return render_template('patient_dashboard.html', upcoming=upcoming, past=past)


@app.route('/dashboard/profile', methods=['GET', 'POST'])
@login_required
def profile_edit():
    """Edit current user profile (full name, email, phone)."""
    form = ProfileEditForm(obj=current_user)
    if form.validate_on_submit():
        current_user.full_name = form.full_name.data.strip()
        current_user.email = form.email.data.strip()
        current_user.phone_number = (form.phone_number.data or '').strip() or None
        db.session.commit()
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('patient_dashboard') if current_user.user_role == 'patient' else url_for('doctor_dashboard'))
    return render_template('profile_edit.html', form=form)


@app.route('/appointment/<int:appointment_id>/cancel', methods=['POST'])
@login_required
def cancel_appointment(appointment_id):
    """Cancel an appointment (patient: own only; doctor: their appointments)."""
    apt = Appointment.query.get_or_404(appointment_id)
    if current_user.user_role == 'patient':
        if apt.patient_id != current_user.user_id:
            flash('You can only cancel your own appointments.', 'danger')
            return redirect(url_for('patient_dashboard'))
    elif current_user.user_role == 'doctor':
        if apt.doctor_id != current_user.doctor_profile.doctor_id:
            flash('You can only cancel appointments for your schedule.', 'danger')
            return redirect(url_for('doctor_dashboard'))
    else:
        flash('Permission denied.', 'danger')
        return redirect(url_for('index'))

    if apt.status in ('cancelled', 'completed'):
        flash('This appointment cannot be cancelled.', 'warning')
    else:
        apt.status = 'cancelled'
        apt.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Appointment cancelled.', 'success')

    if current_user.user_role == 'patient':
        return redirect(url_for('patient_dashboard'))
    return redirect(url_for('doctor_dashboard'))


# ---------- Doctor Dashboard ----------

@app.route('/doctor-dashboard')
@login_required
@doctor_required
def doctor_dashboard():
    """Doctor dashboard: appointments for this doctor, stats, add notes, mark completed."""
    doctor = current_user.doctor_profile
    if not doctor:
        flash('Doctor profile not found.', 'danger')
        return redirect(url_for('index'))

    appointments = Appointment.query.filter_by(doctor_id=doctor.doctor_id).filter(
        Appointment.status.in_(['pending', 'confirmed'])
    ).order_by(Appointment.appointment_date, Appointment.appointment_time).all()

    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    month_start = today.replace(day=1)
    next_month = month_start + timedelta(days=32)
    month_end = next_month.replace(day=1) - timedelta(days=1)

    count_week = Appointment.query.filter_by(doctor_id=doctor.doctor_id).filter(
        Appointment.appointment_date >= week_start,
        Appointment.appointment_date <= week_end,
        Appointment.status.in_(['pending', 'confirmed'])
    ).count()
    count_month = Appointment.query.filter_by(doctor_id=doctor.doctor_id).filter(
        Appointment.appointment_date >= month_start,
        Appointment.appointment_date <= month_end,
        Appointment.status.in_(['pending', 'confirmed'])
    ).count()

    return render_template('doctor_dashboard.html', appointments=appointments,
                           count_week=count_week, count_month=count_month)


@app.route('/appointment/<int:appointment_id>/notes', methods=['GET', 'POST'])
@login_required
@doctor_required
def appointment_notes(appointment_id):
    """Doctor adds or updates notes for an appointment."""
    apt = Appointment.query.get_or_404(appointment_id)
    if apt.doctor_id != current_user.doctor_profile.doctor_id:
        flash('You can only add notes to your own appointments.', 'danger')
        return redirect(url_for('doctor_dashboard'))

    form = DoctorNoteForm(obj=apt)
    if form.validate_on_submit():
        apt.notes = (form.notes.data or '').strip() or None
        apt.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Notes saved.', 'success')
        return redirect(url_for('doctor_dashboard'))
    return render_template('appointment_notes.html', form=form, appointment=apt)


@app.route('/appointment/<int:appointment_id>/complete', methods=['POST'])
@login_required
@doctor_required
def complete_appointment(appointment_id):
    """Mark an appointment as completed."""
    apt = Appointment.query.get_or_404(appointment_id)
    if apt.doctor_id != current_user.doctor_profile.doctor_id:
        flash('Permission denied.', 'danger')
        return redirect(url_for('doctor_dashboard'))
    apt.status = 'completed'
    apt.updated_at = datetime.utcnow()
    db.session.commit()
    flash('Appointment marked as completed.', 'success')
    return redirect(url_for('doctor_dashboard'))


# ---------- Contact form AJAX (optional) ----------

@app.route('/api/contact', methods=['POST'])
def api_contact():
    """Submit contact form via AJAX; returns JSON."""
    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    email = (data.get('email') or '').strip()
    phone = (data.get('phone') or '').strip()
    subject = (data.get('subject') or '').strip()
    message = (data.get('message') or '').strip()
    if not name or not email or not subject or not message:
        return jsonify({'success': False, 'error': 'All required fields must be filled.'}), 400
    if '@' not in email or '.' not in email:
        return jsonify({'success': False, 'error': 'Please enter a valid email address.'}), 400
    try:
        submission = ContactSubmission(
            name=name, email=email, phone=phone or None, subject=subject, message=message
        )
        db.session.add(submission)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Your message has been sent.'})
    except Exception as e:
        db.session.rollback()
        app.logger.exception(e)
        return jsonify({'success': False, 'error': 'Could not send message. Please try again.'}), 500


# ---------- Error handlers ----------

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(e):
    db.session.rollback()
    return render_template('500.html'), 500


# ---------- Init DB and seed ----------

def init_db_and_seed():
    """Create tables and seed sample doctors and an admin user if none exist."""
    with app.app_context():
        db.create_all()
        # Seed doctors: create users + doctor profiles if no doctors exist
        if Doctor.query.first():
            return
        # Create doctor users and their Doctor profiles
        specializations_data = [
            ('dr_smith', 'Dr. Sarah Smith', 'Cardiology', 'MD, FACC', 15, 150.00,
             'Mon,Tue,Wed,Thu', '09:00,10:00,11:00,14:00,15:00',
             'Board-certified cardiologist with expertise in preventive care and heart disease management.'),
            ('dr_jones', 'Dr. Michael Jones', 'Dermatology', 'MD, FAAD', 10, 120.00,
             'Mon,Wed,Fri', '09:00,10:00,11:00',
             'Specializing in medical and cosmetic dermatology. Committed to skin health for all ages.'),
            ('dr_williams', 'Dr. Emily Williams', 'Pediatrics', 'MD, FAAP', 12, 100.00,
             'Tue,Thu,Fri', '08:00,09:00,10:00,11:00,14:00',
             'Caring for children from birth through adolescence. Focus on preventive care and family support.'),
            ('dr_brown', 'Dr. James Brown', 'General Practice', 'MD, Family Medicine', 20, 90.00,
             'Mon,Tue,Wed,Thu,Fri', '08:00,09:00,10:00,11:00,14:00,15:00',
             'Experienced family physician providing comprehensive care for all ages.'),
        ]
        for username, full_name, spec, qual, yrs, fee, days, slots, about in specializations_data:
            if User.query.filter_by(username=username).first():
                continue
            user = User(
                username=username,
                email=f'{username}@clinic.example.com',
                full_name=full_name,
                user_role='doctor'
            )
            user.set_password('doctor123')
            db.session.add(user)
            db.session.flush()
            doctor = Doctor(
                user_id=user.user_id,
                specialization=spec,
                qualifications=qual,
                years_of_experience=yrs,
                consultation_fee=fee,
                available_days=days,
                available_time_slots=slots,
                about_text=about
            )
            db.session.add(doctor)
        # One patient for testing
        if not User.query.filter_by(username='patient').first():
            patient = User(
                username='patient',
                email='patient@example.com',
                full_name='John Patient',
                user_role='patient'
            )
            patient.set_password('patient123')
            db.session.add(patient)
        db.session.commit()


if __name__ == '__main__':
    init_db_and_seed()
    app.run(debug=True, port=5000)
