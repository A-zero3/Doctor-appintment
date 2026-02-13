# CareFirst Medical – Doctor Appointment System

A full-stack web application for booking and managing medical appointments. Patients can book appointments online; doctors and staff can manage schedules, add notes, and mark appointments complete.

## Features

- **Patient flow**: Browse doctors, book appointments (with date/time and reason), view and cancel upcoming appointments, view past appointments and doctor notes, edit profile.
- **Doctor flow**: View appointments (with patient contact info), add/update notes, mark appointments complete, cancel appointments, view weekly/monthly stats.
- **Public**: Home page with hero and featured doctors, Doctors page (filter by specialization, search), About, Contact (form stored in database).
- **Auth**: Combined Login/Register page with tabs; role-based access (patient, doctor); secure password hashing (Werkzeug); session management (Flask-Login).
- **Validation**: Client-side (JavaScript) and server-side (Flask-WTF) for all forms; appointment slot availability checked on submit.

## Tech Stack

- **Frontend**: HTML5, CSS3, Bootstrap 5, JavaScript, jQuery
- **Backend**: Flask (Python), Jinja2
- **Database**: SQLAlchemy (SQLite by default; configurable)
- **Auth**: Flask-Login, Werkzeug password hashing
- **Forms**: Flask-WTF, WTForms

## Project Structure

```
├── app.py              # Flask app, routes, auth, CRUD
├── config.py           # Configuration (DB, secret key, uploads)
├── models.py           # User, Doctor, Appointment, ContactSubmission
├── forms.py            # Registration, Login, BookAppointment, Contact, ProfileEdit, DoctorNote
├── requirements.txt
├── README.md
├── instance/           # SQLite DB (created on first run)
├── static/
│   ├── css/custom.css  # Medical theme styles
│   ├── js/main.js      # Validation, AJAX, confirmations
│   └── uploads/        # Doctor profile images (optional)
└── templates/
    ├── base.html
    ├── home.html
    ├── doctors.html
    ├── book_appointment.html
    ├── patient_dashboard.html
    ├── doctor_dashboard.html
    ├── about.html
    ├── contact.html
    ├── login.html      # Login + Register tabs
    ├── profile_edit.html
    ├── appointment_notes.html
    ├── 404.html
    └── 500.html
```

## Setup

1. **Create a virtual environment (recommended)**

   ```bash
   python -m venv venv
   venv\Scripts\activate   # Windows
   # or: source venv/bin/activate   # macOS/Linux
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**

   ```bash
   python app.py
   ```

   On first run, the app creates the database and seeds sample doctors and a test patient. Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.

## Test Credentials

After the first run, you can log in with:

| Role    | Username   | Password    |
|---------|------------|-------------|
| Patient | `patient`  | `patient123` |
| Doctor  | `Anil Shrestha` | `doctor123`  |
| Doctor  | `Sameer Shrestha` | `doctor123`  |
| Doctor  | `Biraj Shrestha` | `doctor123` |
| Doctor  | `Digdarshan Khadka` | `doctor123`  |

- **Patient**: Book appointments, view/cancel upcoming, view past appointments and notes, edit profile.
- **Doctor**: View appointments, add notes, mark complete, cancel, see weekly/monthly counts.

## Configuration

- **Database**: Set `DATABASE_URL` in the environment or edit `config.py` (default: `sqlite:///doctor_appointment.db` in the `instance` folder).
- **Secret key**: Set `SECRET_KEY` in the environment for production.

## Database Schema

- **Users**: user_id, username, email, password_hash, user_role (patient/doctor/admin), full_name, phone_number, date_of_birth, account_creation, last_login
- **Doctors**: doctor_id, user_id (FK → Users), specialization, qualifications, years_of_experience, consultation_fee, available_days, available_time_slots, about_text, profile_image_filename
- **Appointments**: appointment_id, patient_id (FK → Users), doctor_id (FK → Doctors), appointment_date, appointment_time, status (pending/confirmed/completed/cancelled), reason_for_visit, notes, created_at, updated_at
- **ContactSubmission**: id, name, email, phone, subject, message, submitted_at

Relationships: User (patient) → many Appointments; Doctor → many Appointments; User (doctor) → one Doctor profile.

## License

This project is a template for educational and prototyping use. Customize branding, specializations, and features as needed for your practice.
