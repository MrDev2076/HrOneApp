# app.py - Complete Combined HR Management System with Leave Management
import os
import sqlite3
import json
from functools import wraps
from datetime import datetime, date, timedelta
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_mail import Mail, Message
from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms import StringField, EmailField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "super_secret_hrone_key_2026"
DB_FILE = "database.db"

# File Upload Configuration
UPLOAD_FOLDER = os.path.join(app.root_path, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB

# Flask-Mail Feature Setup
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'nadipallisudharshan@gmail.com')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', 'grha zhrj tknt gthb')
app.config['MAIL_DEFAULT_SENDER'] = app.config['MAIL_USERNAME']

mail = Mail(app)

class ContactForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    subject = StringField('Subject', validators=[DataRequired()])
    message = TextAreaField('Message', validators=[DataRequired()])
    attachment = FileField('Attachment(Optional, Max 100MB)') 
    submit = SubmitField('Send Message')

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        # Users table with leave_balance field
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL,
                member_since TEXT DEFAULT '2026',
                leave_balance INTEGER DEFAULT 20
            )
        ''')
        
        # Leave Requests table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS leave_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                reason TEXT NOT NULL,
                status TEXT DEFAULT 'Pending',
                user_id INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Tasks table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT NOT NULL DEFAULT 'todo',
                user_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Meetings table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS meetings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_code TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                created_by TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                created_at TEXT NOT NULL
            )
        ''')
        
        # Insert default admin, manager and employees
        try:
            conn.execute("INSERT INTO users (username, email, password, role, leave_balance) VALUES (?, ?, ?, ?, ?)",
                         ('admin', 'admin@hrone.com', 'admin123', 'Admin', 0))
            conn.execute("INSERT INTO users (username, email, password, role, leave_balance) VALUES (?, ?, ?, ?, ?)",
                         ('manager', 'manager@hrone.com', 'password123', 'Manager', 0))
            conn.execute("INSERT INTO users (username, email, password, role, leave_balance) VALUES (?, ?, ?, ?, ?)",
                         ('Sruthi', 'sruthi@hrone.com', 'user123', 'Employee', 20))
            conn.execute("INSERT INTO users (username, email, password, role, leave_balance) VALUES (?, ?, ?, ?, ?)",
                         ('Vishal', 'vishal@hrone.com', 'user123', 'Employee', 20))
            conn.execute("INSERT INTO users (username, email, password, role, leave_balance) VALUES (?, ?, ?, ?, ?)",
                         ('Tara', 'tara@hrone.com', 'user123', 'Employee', 20))
            conn.commit()
        except sqlite3.IntegrityError:
            pass

# Room Session Memory States
ROOM_PARTICIPANTS = {}  
ROOM_MESSAGES = {}      

# --- Protection Decorators ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash("Authentication required! Please log in first.", "danger")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        if session.get('role') != 'Admin':
            flash("Access denied! System Administrator clearance required.", "danger")
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# --- Authentication Routes ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with get_db_connection() as conn:
            user = conn.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password)).fetchone()
            if user:
                session['username'] = user['username']
                session['role'] = user['role']
                session['user_id'] = user['id']
                session['leave_balance'] = user['leave_balance']
                flash(f"Welcome back, {user['username']}!", "success")
                return redirect(url_for('dashboard'))
            flash("Invalid credentials. Try again.", "danger")
    return render_template('home.html', show_login_modal=True)

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for('home'))

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

# --- Dashboard ---
@app.route('/dashboard')
@login_required
def dashboard():
    if session.get('role') == 'Admin':
        return redirect(url_for('admin_dashboard'))
    
    with get_db_connection() as conn:
        user = conn.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],)).fetchone()
        orders = conn.execute("SELECT id, title as id, 'placed' as status, '0' as total, 'Just now' as created_at FROM tasks WHERE user_id = ?", (session['user_id'],)).fetchall()
        
        # Get pending count
        pending_count = conn.execute(
            "SELECT COUNT(*) as count FROM leave_requests WHERE status = 'Pending'"
        ).fetchone()['count']
        
    return render_template('user_dashboard.html', user=user, orders=orders, pending_count=pending_count)

# --- Leave Management Routes ---
@app.route('/leaves')
@login_required
def leaves():
    with get_db_connection() as conn:
        # Get user info
        user = conn.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],)).fetchone()
        
        if session.get('role') in ['Admin', 'Manager']:
            # Get all leave requests with employee names
            leave_requests_raw = conn.execute("""
                SELECT lr.*, u.username as employee_name 
                FROM leave_requests lr
                JOIN users u ON lr.user_id = u.id
                ORDER BY lr.created_at DESC
            """).fetchall()
            
            # Get pending requests separately
            pending_requests_raw = conn.execute("""
                SELECT lr.*, u.username as employee_name 
                FROM leave_requests lr
                JOIN users u ON lr.user_id = u.id
                WHERE lr.status = 'Pending'
                ORDER BY lr.created_at ASC
            """).fetchall()
        else:
            # Get user's own leave requests
            leave_requests_raw = conn.execute("""
                SELECT * FROM leave_requests 
                WHERE user_id = ? 
                ORDER BY created_at DESC
            """, (session['user_id'],)).fetchall()
            pending_requests_raw = []
        
        # Convert to list of dicts and calculate duration
        leave_requests = []
        for req in leave_requests_raw:
            req_dict = dict(req)
            start = datetime.strptime(req_dict['start_date'], '%Y-%m-%d').date()
            end = datetime.strptime(req_dict['end_date'], '%Y-%m-%d').date()
            req_dict['duration'] = (end - start).days + 1
            leave_requests.append(req_dict)
        
        pending_requests = []
        for req in pending_requests_raw:
            req_dict = dict(req)
            start = datetime.strptime(req_dict['start_date'], '%Y-%m-%d').date()
            end = datetime.strptime(req_dict['end_date'], '%Y-%m-%d').date()
            req_dict['duration'] = (end - start).days + 1
            pending_requests.append(req_dict)
        
        # Get pending count for badge
        pending_count = conn.execute(
            "SELECT COUNT(*) as count FROM leave_requests WHERE status = 'Pending'"
        ).fetchone()['count']
        
        # Get all users for dropdown (for admin/manager)
        users = conn.execute("SELECT id, username, role, leave_balance FROM users").fetchall()
    
    return render_template('leaves.html', 
                         active_tab='leaves', 
                         page_title="Leave Management Dashboard",
                         target_heading="Time-Off Approvals Module",
                         leave_requests=leave_requests,
                         pending_requests=pending_requests,
                         pending_count=pending_count,
                         user=user,
                         users=users)

@app.route('/request-leave', methods=['POST'])
@login_required
def request_leave():
    if session.get('role') in ['Admin', 'Manager']:
        flash('Admins and Managers cannot request leave.', 'danger')
        return redirect(url_for('leaves'))
    
    start = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
    end = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()
    reason = request.form.get('reason', '').strip()
    
    # Validation
    if not reason:
        flash('Please provide a reason for leave.', 'danger')
        return redirect(url_for('leaves'))
    
    if start < date.today():
        flash('Cannot apply for leave on past dates.', 'danger')
        return redirect(url_for('leaves'))
        
    if start > end:
        flash('The start date cannot be later than the end date.', 'danger')
        return redirect(url_for('leaves'))
    
    with get_db_connection() as conn:
        # Check for overlapping leave requests
        overlapping = conn.execute("""
            SELECT * FROM leave_requests 
            WHERE user_id = ? 
            AND status IN ('Pending', 'Approved')
            AND date(start_date) <= date(?)
            AND date(end_date) >= date(?)
        """, (session['user_id'], end.strftime('%Y-%m-%d'), start.strftime('%Y-%m-%d'))).fetchone()
        
        if overlapping:
            flash(f'You have already applied for leave during this period.', 'danger')
            return redirect(url_for('leaves'))
        
        # Check leave balance
        requested_days = (end - start).days + 1
        user = conn.execute("SELECT leave_balance FROM users WHERE id = ?", (session['user_id'],)).fetchone()
        
        if requested_days > user['leave_balance']:
            flash(f'Insufficient leave balance. Available: {user["leave_balance"]} days, Requested: {requested_days} days.', 'danger')
            return redirect(url_for('leaves'))
        
        # Create leave request
        conn.execute("""
            INSERT INTO leave_requests (start_date, end_date, reason, status, user_id)
            VALUES (?, ?, ?, 'Pending', ?)
        """, (start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d'), reason, session['user_id']))
        conn.commit()
        
        flash('Leave request submitted successfully!', 'success')
        return redirect(url_for('leaves'))

@app.route('/action-leave/<int:request_id>/<string:action>')
@login_required
def action_leave(request_id, action):
    if session.get('role') not in ['Admin', 'Manager']:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('leaves'))
    
    with get_db_connection() as conn:
        leave_req = conn.execute("""
            SELECT lr.*, u.leave_balance as user_balance, u.id as user_id
            FROM leave_requests lr
            JOIN users u ON lr.user_id = u.id
            WHERE lr.id = ?
        """, (request_id,)).fetchone()
        
        if not leave_req:
            flash('Leave request not found.', 'danger')
            return redirect(url_for('leaves'))
        
        if action == 'approve':
            start = datetime.strptime(leave_req['start_date'], '%Y-%m-%d').date()
            end = datetime.strptime(leave_req['end_date'], '%Y-%m-%d').date()
            requested_days = (end - start).days + 1
            
            if leave_req['user_balance'] >= requested_days:
                # Deduct from leave balance
                conn.execute("""
                    UPDATE users SET leave_balance = leave_balance - ? 
                    WHERE id = ?
                """, (requested_days, leave_req['user_id']))
                # Update request status
                conn.execute("""
                    UPDATE leave_requests SET status = 'Approved' 
                    WHERE id = ?
                """, (request_id,))
                conn.commit()
                flash(f'Leave request approved. {requested_days} days deducted from balance.', 'success')
            else:
                flash(f'Employee has insufficient leave balance. Available: {leave_req["user_balance"]} days, Required: {requested_days} days.', 'danger')
        
        elif action == 'reject':
            conn.execute("UPDATE leave_requests SET status = 'Rejected' WHERE id = ?", (request_id,))
            conn.commit()
            flash('Leave request rejected.', 'info')
        
        else:
            flash('Invalid action.', 'danger')
        
        return redirect(url_for('leaves'))

# --- Admin Controller Core ---
@app.route('/admin')
@admin_required
def admin_dashboard():
    with get_db_connection() as conn:
        users = conn.execute("SELECT * FROM users").fetchall()
        pending_count = conn.execute(
            "SELECT COUNT(*) as count FROM leave_requests WHERE status = 'Pending'"
        ).fetchone()['count']
    return render_template('admin_dashboard.html', users=users, pending_count=pending_count)

@app.route('/admin/add', methods=['POST'])
@admin_required
def admin_add():
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    role = request.form['role']
    leave_balance = request.form.get('leave_balance', 20)
    
    try:
        with get_db_connection() as conn:
            conn.execute("""
                INSERT INTO users (username, email, password, role, leave_balance) 
                VALUES (?, ?, ?, ?, ?)
            """, (username, email, password, role, leave_balance))
            conn.commit()
        flash("New profile successfully registered.", "success")
    except sqlite3.IntegrityError:
        flash("Username already exists in system.", "danger")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/edit/<int:id>', methods=['POST'])
@admin_required
def admin_edit(id):
    username = request.form['username']
    email = request.form['email']
    role = request.form['role']
    leave_balance = request.form.get('leave_balance', 20)
    
    with get_db_connection() as conn:
        conn.execute("""
            UPDATE users SET username = ?, email = ?, role = ?, leave_balance = ? 
            WHERE id = ?
        """, (username, email, role, leave_balance, id))
        conn.commit()
    flash("User profile updated successfully.", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete/<int:id>')
@admin_required
def admin_delete(id):
    with get_db_connection() as conn:
        conn.execute("DELETE FROM users WHERE id = ?", (id,))
        conn.commit()
    flash("Profile successfully removed from system.", "warning")
    return redirect(url_for('admin_dashboard'))

@app.route('/user/update', methods=['POST'])
@login_required
def user_update():
    email = request.form['email']
    with get_db_connection() as conn:
        conn.execute("UPDATE users SET email = ? WHERE id = ?", (email, session['user_id']))
        conn.commit()
    flash("Contact email reference updated.", "success")
    return redirect(url_for('dashboard'))

@app.route('/user/reset-password', methods=['POST'])
@login_required
def user_reset_password():
    password = request.form['password']
    with get_db_connection() as conn:
        conn.execute("UPDATE users SET password = ? WHERE id = ?", (password, session['user_id']))
        conn.commit()
    flash("Security token updated securely.", "success")
    return redirect(url_for('dashboard'))

# --- Tasks Routes ---
@app.route('/tasks')
@login_required
def tasks():
    with get_db_connection() as conn:
        todo = conn.execute("SELECT * FROM tasks WHERE status = 'todo'").fetchall()
        progress = conn.execute("SELECT * FROM tasks WHERE status = 'progress'").fetchall()
        done = conn.execute("SELECT * FROM tasks WHERE status = 'done'").fetchall()
        users = conn.execute("SELECT id, username FROM users").fetchall()
        pending_count = conn.execute(
            "SELECT COUNT(*) as count FROM leave_requests WHERE status = 'Pending'"
        ).fetchone()['count']
    return render_template('tasks.html', 
                         active_tab='tasks', 
                         page_title="Agile Scrum Workspace", 
                         todo_tasks=todo, 
                         progress_tasks=progress, 
                         done_tasks=done, 
                         users=users,
                         pending_count=pending_count)

@app.route('/tasks/add', methods=['POST'])
@login_required
def add_scrum_task():
    title = request.form['title']
    description = request.form['description']
    user_id = request.form.get('user_id') or None
    with get_db_connection() as conn:
        conn.execute("INSERT INTO tasks (title, description, status, user_id) VALUES (?, ?, 'todo', ?)", 
                    (title, description, user_id))
        conn.commit()
    flash("Scrum item committed to backlog.", "success")
    return redirect(url_for('tasks'))

@app.route('/tasks/move/<int:id>/<string:status>')
@login_required
def move_scrum_task(id, status):
    if status in ['todo', 'progress', 'done']:
        with get_db_connection() as conn:
            conn.execute("UPDATE tasks SET status = ? WHERE id = ?", (status, id))
            conn.commit()
        flash("Task sprint classification transitioned.", "success")
    return redirect(url_for('tasks'))

# --- Contact Routes ---
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        msg = Message(
            subject=f"[Contact form] {form.subject.data}",
            recipients=['nadipallisudharshan@gmail.com'],
            reply_to=form.email.data
        )
        body_text = f"From: {form.name.data} - {form.email.data} \n\n\nMessage: \n{form.message.data}"
        file = form.attachment.data
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            file_size = os.path.getsize(file_path)

            if file_size > 20 * 1024 * 1024:
                body_text += f"\n\n[SYSTEM NOTE]: A larger file named `{filename}` ({round(file_size/(1024*1024), 2)} MB)"
            else:
                with app.open_resource(file_path) as fp:
                    msg.attach(filename, file.mimetype, fp.read())
                body_text += f"\n\n[SYSTEM NOTE:] Attached file `{filename}` successfully"
        msg.body = body_text
        try:
            mail.send(msg)
            flash('Your form has submitted successfully', 'success')
        except Exception as e:
            flash(f'An error occurred: {e}', 'danger')
    return render_template('contact.html', form=form)

@app.errorhandler(413)
def file_too_large(e):
    flash('File is too large!\nMaximum allowed size is 100MB', 'danger')
    return redirect(url_for('contact'))

# --- Meetings Routes ---
@app.route('/meetings')
@login_required
def meetings():
    with get_db_connection() as conn:
        active_meets = conn.execute("SELECT * FROM meetings WHERE status = 'active' ORDER BY id DESC").fetchall()
        pending_count = conn.execute(
            "SELECT COUNT(*) as count FROM leave_requests WHERE status = 'Pending'"
        ).fetchone()['count']
    return render_template('meetings.html', 
                         active_tab='meetings', 
                         page_title="Corporate Sync Terminal", 
                         active_meets=active_meets,
                         pending_count=pending_count)

@app.route('/meetings/create', methods=['POST'])
@login_required
def create_meeting():
    title = request.form.get('title', 'Ad-hoc Sync').strip()
    room_code = request.form.get('room_code', '').strip().lower()
    if not room_code:
        room_code = f"meet-{os.urandom(3).hex()}"
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        with get_db_connection() as conn:
            conn.execute("INSERT INTO meetings (room_code, title, created_by, created_at) VALUES (?, ?, ?, ?)",
                         (room_code, title, session['username'], timestamp))
            conn.commit()
        flash(f"Meeting cluster node [{room_code}] opened successfully.", "success")
    except sqlite3.IntegrityError:
        flash("Room identifier code is currently active. Choose another code identifier.", "danger")
        return redirect(url_for('meetings'))
        
    return redirect(url_for('join_meeting_room', room_code=room_code))

@app.route('/meetings/room/<string:room_code>')
@login_required
def join_meeting_room(room_code):
    username = session['username']
    is_admin_user = (session.get('role') == 'Admin')
    
    with get_db_connection() as conn:
        meet = conn.execute("SELECT * FROM meetings WHERE room_code = ? AND status = 'active'", (room_code,)).fetchone()
    
    if not meet:
        flash("Target conference session cannot be found or was closed by administrator.", "danger")
        return redirect(url_for('meetings'))

    if room_code not in ROOM_PARTICIPANTS:
        ROOM_PARTICIPANTS[room_code] = {}
    if room_code not in ROOM_MESSAGES:
        ROOM_MESSAGES[room_code] = []

    # Admin or room creator gets immediate access
    is_privileged = is_admin_user or (meet['created_by'] == username)
    determined_status = 'allowed' if is_privileged else 'pending'

    ROOM_PARTICIPANTS[room_code][username] = {
        'username': username,
        'role': session.get('role'),
        'cam': False,
        'mic': False,
        'speaking': False,
        'raised_hand': False,
        'screen_sharing': False,
        'status': determined_status
    }

    return render_template('meetings.html', 
                           active_tab='meetings', 
                           in_room=True, 
                           room_code=room_code, 
                           meet_title=meet['title'],
                           is_host=is_privileged)

@app.route('/meetings/api/sync/<string:room_code>', methods=['GET', 'POST'])
@login_required
def api_sync_room(room_code):
    username = session['username']
    
    # Initialize room if not exists
    if room_code not in ROOM_PARTICIPANTS:
        ROOM_PARTICIPANTS[room_code] = {}
    if room_code not in ROOM_MESSAGES:
        ROOM_MESSAGES[room_code] = []

    with get_db_connection() as conn:
        meet = conn.execute("SELECT * FROM meetings WHERE room_code = ?", (room_code,)).fetchone()
    
    # Check if user is admin or room creator
    is_privileged = (session.get('role') == 'Admin') or (meet and meet['created_by'] == username)

    # Handle POST request - update user state
    if request.method == 'POST':
        payload = request.get_json() or {}
        
        # Initialize user if not exists
        if username not in ROOM_PARTICIPANTS[room_code]:
            ROOM_PARTICIPANTS[room_code][username] = {
                'username': username,
                'role': session.get('role'),
                'cam': False,
                'mic': False,
                'speaking': False,
                'raised_hand': False,
                'screen_sharing': False,
                'status': 'allowed' if is_privileged else 'pending'
            }
        
        # Update user state
        user_state = ROOM_PARTICIPANTS[room_code][username]
        for key in ['cam', 'mic', 'speaking', 'raised_hand', 'screen_sharing']:
            if key in payload:
                user_state[key] = bool(payload[key])
        
        # If screen sharing is enabled, disable for others
        if payload.get('screen_sharing'):
            for peer in ROOM_PARTICIPANTS[room_code]:
                if peer != username:
                    ROOM_PARTICIPANTS[room_code][peer]['screen_sharing'] = False
        
        # Ensure privileged users always have 'allowed' status
        if is_privileged:
            user_state['status'] = 'allowed'
    
    # Get current user state
    user_node = ROOM_PARTICIPANTS[room_code].get(username)
    if not user_node:
        # Re-initialize if somehow missing
        ROOM_PARTICIPANTS[room_code][username] = {
            'username': username,
            'role': session.get('role'),
            'cam': False,
            'mic': False,
            'speaking': False,
            'raised_hand': False,
            'screen_sharing': False,
            'status': 'allowed' if is_privileged else 'pending'
        }
        user_node = ROOM_PARTICIPANTS[room_code][username]

    return jsonify({
        'status': user_node['status'],
        'participants': list(ROOM_PARTICIPANTS[room_code].values()),
        'messages': ROOM_MESSAGES.get(room_code, [])
    })

@app.route('/meetings/api/chat/send/<string:room_code>', methods=['POST'])
@login_required
def api_send_message(room_code):
    if room_code not in ROOM_MESSAGES:
        ROOM_MESSAGES[room_code] = []
    
    payload = request.get_json() or {}
    text = payload.get('message', '').strip()
    if text:
        ROOM_MESSAGES[room_code].append({
            'sender': session['username'],
            'text': text,
            'time': datetime.now().strftime('%H:%M')
        })
    return jsonify({'status': 'success'})

@app.route('/meetings/api/admin/action/<string:room_code>', methods=['POST'])
@login_required
def api_admin_action(room_code):
    with get_db_connection() as conn:
        meet = conn.execute("SELECT * FROM meetings WHERE room_code = ?", (room_code,)).fetchone()
    
    is_admin = (session.get('role') == 'Admin' or (meet and meet['created_by'] == session['username']))
    if not is_admin:
        return jsonify({'status': 'unauthorized'}), 403

    payload = request.get_json() or {}
    target_user = payload.get('target_user')
    action = payload.get('action')

    if room_code in ROOM_PARTICIPANTS and target_user in ROOM_PARTICIPANTS[room_code]:
        if action == 'allow':
            ROOM_PARTICIPANTS[room_code][target_user]['status'] = 'allowed'
        elif action == 'remove':
            del ROOM_PARTICIPANTS[room_code][target_user]
        return jsonify({'status': 'success'})
    
    return jsonify({'status': 'target_not_found'})

@app.route('/meetings/end/<string:room_code>')
@login_required
def end_meeting(room_code):
    with get_db_connection() as conn:
        meet = conn.execute("SELECT * FROM meetings WHERE room_code = ?", (room_code,)).fetchone()
    
    if session.get('role') == 'Admin' or (meet and meet['created_by'] == session['username']):
        with get_db_connection() as conn:
            conn.execute("UPDATE meetings SET status = 'closed' WHERE room_code = ?", (room_code,))
            conn.commit()
        if room_code in ROOM_PARTICIPANTS:
            del ROOM_PARTICIPANTS[room_code]
        if room_code in ROOM_MESSAGES:
            del ROOM_MESSAGES[room_code]
        flash("Conference session terminated by host authority.", "warning")
    else:
        flash("Only session hosts retain permission to terminate communication structures.", "danger")
    return redirect(url_for('meetings'))

@app.route('/meetings/leave/<string:room_code>')
@login_required
def leave_meeting(room_code):
    username = session['username']
    if room_code in ROOM_PARTICIPANTS and username in ROOM_PARTICIPANTS[room_code]:
        del ROOM_PARTICIPANTS[room_code][username]
    flash("Disconnected from session channel.", "info")
    return redirect(url_for('meetings'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)