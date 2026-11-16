
from flask import Flask ,render_template,request, redirect, url_for, flash#Imports Flask framework
import json, os
from datetime import datetime, date
import re


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EVENTS_FILE = os.path.join(BASE_DIR, 'data', 'events.json')
ATTENDEES_FILE = os.path.join(BASE_DIR, 'data', 'attendees.json')
FEEDBACK_FILE = os.path.join(BASE_DIR, 'data', 'feedback.json')


# Creating Flask application
app = Flask(__name__) #Creates application instance
app.secret_key = 'event-management-secret-key'


# Home route
@app.route('/') #Defines the homepage URL
def home(): #Function executed when homepage is requested
    return render_template('index.html')

@app.route('/events')
def view_events():

    events = read_json(EVENTS_FILE)

    return render_template('events.html', events=events)

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


@app.route('/register/<int:event_id>', methods=['GET', 'POST'])
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

@app.route('/attendees/<int:event_id>')
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

@app.route('/dashboard')
def dashboard():

    events = read_json(EVENTS_FILE)
    attendees = read_json(ATTENDEES_FILE)

    total_events = len(events)
    total_registrations = len(attendees)

    total_confirmed = sum(
        1 for attendee in attendees
        if attendee.get('status') == 'Confirmed'
    )

    total_waitlisted = sum(
        1 for attendee in attendees
        if attendee.get('status') == 'Waitlisted'
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
        event_summaries=event_summaries
    )
@app.route('/feedback/<int:event_id>', methods=['GET', 'POST'])
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


@app.route('/feedbacks/<int:event_id>')
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

def count_confirmed(event_id):

    attendees = read_json(ATTENDEES_FILE)

    count = 0

    for attendee in attendees:

        if (attendee['event_id'] == event_id
                and attendee['status'] == 'Confirmed'):

            count += 1

    return count

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

    total_registered = len(event_attendees)

    ticket_price = float(event.get('ticket_price', 0))

    revenue = confirmed * ticket_price

    return {
        "event_name": event.get('name', 'Unnamed Event'),
        "total_registered": total_registered,
        "confirmed": confirmed,
        "waitlisted": waitlisted,
        "revenue": revenue
    }

def validate_email(email):
    pattern = r'^[\w.-]+@[\w.-]+\.[A-Za-z]{2,}$'
    return re.match(pattern, email) is not None

# Function to read JSON data
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

# Function to write JSON data
def write_json(filename, data):

    try:
        with open(filename, 'w') as file:
            json.dump(data, file, indent=4)

        return True

    except OSError as error:
        print(f"File writing error: {error}")
        return False

#date validation function
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


@app.route('/create-event', methods=['GET', 'POST'])
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

# Run the application
if __name__ == '__main__':
    app.run(debug=True)	#Starts development server