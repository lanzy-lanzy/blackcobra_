# Karate Club Management System

This is a comprehensive management system for a Karate club, built with Django. It includes features for managing trainees, events, matches, billing, and more. The frontend is built with a modern, lightweight stack using Tailwind CSS, Alpine.js, and HTMX.

This README provides a spec-driven guide for an AI agent to set up, run, and understand the project.

## Features

-   **Trainee Management:** Add, edit, and manage trainee information.
-   **Event Management:** Create, manage, and view details of events and tournaments.
-   **Match Management:** Schedule, score, and manage matches.
-   **Billing and Payments:** Manage fees, payments, and billing for trainees.
-   **Belt Promotions:** Track and manage trainee belt promotions.
-   **User Roles:** Different portals for Admins, Judges, and Trainees.
-   **Reporting:** Generate reports for events and other activities.

## Tech Stack

-   **Backend:**
    -   Python 3.11
    -   Django 5.2
-   **Frontend:**
    -   Tailwind CSS (via CDN)
    -   Alpine.js
    -   HTMX
-   **Database:**
    -   SQLite3 (for development)

## Prerequisites

-   Python 3.11 or later
-   Git

## Setup & Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd KarateClub_
    ```

2.  **Set up Python environment:**
    -   Create and activate a virtual environment:
        ```bash
        python -m venv venv
        source venv/bin/activate  # On Windows use `venv\Scripts\activate`
        ```
    -   Install Python dependencies:
        ```bash
        pip install -r requirements.txt
        ```

3.  **Set up the database:**
    -   Run database migrations:
        ```bash
        python manage.py migrate
        ```

4.  **Create a superuser (admin):**
    ```bash
    python manage.py createsuperuser
    ```

## Running the Application

1.  **Start the Django development server:**
    ```bash
    python manage.py runserver
    ```
    The application will be available at `http://127.0.0.1:8000/`.

## Running Tests

-   **Django Tests:**
    ```bash
    python manage.py test black_cobra_judo
    ```

## Key Files & Directories

-   `manage.py`: Django's command-line utility for administrative tasks.
-   `requirements.txt`: Python dependencies.
-   `KarateClub_/`: The main Django project directory.
    -   `settings.py`: Django project settings.
    -   `urls.py`: Main URL configuration.
-   `black_cobra_judo/`: The core Django app for the Karate Club.
    -   `models.py`: Database models.
    -   `views.py`: Application views (request handlers).
    -   `urls.py`: App-specific URL patterns.
-   `templates/`: Django HTML templates, including Tailwind CSS, Alpine.js, and HTMX integration.
-   `static/`: Static files (CSS, JS, images).
-   `db.sqlite3` / `db_new.sqlite3`: SQLite database files.