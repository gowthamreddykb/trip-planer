# Trip Planner — Web Application

A travel planning and exploration platform built with **Python 3, Flask, MySQL, and Bootstrap 5**. Trip Planner enables travelers to create and manage private day-by-day itineraries, track budgets automatically with real-time recalculations, explore verified destination guides, and submit multi-place travel recommendations.

---

## 1. Project Overview

Trip Planner turns travel ideas into structured, actionable itineraries. Users can browse destination highlights, add them directly to their own custom trips, organize daily activities by morning/afternoon/evening, and monitor travel expenses against their target budgets. The platform also empowers the community to suggest multiple attractions for any destination in a single multi-place submission.

---

## 2. Key Features

1. **Secure Authentication & Ownership**:
   - Registration, login, and session persistence with Werkzeug password hashing.
   - Private trip and activity isolation: users can only view, edit, or delete their own trips.
   - Admin moderation dashboard for reviewing community place submissions.

2. **Trip & Budget Management**:
   - Create, edit, and delete trips with destination, start date, end date, and target budget.
   - Automatic calculation of total activity costs, remaining funds, or over-budget amounts.
   - Date protection: editing trip dates checks all existing activities and blocks date contractions that would leave activities outside the trip range.

3. **Day-wise Itineraries**:
   - Activities grouped by date into intuitive day tabs (e.g., Day 1, Day 2).
   - Activity categories (Nature, Beach, Historical, Mountain, Adventure, Food, Culture).
   - Add activities directly from the Explore catalog with one click.

4. **Explore & Discovery**:
   - Filter places by category pills and search by keyword simultaneously.
   - Rich Place Details view showing best time to visit, recommended duration, cost range, photo gallery, local cuisine, travel tips, and suggested 2-day itineraries.

5. **Multi-Place Submission (Single Form)**:
   - Submit multiple places under one destination in a single request.
   - Repeating place cards with independent image uploads, previews, categories, and descriptions.
   - Shared destination details (region, overview, tips, local food).

---

## 3. Technology Stack

- **Backend**: Python 3.10+ / Flask 3.1.3
- **Database**: MySQL 8.0 / MariaDB
- **Connector**: `mysql-connector-python` 26.7.0
- **Security & Templates**: Werkzeug 3.1.9, Jinja2 3.1.6, itsdangerous 2.2.0, MarkupSafe 3.0.3, blinker 1.9.0, click 8.5.0
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5.3, Bootstrap Icons 1.11
- **Testing**: `pytest` 9.1+

---

## 4. Project Folder Structure

```
trip_planner/
├── app.py                      # Main Flask application and route controllers
├── config.py                   # Configuration and environment variables
├── db.py                       # MySQL connection pool and query helpers
├── schema.sql                  # 6-table database schema & seed data
├── requirements.txt            # Python dependencies
├── .env.example                # Example environment configuration
├── .gitignore                  # Git ignore rules
├── README.md                   # Complete documentation
│
├── static/
│   ├── css/
│   │   └── style.css           # Travel journal aesthetic stylesheet
│   ├── js/
│   │   ├── main.js             # General UI interactivity & validations
│   │   └── places.js           # Multi-place repeating form manager
│   ├── images/                 # Static graphical assets
│   └── uploads/
│       └── places/             # User-uploaded place photographs
│
├── templates/
│   ├── base.html               # Base layout with dark teal navbar & footer
│   ├── home.html               # Landing page with hero & popular destinations
│   ├── explore.html            # Public places catalog with filters
│   ├── place_details.html      # Detailed place guide & Add-to-Trip modal
│   ├── suggest_places.html     # Repeating multi-place submission form
│   ├── 403.html                # Access Denied / Validation error page
│   ├── 404.html                # Not Found page
│   ├── 500.html                # Internal Server Error page
│   │
│   ├── auth/
│   │   ├── login.html          # Login form with demo accounts
│   │   └── register.html       # User registration form
│   │
│   ├── trips/
│   │   ├── my_trips.html       # Dashboard of user-owned trips
│   │   ├── trip_form.html      # Create and edit trip form
│   │   ├── trip_detail.html    # Day-wise itinerary and budget overview
│   │   └── activity_form.html  # Add and edit activity form
│   │
│   └── admin/
│       └── place_suggestions.html # Moderation queue for submissions
│
└── tests/
    ├── conftest.py             # Pytest configuration and fixtures
    ├── test_auth.py            # Authentication & session tests
    ├── test_trips.py           # Trip CRUD and privacy enforcement tests
    ├── test_activities.py      # Day activity & budget recalculation tests
    └── test_places.py          # Multi-place submission and explore tests
```

---

## 5. Setup & Installation

### Step 1: Clone & Virtual Environment
```bash
git clone <repository_url>
cd trip_planner
python3 -m venv venv
source venv/bin/activate
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: MySQL Database Setup
Log in to your MySQL server and run:
```sql
CREATE DATABASE trip_planner CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Execute `schema.sql`:
```bash
mysql -u root -p trip_planner < schema.sql
```

### Step 4: Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Update database credentials and `SECRET_KEY` in `.env`.

### Step 5: Creating the First Administrator
The database schema seeds an initial administrator:
- **Username**: `admin`
- **Email**: `admin@tripplanner.com`
- **Password**: `admin123`

To promote an existing registered user to administrator directly in MySQL:
```sql
UPDATE users SET role = 'admin' WHERE username = 'your_username';
```

---

## 6. Running the Application

Start the Flask server:
```bash
python3 app.py
```
Access the application in your browser at `http://localhost:3000` (or `http://localhost:5000`).

---

## 7. Running Automated Tests

Run the full pytest suite with verbose output:
```bash
PYTHONPATH=. pytest -v
```

All 21 unit and integration tests will execute and verify authentication, trip access control, budget recalculations, multi-place submissions, and moderation rules.

---

## 8. Common Errors & Solutions

1. **Access Denied (403)**:
   - Occurs when attempting to view or edit another user's private trip ID. Trips are strictly owned by their creator.
2. **Date Constraint Error**:
   - Activities must have dates between the trip's start date and end date.
   - Modifying a trip's dates is blocked if existing activities would fall outside the new date range.
3. **Database Connection Refused**:
   - Verify that your MySQL server (`service mariadb status` or `service mysql status`) is running on port 3306.
# trip-planer
2ca0f9ff17cbe9fae29ded05a1270450d28ad2ac
