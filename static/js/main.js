/**
 * CareFirst Medical - Doctor Appointment System
 * Client-side validation, contact form AJAX, confirmation dialogs, smooth scroll.
 */
(function() {
  'use strict';

  function validateEmail(email) {
    var re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(String(email).toLowerCase());
  }

  function validatePhone(phone) {
    if (!phone || !phone.trim()) return true;
    var digits = phone.replace(/\D/g, '');
    return digits.length >= 10 && digits.length <= 15;
  }

  function showFieldError(input, message) {
    input.classList.add('is-invalid');
    var fb = input.nextElementSibling;
    if (fb && fb.classList.contains('invalid-feedback')) {
      fb.textContent = message;
      fb.style.display = 'block';
    }
  }

  function clearFieldError(input) {
    input.classList.remove('is-invalid');
    var fb = input.nextElementSibling;
    if (fb && fb.classList.contains('invalid-feedback')) fb.style.display = 'none';
  }

  // ----- Contact form validation -----
  var contactForm = document.getElementById('contact-form');
  if (contactForm) {
    contactForm.addEventListener('submit', function(e) {
      var name = contactForm.querySelector('[name="name"]');
      var email = contactForm.querySelector('[name="email"]');
      var phone = contactForm.querySelector('[name="phone"]');
      var subject = contactForm.querySelector('[name="subject"]');
      var message = contactForm.querySelector('[name="message"]');
      var valid = true;
      [name, subject, message].forEach(function(field) {
        if (!field || !field.value.trim()) {
          showFieldError(field, 'This field is required.');
          valid = false;
        } else {
          clearFieldError(field);
        }
      });
      if (email) {
        if (!email.value.trim()) {
          showFieldError(email, 'Email is required.');
          valid = false;
        } else if (!validateEmail(email.value)) {
          showFieldError(email, 'Please enter a valid email address.');
          valid = false;
        } else {
          clearFieldError(email);
        }
      }
      if (phone && phone.value.trim() && !validatePhone(phone.value)) {
        showFieldError(phone, 'Please enter a valid phone number.');
        valid = false;
      } else if (phone) clearFieldError(phone);
      if (!valid) e.preventDefault();
    });
  }

  // ----- Register form: password strength and match -----
  var registerForm = document.getElementById('register-form');
  if (registerForm) {
    var pw = registerForm.querySelector('[name="password"]');
    var confirm = registerForm.querySelector('[name="confirm_password"]');
    var username = registerForm.querySelector('[name="username"]');
    registerForm.addEventListener('submit', function(e) {
      var valid = true;
      if (username && username.value.length < 3) {
        showFieldError(username, 'Username must be at least 3 characters.');
        valid = false;
      } else if (username) clearFieldError(username);
      if (pw) {
        if (pw.value.length < 8) {
          showFieldError(pw, 'Password must be at least 8 characters.');
          valid = false;
        } else {
          clearFieldError(pw);
        }
      }
      if (confirm && pw && confirm.value !== pw.value) {
        showFieldError(confirm, 'Passwords must match.');
        valid = false;
      } else if (confirm) clearFieldError(confirm);
      if (!valid) e.preventDefault();
    });
  }

  // ----- Login form: required fields -----
  var loginForm = document.getElementById('login-form');
  if (loginForm) {
    loginForm.addEventListener('submit', function(e) {
      var user = loginForm.querySelector('[name="username"]');
      var pass = loginForm.querySelector('[name="password"]');
      var valid = true;
      if (!user || !user.value.trim()) {
        if (user) showFieldError(user, 'Username is required.');
        valid = false;
      }
      if (!pass || !pass.value.trim()) {
        if (pass) showFieldError(pass, 'Password is required.');
        valid = false;
      }
      if (!valid) e.preventDefault();
    });
  }

  // ----- Book appointment form: required doctor, date, time, reason -----
  var bookForm = document.getElementById('book-appointment-form');
  if (bookForm) {
    bookForm.addEventListener('submit', function(e) {
      var doctorSelect = bookForm.querySelector('select[name="doctor_id"]');
      var dateInput = bookForm.querySelector('#appointment_date');
      var timeInput = bookForm.querySelector('#appointment_time');
      var reason = bookForm.querySelector('[name="reason_for_visit"]');
      var valid = true;
      if (!doctorSelect || parseInt(doctorSelect.value, 10) === 0) {
        if (doctorSelect) showFieldError(doctorSelect, 'Please select a doctor.');
        valid = false;
      } else if (doctorSelect) clearFieldError(doctorSelect);
      if (!dateInput || !dateInput.value) {
        if (dateInput) showFieldError(dateInput, 'Please select a date.');
        valid = false;
      } else if (dateInput) clearFieldError(dateInput);
      if (!timeInput || !timeInput.value) {
        var wrapper = document.getElementById('time-slots-error');
        if (wrapper) { wrapper.style.display = 'block'; wrapper.textContent = 'Please select a time slot.'; }
        valid = false;
      } else {
        var w = document.getElementById('time-slots-error');
        if (w) { w.style.display = 'none'; }
      }
      if (!reason || !reason.value.trim()) {
        if (reason) showFieldError(reason, 'Please describe your reason for the visit.');
        valid = false;
      } else if (reason) clearFieldError(reason);
      if (!valid) e.preventDefault();
    });
  }

  // ----- Smooth scroll for anchor links -----
  document.querySelectorAll('a[href^="#"]').forEach(function(anchor) {
    if (anchor.getAttribute('href') === '#') return;
    anchor.addEventListener('click', function(e) {
      var target = document.querySelector(anchor.getAttribute('href'));
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });

  // ----- Confirm before cancel (additional safety; forms may have onsubmit too) -----
  var cancelForms = document.querySelectorAll('form[action*="cancel"]');
  cancelForms.forEach(function(form) {
    if (form.getAttribute('onsubmit')) return;
    form.addEventListener('submit', function(e) {
      if (!confirm('Are you sure you want to cancel this appointment?')) {
        e.preventDefault();
      }
    });
  });
})();
