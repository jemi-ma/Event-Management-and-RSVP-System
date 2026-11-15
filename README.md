# Event Management & RSVP System

## Project Overview

The Event Management & RSVP System is a web-based application developed using Python Flask. It helps users create and manage events, register attendees, monitor event capacity, and track registrations.

The application provides a centralized platform for managing college events, workshops, weddings, and other gatherings.

## Technologies Used

- Python
- Flask
- HTML5
- CSS3
- JavaScript
- JSON for file-based data storage

## Features

### 1. Event Management
- Create new events.
- Enter event name, date, venue, capacity, ticket price, and description.
- View available events.

### 2. RSVP Registration
- Register attendees for events.
- Validate attendee information.
- Prevent duplicate registrations.
- Check event capacity automatically.

### 3. Waitlist Management
- Confirm registrations when seats are available.
- Add additional registrations to the waitlist when an event is full.

### 4. Attendee Management
- View registered attendees.
- Display attendee details and registration status.

### 5. Event Categorization
- Display upcoming events.
- Display past events based on event dates.

### 6. Dashboard
- Display total events.
- Display total registrations.
- Track confirmed and waitlisted attendees.
- Calculate estimated event revenue.

### 7. Feedback System
- Collect attendee feedback.
- Allow users to provide ratings and comments.

### 8. Input Validation and Exception Handling
- Validate user inputs.
- Handle invalid dates and numerical values.
- Handle JSON file errors.

## Project Structure

```text
event_management_and_RSVP_system_using_flask/
│
├── app.py
├── requirements.txt
├── README.md
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
│   └── feedback.html
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
│   └── feedback.json
│
└── venv/
```

## Installation and Setup

### Step 1: Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
```

### Step 2: Navigate to the project directory

```bash
cd event_management_and_RSVP_system_using_flask
```

### Step 3: Create a virtual environment

```bash
python -m venv venv
```

### Step 4: Activate the virtual environment

Windows:

```bash
venv\Scripts\activate
```

### Step 5: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 6: Run the application

```bash
python app.py
```

### Step 7: Open the application

Visit:

http://127.0.0.1:5000/

## Data Storage

The application uses JSON files to store event information, attendee registrations, and feedback.

This provides simple file-based storage without requiring a separate database server.

## Future Enhancements

- Email-based event confirmation.
- Calendar integration.
- Online payment integration.
- User authentication and authorization.
- Automated waitlist promotion.
- Database integration using MySQL or SQLite.

## Author

Developed as a Python Flask mini project.