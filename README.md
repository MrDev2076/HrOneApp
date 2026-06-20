
### ### HrOne - HR MANAGEMENT SYSTEM                      


An all-in-one, lightweight Human Resource Management System (HRMS) powered 
by Python, Flask, and SQLite. The application streamlines employee management, 
automates time-off workflows, runs a real-time corporate sync and chat module, 
and offers custom tools for task coordination alongside a secure help desk 
mailing framework.

---

## 🛠️ CORE FEATURES

### Feature 1: Role-Based Admin Panel (SQLite DB)
* **Access Levels:** Differentiates system logic among Admin, Manager, and 
    Employee accounts.
* **Secure Routing:** Restricts functional pathways via custom protection 
    decorators (`@login_required` and `@admin_required`).
* **CRUD Engine:** The system initializes an automated SQLite pipeline 
    pre-populating base administrative identities (`admin`, `manager`, 
    `Sruthi`, `Vishal`, `Tara`). Admins can register, update, or purge 
    system profiles directly from their dashboard.

### Feature 2: Leave Request Form
* **Validation Rules:** Prevents retroactively dated applications, handles 
    date logic boundary checks (Start Date cannot be later than End Date), 
    and checks against active time-off requests to avoid timeline collisions.
* **Balance Deductions:** Tracks independent profile metrics initialized 
    at 20 standard days. Once an Admin or Manager issues an Approval action, 
    the requested days are automatically calculated and deducted from the 
    employee's SQLite balance profile.

### Feature 3: Meetings Room Sync & Chat Module
* **Participant Authorization:** Integrates a custom gatekeeper workflow. 
    Standard identities routing into an active meeting pin are set to a 
    'pending' state until an Admin or Room Host issues a clearance action.
* **State Polling Node:** Features a granular polling state memory system 
    built into `ROOM_PARTICIPANTS` and `ROOM_MESSAGES`. It synchronizes system 
    actions such as muting mics, turning on cams, hand-raising, screen-share 
    monopolization, and structured text messaging.

### Feature 4: Task Management & Workflows (Agile - Scrum)
* **Sprint Workspaces:** Organizes tasks using an Agile Scrum board structure 
    split into `todo`, `progress`, and `done` classifications.
* **Backlog Planning:** Enables rapid task creation and assigns targeted items 
    to specific personnel profiles utilizing indexed relational foreign key constraints 
    back to the main user table.

### Feature 5: Contact Admin Mailing Gateway
* **Flask-Mail SMTP:** Runs a secure outbound mail route leveraging Google 
    SMTP endpoints (`smtp.gmail.com:587`) protected by TLS cryptographic wrappers.
* **Data Size Safety Rails:** Supports standard text emails along with multi-part 
    file uploads up to 100MB. Files exceeding 20MB trigger an alternate workflow 
    that logs a system notice instead of attaching the file directly, preventing 
    outbound server errors.

## 🗺️ ENDPOINT ROUTING & FUNCTIONAL PATHS

### 🔐 Authentication Context
* `GET/POST  /login`          -> Renders login target inside home view; authenticates user and maps details into Flask Session storage.
* `GET       /logout`         -> Invokes programmatic `.clear()` action on session variables; returns user to home route.
* `GET       /`               -> Resolves central `home.html` rendering node structure.
* `GET       /about`          -> Returns organizational information rendering layouts.

### 📊 Dashboard Interfaces
* `GET       /dashboard`      -> Router wrapper. Evaluates identity profile context, then forwards user to Admin or Employee view.

### ⏱️ Leave Management Module
* `GET       /leaves`         -> Renders request records dashboard. Admins/Managers view global logs; Employees track their own limits.
* `POST      /request-leave`  -> Validates dates, checks balances, and logs new requests as 'Pending'.
* `GET       /action-leave/<id>/<action>` -> Authorizes Admin/Manager decisions (`approve`/`reject`), updating profile balance counters.

### 👥 Admin Operations Core
* `GET       /admin`          -> Renders central profile lists (Restricted to Admin identities).
* `POST      /admin/add`      -> Inserts new employee record tracking fields directly into the database.
* `POST      /admin/edit/<id>`-> Modifies target user fields (Username, Email, Access Level, Leave Allowances).
* `GET       /admin/delete/<id>` -> Permanently purges target user profile record indexes from storage tables.
* `POST      /user/update`    -> Allows an authenticated employee to update their own contact email field.
* `POST      /user/reset-password` -> Enables instant updates to personal security access tokens.

### 🏃 Scrum Workspace Engine
* `GET       /tasks`          -> Gathers sprint board cards sorting entries across `todo`, `progress`, and `done`.
* `POST      /tasks/add`      -> Commits a new task item into the project backlog.
* `GET       /tasks/move/<id>/<status>` -> Shifts a target task card into a new status lane.

### ✉️ Help Desk Portal
* `GET/POST  /contact`        -> Renders WTForms client wrapper; transfers validated text data and files to the mail server.

### 💬 Video Sync & Polling Rooms
* `GET       /meetings`       -> Lists active corporate meetings and handles ad-hoc connection forms.
* `POST      /meetings/create` -> Generates unique meeting nodes (`meet-******`) and saves them to the database.
* `GET       /meetings/room/<room_code>` -> Connects users to the meeting room layout interface.
* `GET/POST  /meetings/api/sync/<room_code>` -> API endpoint. Processes participant states (Cams, Mics, Access Statuses).
* `POST      /meetings/api/chat/send/<room_code>` -> Appends new chat messages to the room's memory array (`ROOM_MESSAGES`).
* `POST      /meetings/api/admin/action/<room_code>` -> Host-only route. Authorizes pending attendees or disconnects target users.
* `GET       /meetings/end/<room_code>` -> Closes the meeting node and clears its temporary room state data.
* `GET       /meetings/leave/<room_code>` -> Disconnects the individual user from the targeted meeting array.

---

## 🚀 INSTALLATION & LOCAL DEPLOYMENT COMMANDS

Follow these steps to set up and run the application locally on your machine:

### 1. Initialize Project Directory
```bash
git clone <your-repository-url>
cd HrOne

```
Configure Virtual Environment Sandbox
# Generate the virtual environment container
```bash
python -m venv cabin(venv)
```
# Activate the sandbox environment (Windows OS)
```bash
"cabin(venv)/Scripts/activate"
```
# Activate the sandbox environment (Mac/Linux OS)
```bash
source cabin(venv)/bin/activate
```
Install Dependencies
# Upgrade the local pip installer engine
```bash
python -m pip install --upgrade pip
```
# Install required system packages
```bash
pip install -r requirements.txt
```

Set Up Environment Variables (Optional)
# On Windows (Command Prompt)
set MAIL_USERNAME="your-email@gmail.com"
set MAIL_PASSWORD="your-app-password"

# On Windows (PowerShell)
$env:MAIL_USERNAME="your-email@gmail.com"
$env:MAIL_PASSWORD="your-app-password"

# On Linux/Mac
export MAIL_USERNAME="your-email@gmail.com"
export MAIL_PASSWORD="your-app-password"

Launch the Application Server
```bash
# Run the core Flask script directly
python app.py
```
*Local URL:* **http://127.0.0.1:5000/**

*Default Admin Credentials:* **Username:** admin **| Password:** admin123

*Default Employee Credentials:* **Username:** Sruthi **| Password:** user123
