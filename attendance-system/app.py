from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime
import os
import pyrebase
import traceback
app = Flask(__name__)








# Hardcoded users (for simplicity; use Firestore/Auth in real apps)
users = {}
@app.route('/')
def intro():
    return render_template('intro.html')

# Home route redirects to login
@app.route('/home')
def home():
    return redirect(url_for('login'))

# Signup page
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Check if passwords match
        if password != confirm_password:
            return render_template('signup.html', error='Passwords do not match.')

        try:
            # Attempt to create user using Firebase
            user = auth.create_user_with_email_and_password(email, password)
            session['user'] = email
             # 🔽 Save to Firebase under 'users'
            db.reference('users').push({
                'name': name,
                'email': email
            })
            return redirect(url_for('login'))

        except Exception as e:
            # Print full error to console for debugging
            print(f"Signup error: {e}")

            # Extract Firebase error message if possible
            error_message = "Signup failed. Try again with a different email or stronger password."
            try:
                error_json = e.args[1]
                error_data = eval(error_json)
                error_message = error_data['error']['message'].replace('_', ' ').capitalize()
            except:
                pass

            return render_template('signup.html', error=error_message)

    return render_template('signup.html')


    return render_template('signup.html')
# Forgot Password page
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        # For now, we just simulate a message
        message = f"If an account with {email} exists, a password reset link has been sent."
        return render_template('forgot_password.html', message=message)
    
    return render_template('forgot_password.html')

# Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        try:
            user = auth.sign_in_with_email_and_password(email, password)
            session['user'] = email
            return redirect(url_for('dashboard'))
        except Exception as e:
            error_message = "Invalid email or password."
            print(f"Login error: {e}")
            return render_template('login.html', error=error_message)

    return render_template('login.html')


# ----------------------
# Dashboard Route
# ----------------------
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))

    attendance_ref = db.reference('attendance')
    all_records = attendance_ref.get()
    today_str = datetime.now().strftime('%Y-%m-%d')
    today_count = 0

    if all_records:
        for rec in all_records.values():
            if rec['timestamp'].startswith(today_str):
                today_count += 1

    return render_template('dashboard.html',
                           today_count=today_count,
                           session=session)


# ----------------------
# Mark Attendance Page
# ----------------------
# ✅ Remove or comment out the old /mark_attendance API if not used

# Already present:
@app.route('/mark', methods=['GET', 'POST'])
def mark_attendance_page():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        student_id = request.form['id']
        time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            ref = db.reference('attendance')
            ref.push({
                'name': name,
                'id': student_id,
                'timestamp': time_now
            })
            return render_template('mark_attendance_page.html', message='✅ Attendance marked successfully!')
        except Exception as e:
            return render_template('mark_attendance_page.html', error='Something went wrong. Try again.')

    return render_template('mark_attendance_page.html')



# ----------------------
# View Attendance Records
# ----------------------
@app.route('/attendance-records')
def view_attendance():
    if 'user' not in session:
        return redirect(url_for('login'))

    ref = db.reference('attendance')
    records = ref.get()

    attendance_list = []
    if records:
        for key, value in records.items():
            attendance_list.append(value)

    return render_template('view_attendance.html', records=attendance_list)


# ----------------------
# View Students Page
# ----------------------
@app.route('/view_students')
def view_students():
    if 'user' not in session:
        return redirect(url_for('login'))

    users_ref = db.reference('users')
    students = users_ref.get()

    return render_template('view_students.html', students=students)


# ----------------------
# Attendance API Endpoint
# ----------------------


# ----------------------
# Logout Route
# ----------------------
@app.route('/logout')
def logout():
    session.pop('user', None)  # Remove user from session
    return redirect(url_for('login'))

# ----------------------
# Run the app
# ----------------------
if __name__ == '__main__':
    app.run(debug=True)
