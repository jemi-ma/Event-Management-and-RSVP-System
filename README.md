# Eventora – Event Management & RSVP System

Eventora is a web-based Event Management and RSVP System developed using Python and Flask. It provides a simple platform for organizers to create and manage events while allowing attendees to explore events, register, manage their registrations, and submit feedback.

The project demonstrates Python programming concepts, Flask application development, JSON-based file handling, user authentication, and role-based access control.

## Features

### User Management
- User registration and login.
- Secure password hashing.
- Session-based authentication.
- Role-based access for organizers and attendees.
- Logout functionality.

### Event Management
- Create and manage events.
- View upcoming and past events.
- Display event details, venue, date, capacity, and ticket price.
- Event capacity management.

### RSVP and Registration
- Register for events.
- Prevent duplicate registrations.
- Confirm registrations based on available capacity.
- Automatically add attendees to a waitlist when an event is full.
- View personal registrations.
- Cancel registrations.
- Automatically promote a waitlisted attendee when a confirmed registration is cancelled.

### Organizer Dashboard
- View event statistics.
- Track total registrations, confirmed registrations, waitlisted attendees, and cancellations.
- Calculate event revenue.
- View attendee information.
- Search attendees by name or email.
- Filter attendees by registration status.

### Feedback Management
- Submit feedback for completed events.
- Provide ratings and comments.
- View feedback submitted for individual events.
- Calculate average event ratings.

## User Roles

| Role | Access |
|---|---|
| Organizer | Create events, access the dashboard, view attendees, and manage event feedback. |
| Attendee | Explore events, register, view personal registrations, and cancel registrations. |
| Public Visitor | Browse available events and view event details. |

## Technologies Used

- **Programming Language:** Python
- **Backend Framework:** Flask
- **Frontend:** HTML, CSS, JavaScript
- **Templating Engine:** Jinja2
- **Data Storage:** JSON files
- **Authentication:** Flask Sessions and Werkzeug Password Hashing
- **Development Environment:** Visual Studio Code

## Project Structure

```text
Event-Management-and-RSVP-System/
│
├── app.py
│
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── create_event.html
│   ├── events.html
│   ├── event_details.html
│   ├── rsvp.html
│   ├── attendees.html
│   ├── event_categories.html
│   ├── dashboard.html
│   ├── feedback.html
│   ├── view_feedback.html
│   ├── register.html
│   ├── login.html
│   └── my_registrations.html
│
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── script.js
│   └── images/
│
├── data/
│   ├── events.json
│   ├── attendees.json
│   ├── feedback.json
│   └── users.json
│
├── requirements.txt
├── README.md
└── .gitignore
```

## Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/jemi-ma/Event-Management-and-RSVP-System.git
```

### 2. Navigate to the Project Directory

```bash
cd Event-Management-and-RSVP-System
```

### 3. Create a Virtual Environment

```bash
python -m venv venv
```

### 4. Activate the Virtual Environment

For Windows:

```bash
venv\Scripts\activate
```

### 5. Install Dependencies

```bash
pip install -r requirements.txt
```

### 6. Run the Application

```bash
python app.py
```

### 7. Open in Browser

Visit:

```text
http://127.0.0.1:5000/
```

## Data Storage

Eventora uses JSON files for storing application data:

- `events.json` – Event information.
- `attendees.json` – Event registration details.
- `feedback.json` – Event feedback and ratings.
- `users.json` – User account information.

This project uses JSON-based storage instead of a relational database to demonstrate file handling and data manipulation using Python.

## Python Concepts Demonstrated

- Functions and modular programming.
- Lists and dictionaries.
- File handling and JSON operations.
- Exception handling.
- Conditional statements and loops.
- Data validation.
- Decorators.
- Password hashing.
- Session management.
- Flask routing and request handling.

## Future Enhancements

- Database integration using MySQL or MongoDB.
- Email notifications for event registrations.
- Enhanced user profile management.
- Improved event administration features.

## Author

**Jemima Asok**

GitHub: https://github.com/jemi-ma

---

*Eventora – Making event management simpler.*