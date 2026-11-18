a"""
Eventora - Event Management & RSVP System

Flask application entry point.
Stores application data in JSON files inside the data/ directory.
"""

# ============================================================
# 1. IMPORTS
# ============================================================

from flask import (
    Flask, render_template, request,
    redirect, url_for, flash, session
)
from werkzeug.security import generate_password_hash, check_password_hash

import json
import os
import re
from datetime import datetime, date
from functools import wraps


# ============================================================
# 2. APPLICATION CONFIGURATION AND DATA FILE PATHS
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

EVENTS_FILE = os.path.join(BASE_DIR, 'data', 'events.json')
ATTENDEES_FILE = os.path.join(BASE_DIR, 'data', 'attendees.json')
FEEDBACK_FILE = os.path.join(BASE_DIR, 'data', 'feedback.json')
USERS_FILE = os.path.join(BASE_DIR, 'data', 'users.json')

# Create the Flask application instance.
app = Flask(__name__)

# Use an environment variable for deployment; the fallback is for local development.
app.secret_key = os.environ.get(
    'SECRET_KEY',
    'eventora-development-secret-key-change-before-deployment'
)


# ============================================================
# 3. JSON FILE HANDLING FUNCTIONS
# ============================================================

# Read JSON data from a file. Return an empty list if the file is
# missing, contains invalid JSON, or cannot be read.
def read_json(filename):
    try:
        with open(filename, 'r') as file:
            return json.load(file)

    except FileNotFoundError:
        print(f"File not found: {filename}")
        return []

    except json.JSONDecodeError:
        print(f"Invalid JSON format in: {filename}")
        return []

    except OSError as error:
        print(f"File reading error: {error}")
        return []

# Write Python data to a JSON file. Return True when saving succeeds
# and False when a file-system error occurs.
def write_json(filename, data):

    try:
        with open(filename, 'w') as file:
            json.dump(data, file, indent=4)

        return True

    except OSError as error:
        print(f"File writing error: {error}")
        return False


# ============================================================
# 4. VALIDATION AND EVENT SUMMARY HELPER FUNCTIONS
# ============================================================

# Check whether an email address has a basic valid email format.
def validate_email(email):
    pattern = r'^[\w.-]+@[\w.-]+\.[A-Za-z]{2,}$'
    return re.match(pattern, email) is not None

# Validate an event date and ensure it is today or in the future.
def validate_event_date(event_date):

    try:
        event_date = datetime.strptime(
            event_date, "%Y-%m-%d"
        ).date()

        if event_date < date.today():
            return False

        return True

    except ValueError:
        return False

# Count the confirmed registrations for a particular event.
def count_confirmed(event_id):

    attendees = read_json(ATTENDEES_FILE)

    count = 0

    for attendee in attendees:

        if (attendee['event_id'] == event_id
                and attendee['status'] == 'Confirmed'):

            count += 1

    return count

# Calculate registration counts and expected ticket revenue for an event.
def calculate_event_summary(event, attendees):

    event_attendees = [
        attendee for attendee in attendees
        if attendee.get('event_id') == event.get('id')
    ]

    confirmed = sum(
        1 for attendee in event_attendees
        if attendee.get('status') == 'Confirmed'
    )

    waitlisted = sum(
        1 for attendee in event_attendees
        if attendee.get('status') == 'Waitlisted'
    )

    cancelled = sum(
        1 for attendee in event_attendees
        if attendee.get('status') == 'Cancelled'
    )

    total_registered = confirmed + waitlisted

    ticket_price = float(event.get('ticket_price', 0))

    revenue = confirmed * ticket_price

    return {
        "event_name": event.get('name', 'Unnamed Event'),
        "total_registered": total_registered,
        "confirmed": confirmed,
        "waitlisted": waitlisted,
        "cancelled": cancelled,
        "revenue": revenue
    }


# ============================================================
# 5. AUTHENTICATION AND AUTHORIZATION DECORATORS
# ============================================================

# Require a user to be logged in before accessing a protected route.
def login_required(route_function):

    @wraps(route_function)
    def wrapper(*args, **kwargs):

        if 'user_id' not in session:
            flash("Please login to access this page.", "warning")
            return redirect(url_for('login'))

        return route_function(*args, **kwargs)

    return wrapper

# Restrict a route to users with the specified role (organizer or attendee).
def role_required(required_role):

    def decorator(route_function):

        @wraps(route_function)
        @login_required
        def wrapper(*args, **kwargs):

            if session.get('user_role') != required_role:
                flash("You don't have permission to access this page.", "danger")

                if session.get('user_role') == 'organizer':
                    return redirect(url_for('dashboard'))

                return redirect(url_for('view_events'))

            return route_function(*args, **kwargs)

        return wrapper

    return decorator


# ============================================================
# 6. HOME AND ACCOUNT MANAGEMENT ROUTES
# ============================================================

# Display the Eventora home page.
@app.route('/') #Defines the homepage URL
def home(): #Function executed when homepage is requested
    return render_template('index.html')

# Create a new organizer or attendee account after validating the form.
@app.route('/register-account', methods=['GET', 'POST'])
def register_account():

    if request.method == 'POST':

        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        role = request.form.get('role', '').strip().lower()

        # Validate required fields
        if not name or not email or not password or not confirm_password or not role:
            flash("Please fill in all fields.", "danger")
            return redirect(url_for('register_account'))

        # Validate email
        if not validate_email(email):
            flash("Please enter a valid email address.", "danger")
            return redirect(url_for('register_account'))

        # Validate password
        if len(password) < 8:
            flash("Password must contain at least 8 characters.", "danger")
            return redirect(url_for('register_account'))

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for('register_account'))

        # Validate role
        if role not in ['organizer', 'attendee']:
            flash("Invalid account role.", "danger")
            return redirect(url_for('register_account'))

        users = read_json(USERS_FILE)

        # Check duplicate email
        for user in users:
            if user['email'] == email:
                flash("An account with this email already exists.", "warning")
                return redirect(url_for('register_account'))

        # Generate user ID
        user_id = max(
            [user.get('id', 0) for user in users],
            default=0
        ) + 1

        # Create user
        new_user = {
            "id": user_id,
            "name": name,
            "email": email,
            "password": generate_password_hash(password),
            "role": role,
            "created_at": date.today().isoformat()
        }

        users.append(new_user)

        if write_json(USERS_FILE, users):
            flash("Account created successfully! Please login.", "success")
            return redirect(url_for('login'))

        flash("Unable to create account. Please try again.", "danger")

    return render_template('register.html')

# Authenticate a user and redirect them according to their account role.
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash("Please enter your email and password.", "danger")
            return redirect(url_for('login'))

        users = read_json(USERS_FILE)

        user = next(
            (u for u in users if u['email'] == email),
            None
        )

        if user and check_password_hash(user['password'], password):

            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_email'] = user['email']
            session['user_role'] = user['role']

            flash(f"Welcome back, {user['name']}!", "success")

            if user['role'] == 'organizer':
                return redirect(url_for('dashboard'))

            return redirect(url_for('view_events'))

        flash("Invalid email or password.", "danger")

    return render_template('login.html')

# Clear the current user's session and log them out.
@app.route('/logout')
def logout():

    session.clear()

    flash("You have been logged out successfully.", "success")

    return redirect(url_for('login'))


# ============================================================
# 7. EVENT BROWSING ROUTES
# ============================================================

# Display all available events.
@app.route('/events')
def view_events():

    events = read_json(EVENTS_FILE)

    return render_template('events.html', events=events)

# Display the details page for one selected event.
@app.route('/event/<int:event_id>')
def event_details(event_id):

    events = read_json(EVENTS_FILE)

    selected_event = None

    for event in events:
        if event['id'] == event_id:
            selected_event = event
            break

    if selected_event is None:
        return "Event not found", 404

    return render_template(
        'event_details.html',
        event=selected_event
    )

# Separate events into upcoming and past event lists.
@app.route('/event-categories')
def event_categories():
    events = read_json(EVENTS_FILE)

    upcoming_events = []
    past_events = []

    today = date.today()

    for event in events:
        try:
            event_date = datetime.strptime(
                event['date'], "%Y-%m-%d"
            ).date()

            if event_date >= today:
                upcoming_events.append(event)
            else:
                past_events.append(event)

        except (ValueError, KeyError):
            print(f"Invalid date or missing date for event: {event}")

    upcoming_events.sort(key=lambda event: event['date'])
    past_events.sort(key=lambda event: event['date'], reverse=True)

    return render_template(
        'event_categories.html',
        upcoming_events=upcoming_events,
        past_events=past_events
    )


# ============================================================
# 8. EVENT MANAGEMENT ROUTES (ORGANIZER)
# ============================================================

# Allow an organizer to create an event after validating its details.
@app.route('/create-event', methods=['GET', 'POST'])
@role_required('organizer')
def create_event():
    


    if request.method == 'POST':

        # Receive form data
        name = request.form.get('name', '').strip()
        event_date = request.form.get('date', '').strip()
        venue = request.form.get('venue', '').strip()
        capacity = request.form.get('capacity', '').strip()
        description = request.form.get('description', '').strip()
        ticket_price = request.form.get('ticket_price', '0').strip()

        # Validate required fields
        if not name or not event_date or not venue or not capacity:
            flash("Please fill in all required fields.", "danger")
            return redirect(url_for('create_event'))

        # Validate date
        if not validate_event_date(event_date):
            flash("Please enter a valid future event date.", "danger")
            return redirect(url_for('create_event'))

        # Validate capacity and ticket price
        try:
            capacity = int(capacity)
            ticket_price = float(ticket_price)

            if capacity <= 0 or ticket_price < 0:
                raise ValueError

        except ValueError:
            flash("Enter a valid capacity and ticket price.", "danger")
            return redirect(url_for('create_event'))

        # Read existing events
        events = read_json(EVENTS_FILE)

        # Generate unique event ID
        event_id = max(
            [event.get('id', 0) for event in events],
            default=0
        ) + 1

        # Create event dictionary
        new_event = {
            "id": event_id,
            "name": name,
            "date": event_date,
            "venue": venue,
            "capacity": capacity,
            "description": description,
            "ticket_price": ticket_price
        }

        # Save event
        events.append(new_event)

        if write_json(EVENTS_FILE, events):
            flash("Event created successfully!", "success")
            return redirect(url_for('view_events'))

        flash("Unable to save event. Please try again.", "danger")

        return redirect(url_for('create_event'))

    return render_template('create_event.html')

# Display the organizer dashboard with event, registration, and revenue summaries.
@app.route('/dashboard')
@role_required('organizer')
def dashboard():

    events = read_json(EVENTS_FILE)
    attendees = read_json(ATTENDEES_FILE)

    total_events = len(events)

    total_registrations = sum(
    1 for attendee in attendees
    if attendee.get('status') in ['Confirmed', 'Waitlisted']
    )

    total_confirmed = sum(
    1 for attendee in attendees
    if attendee.get('status') == 'Confirmed'
    )

    total_waitlisted = sum(
    1 for attendee in attendees
    if attendee.get('status') == 'Waitlisted'
    )

    total_cancelled = sum(
    1 for attendee in attendees
    if attendee.get('status') == 'Cancelled'
    )

    event_summaries = []
    total_revenue = 0

    for event in events:

        summary = calculate_event_summary(event, attendees)

        event_summaries.append(summary)

        total_revenue += summary['revenue']

    return render_template(
        'dashboard.html',
        total_events=total_events,
        total_registrations=total_registrations,
        total_confirmed=total_confirmed,
        total_waitlisted=total_waitlisted,
        total_revenue=total_revenue,
        event_summaries=event_summaries,total_cancelled=total_cancelled,
    )


# ============================================================
# 9. RSVP AND REGISTRATION ROUTES (ATTENDEE)
# ============================================================

# Register a logged-in attendee for an event or add them to its waitlist.
@app.route('/register/<int:event_id>', methods=['GET', 'POST'])
@role_required('attendee')
def register_attendee(event_id):

    events = read_json(EVENTS_FILE)

    selected_event = next(
        (event for event in events if event['id'] == event_id),
        None
    )

    if selected_event is None:
        return "Event not found", 404

    if request.method == 'POST':

        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()

        if not name or not email:
            flash("Name and email are required.", "danger")
            return redirect(url_for('register_attendee', event_id=event_id))

        if not validate_email(email):
            flash("Please enter a valid email address.", "danger")
            return redirect(url_for('register_attendee', event_id=event_id))

        if selected_event['date'] < date.today().isoformat():
            flash("Registration is closed for this event.", "danger")
            return redirect(url_for('event_details', event_id=event_id))

        attendees = read_json(ATTENDEES_FILE)

        # Check duplicate registration
        for attendee in attendees:

            if (attendee['event_id'] == event_id
                    and attendee['email'].lower() == email):

                flash("You have already registered for this event.", "warning")

                return redirect(url_for('event_details', event_id=event_id))

        # Determine registration status
        confirmed_count = count_confirmed(event_id)

        if confirmed_count < selected_event['capacity']:
            status = "Confirmed"
        else:
            status = "Waitlisted"

        # Generate registration ID
        attendee_id = max(
            [attendee.get('id', 0) for attendee in attendees],
            default=0
        ) + 1

        # Create attendee record
        new_attendee = {
            "id": attendee_id,
            "event_id": event_id,
            "name": name,
            "email": email,
            "status": status,
            "registration_date": date.today().isoformat()
        }

        attendees.append(new_attendee)

        if write_json(ATTENDEES_FILE, attendees):

            if status == "Confirmed":
                flash("Registration successful! Your seat is confirmed.", "success")
            else:
                flash("Event is full. You have been added to the waitlist.", "warning")

            return redirect(url_for('event_details', event_id=event_id))

        flash("Registration failed. Please try again.", "danger")

    return render_template('rsvp.html', event=selected_event)

# Display all registrations belonging to the currently logged-in attendee.
@app.route('/my-registrations')
@role_required('attendee')
def my_registrations():

    attendees = read_json(ATTENDEES_FILE)
    events = read_json(EVENTS_FILE)

    user_email = session.get('user_email')

    my_registrations = []

    for attendee in attendees:

        if attendee.get('email') == user_email:

            event = next(
                (e for e in events if e['id'] == attendee['event_id']),
                None
            )

            if event:
                my_registrations.append({
                    "registration": attendee,
                    "event": event
                })

    return render_template(
        'my_registrations.html',
        registrations=my_registrations
    )

# Cancel an attendee's registration and promote the earliest waitlisted attendee
# when a confirmed seat becomes available.
@app.route('/cancel-registration/<int:attendee_id>', methods=['POST'])
@role_required('attendee')
def cancel_registration(attendee_id):

    attendees = read_json(ATTENDEES_FILE)

    user_email = session.get('user_email')

    # Find the attendee's registration
    registration = next(
        (
            a for a in attendees
            if a.get('id') == attendee_id
            and a.get('email') == user_email
        ),
        None
    )

    if not registration:
        flash("Registration not found.", "danger")
        return redirect(url_for('my_registrations'))

    if registration.get('status') == 'Cancelled':
        flash("This registration is already cancelled.", "warning")
        return redirect(url_for('my_registrations'))

    previous_status = registration.get('status')

    # Cancel the registration
    registration['status'] = 'Cancelled'

    promoted = False

    # Promote the earliest waitlisted attendee
    if previous_status == 'Confirmed':

        waitlisted = [
            a for a in attendees
            if a.get('event_id') == registration.get('event_id')
            and a.get('status') == 'Waitlisted'
        ]

        if waitlisted:

            next_attendee = min(
                waitlisted,
                key=lambda a: a.get('id', 0)
            )

            next_attendee['status'] = 'Confirmed'
            promoted = True

    # Save changes before showing success message
    if write_json(ATTENDEES_FILE, attendees):

        if promoted:
            flash(
                "Registration cancelled. A waitlisted attendee has been promoted.",
                "success"
            )

        elif previous_status == 'Waitlisted':
            flash(
                "Waitlist registration cancelled successfully.",
                "success"
            )

        else:
            flash(
                "Registration cancelled successfully.",
                "success"
            )

    else:
        flash(
            "Unable to cancel registration. Please try again.",
            "danger"
        )

    return redirect(url_for('my_registrations'))


# ============================================================
# 10. ATTENDEE MANAGEMENT ROUTES (ORGANIZER)
# ============================================================

# Display the attendee and waitlist records for a selected event.
@app.route('/attendees/<int:event_id>')
@role_required('organizer')
def view_attendees(event_id):
    events = read_json(EVENTS_FILE)

    selected_event = next(
        (event for event in events if event['id'] == event_id),
        None
    )

    if selected_event is None:
        return "Event not found", 404

    attendees = read_json(ATTENDEES_FILE)

    event_attendees = [
        attendee for attendee in attendees
        if attendee['event_id'] == event_id
    ]

    return render_template(
        'attendees.html',
        event=selected_event,
        attendees=event_attendees
    )


# ============================================================
# 11. EVENT FEEDBACK ROUTES
# ============================================================

# Allow a logged-in attendee to submit feedback after an event has ended.
@app.route('/feedback/<int:event_id>', methods=['GET', 'POST'])
@role_required('attendee')
def submit_feedback(event_id):

    events = read_json(EVENTS_FILE)

    selected_event = next(
        (event for event in events if event['id'] == event_id),
        None
    )

    if selected_event is None:
        return "Event not found", 404

    # Check whether the event has ended
    try:
        event_date = datetime.strptime(
            selected_event['date'], "%Y-%m-%d"
        ).date()

    except ValueError:
        flash("Invalid event date.", "danger")
        return redirect(url_for('event_details', event_id=event_id))

    if event_date >= date.today():
        flash(
            "Feedback is available only after the event has ended.",
            "warning"
        )
        return redirect(url_for('event_details', event_id=event_id))

    if request.method == 'POST':

        name = request.form.get('name', '').strip()
        rating = request.form.get('rating', '').strip()
        comments = request.form.get('comments', '').strip()

        if not name or not rating:
            flash("Name and rating are required.", "danger")
            return redirect(url_for(
                'submit_feedback', event_id=event_id
            ))

        try:
            rating = int(rating)

            if rating < 1 or rating > 5:
                raise ValueError

        except ValueError:
            flash("Rating must be between 1 and 5.", "danger")
            return redirect(url_for(
                'submit_feedback', event_id=event_id
            ))

        feedback = read_json(FEEDBACK_FILE)

        new_feedback = {
            "id": len(feedback) + 1,
            "event_id": event_id,
            "event_name": selected_event['name'],
            "name": name,
            "rating": rating,
            "comments": comments,
            "submitted_at": date.today().isoformat()
        }

        feedback.append(new_feedback)

        if write_json(FEEDBACK_FILE, feedback):
            flash("Thank you for your feedback!", "success")
            return redirect(url_for(
                'event_details', event_id=event_id
            ))

        flash("Unable to save feedback.", "danger")

    return render_template(
        'feedback.html',
        event=selected_event
    )

# Display feedback and the average rating for an event to an organizer.
@app.route('/feedbacks/<int:event_id>')
@role_required('organizer')
def view_feedback(event_id):

    events = read_json(EVENTS_FILE)

    selected_event = next(
        (event for event in events if event['id'] == event_id),
        None
    )

    if selected_event is None:
        return "Event not found", 404

    all_feedback = read_json(FEEDBACK_FILE)

    event_feedback = [
        item for item in all_feedback
        if item['event_id'] == event_id
    ]

    total_feedback = len(event_feedback)

    average_rating = (
        round(
            sum(item['rating'] for item in event_feedback)
            / total_feedback, 1
        )
        if total_feedback > 0 else 0
    )

    return render_template(
        'view_feedback.html',
        event=selected_event,
        feedbacks=event_feedback,
        total_feedback=total_feedback,
        average_rating=average_rating
    )


# ============================================================
# 12. APPLICATION ENTRY POINT
# ============================================================

# Start Flask's development server when this file is run directly.
if __name__ == '__main__':
    app.run(debug=True)
