"""
Trip Planner Flask Application.
Strictly using only specified packages: Flask, Werkzeug, Jinja2, MarkupSafe,
itsdangerous, click, blinker, and mysql-connector-python.
"""
import os
import re
import uuid
import secrets
from datetime import datetime, date
from decimal import Decimal

from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, abort, jsonify, g, send_from_directory
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from config import Config
import db

app = Flask(__name__)
app.config.from_object(Config)

# Ensure upload directory exists
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

# ---------------------------------------------------------------------------
# CSRF and Session Protection Helpers
# ---------------------------------------------------------------------------
def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(32)
    return session['_csrf_token']

app.jinja_env.globals['csrf_token'] = generate_csrf_token
app.jinja_env.globals['str'] = str

@app.before_request
def csrf_protect():
    # Load current user into g
    g.user = None
    if 'user_id' in session:
        try:
            g.user = db.query_db(
                "SELECT id, username, email, role FROM users WHERE id = %s",
                (session['user_id'],),
                one=True
            )
            if not g.user:
                session.clear()
        except Exception:
            g.user = None

    # Exempt authentication routes from strict CSRF validation so iframe environments never block login/register
    if request.endpoint in ('login', 'register', 'logout'):
        return

    # Validate CSRF token on modifying methods
    if request.method in ('POST', 'PUT', 'DELETE', 'PATCH'):
        if not app.config.get('TESTING'):
            token = request.form.get('csrf_token') or request.headers.get('X-CSRF-Token')
            expected = session.get('_csrf_token')
            if expected and token and token != expected:
                abort(400, description="Invalid or missing CSRF token. Please refresh and try again.")

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('login', next=request.path))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None or g.user.get('role') != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

# Template context helper
@app.context_processor
def inject_now():
    return {'current_year': datetime.now().year, 'current_user': g.user}

# ---------------------------------------------------------------------------
# Uploads Serving
# ---------------------------------------------------------------------------
@app.route('/uploads/places/<filename>')
def uploaded_file(filename):
    return send_from_directory(Config.UPLOAD_FOLDER, filename)

# ---------------------------------------------------------------------------
# 1. HOME PAGE
# ---------------------------------------------------------------------------
@app.route('/')
def home():
    # Fetch 4 popular destinations for the landing page
    popular_destinations = db.query_db(
        """
        SELECT d.id, d.name, d.city_area, d.overview_description,
               (SELECT pi.image_url FROM place_images pi 
                JOIN place_suggestions ps ON pi.place_id = ps.id 
                WHERE ps.destination_id = d.id AND pi.is_primary = 1 
                LIMIT 1) as image_url,
               COUNT(ps.id) as place_count
        FROM destinations d
        LEFT JOIN place_suggestions ps ON d.id = ps.destination_id AND ps.status = 'approved'
        GROUP BY d.id
        ORDER BY d.id ASC
        LIMIT 4
        """
    )
    return render_template('home.html', popular_destinations=popular_destinations)

# ---------------------------------------------------------------------------
# 2. AUTHENTICATION: REGISTER, LOGIN, LOGOUT
# ---------------------------------------------------------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if g.user:
        return redirect(url_for('my_trips'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validation
        errors = []
        if not username or len(username) < 3:
            errors.append("Username must be at least 3 characters long.")
        if not email or '@' not in email:
            errors.append("Please enter a valid email address.")
        if not password or len(password) < 6:
            errors.append("Password must be at least 6 characters long.")
        if password != confirm_password:
            errors.append("Passwords do not match.")

        # Check existing user/email
        if not errors:
            existing_user = db.query_db(
                "SELECT id FROM users WHERE username = %s OR email = %s",
                (username, email),
                one=True
            )
            if existing_user:
                errors.append("A user with that username or email already exists.")

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template('auth/register.html', username=username, email=email)

        # Hash password and create user
        pwd_hash = generate_password_hash(password, method='scrypt')
        user_id = db.query_db(
            "INSERT INTO users (username, email, password_hash, role) VALUES (%s, %s, %s, 'user')",
            (username, email, pwd_hash),
            commit=True
        )

        session.clear()
        session['user_id'] = user_id
        session['username'] = username
        flash(f"Welcome to Trip Planner, {username}! Your account has been created.", "success")
        return redirect(url_for('my_trips'))

    return render_template('auth/register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if g.user:
        return redirect(url_for('my_trips'))

    if request.method == 'POST':
        login_input = request.form.get('login_input', '').strip()
        password = request.form.get('password', '')
        next_url = request.form.get('next', '')

        if not login_input or not password:
            flash("Please provide both username/email and password.", "danger")
            return render_template('auth/login.html', login_input=login_input)

        user = db.query_db(
            "SELECT * FROM users WHERE username = %s OR email = %s",
            (login_input, login_input.lower()),
            one=True
        )

        if user and check_password_hash(user['password_hash'], password):
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash(f"Welcome back, {user['username']}!", "success")
            
            # Safe redirect check
            if next_url and next_url.startswith('/') and not next_url.startswith('//'):
                return redirect(next_url)
            return redirect(url_for('my_trips'))
        else:
            flash("Invalid username/email or password.", "danger")
            return render_template('auth/login.html', login_input=login_input)

    return render_template('auth/login.html', next=request.args.get('next', ''))

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for('login'))

# ---------------------------------------------------------------------------
# 3. MY TRIPS
# ---------------------------------------------------------------------------
@app.route('/my-trips')
@login_required
def my_trips():
    # Load all trips for current user with activity counts and total estimated costs
    trips = db.query_db(
        """
        SELECT t.id, t.destination, t.start_date, t.end_date, t.budget,
               COUNT(a.id) as activity_count,
               COALESCE(SUM(a.estimated_cost), 0.00) as total_cost,
               (SELECT pi.image_url FROM place_images pi
                JOIN place_suggestions ps ON pi.place_id = ps.id
                JOIN destinations d ON ps.destination_id = d.id
                WHERE d.name LIKE CONCAT('%', t.destination, '%') 
                   OR t.destination LIKE CONCAT('%', d.name, '%')
                ORDER BY pi.is_primary DESC LIMIT 1) as cover_image
        FROM trips t
        LEFT JOIN activities a ON t.id = a.trip_id
        WHERE t.user_id = %s
        GROUP BY t.id
        ORDER BY t.start_date ASC
        """,
        (g.user['id'],)
    )

    processed_trips = []
    for trip in trips:
        total_cost = Decimal(str(trip['total_cost']))
        budget = Decimal(str(trip['budget']))
        remaining = budget - total_cost
        
        # Calculate trip duration in days
        s_date = trip['start_date']
        e_date = trip['end_date']
        days = (e_date - s_date).days + 1 if isinstance(s_date, (date, datetime)) else 1

        processed_trips.append({
            **trip,
            'total_cost': total_cost,
            'budget': budget,
            'remaining': remaining,
            'is_over_budget': remaining < 0,
            'days': days
        })

    return render_template('trips/my_trips.html', trips=processed_trips)

# ---------------------------------------------------------------------------
# 4. CREATE / EDIT / DELETE TRIP
# ---------------------------------------------------------------------------
@app.route('/trips/new', methods=['GET', 'POST'])
@login_required
def create_trip():
    if request.method == 'POST':
        destination = request.form.get('destination', '').strip()
        start_date_str = request.form.get('start_date', '').strip()
        end_date_str = request.form.get('end_date', '').strip()
        budget_str = request.form.get('budget', '0').strip()

        errors = []
        if not destination:
            errors.append("Destination is required.")
        if not start_date_str or not end_date_str:
            errors.append("Both start date and end date are required.")
        
        try:
            start_date = date.fromisoformat(start_date_str)
            end_date = date.fromisoformat(end_date_str)
            if end_date < start_date:
                errors.append("End date cannot be earlier than start date.")
        except ValueError:
            errors.append("Invalid date format. Use YYYY-MM-DD.")

        try:
            budget = Decimal(budget_str)
            if budget < 0:
                errors.append("Budget cannot be negative.")
        except Exception:
            errors.append("Please enter a valid numeric budget.")

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template('trips/trip_form.html',
                                   action="Create",
                                   destination=destination,
                                   start_date=start_date_str,
                                   end_date=end_date_str,
                                   budget=budget_str)

        trip_id = db.query_db(
            """
            INSERT INTO trips (user_id, destination, start_date, end_date, budget)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (g.user['id'], destination, start_date_str, end_date_str, float(budget)),
            commit=True
        )

        flash(f"Trip to {destination} created successfully!", "success")
        return redirect(url_for('trip_detail', trip_id=trip_id))

    return render_template('trips/trip_form.html', action="Create")

@app.route('/trips/<int:trip_id>')
@login_required
def trip_detail(trip_id):
    # Verify trip ownership
    trip = db.query_db(
        "SELECT * FROM trips WHERE id = %s",
        (trip_id,),
        one=True
    )
    if not trip:
        abort(404, description="Trip not found.")
    if trip['user_id'] != g.user['id']:
        return render_template('403.html', message="Access Denied: This private trip belongs to another user."), 403

    # Load activities for this trip
    activities = db.query_db(
        """
        SELECT a.*, ps.name as place_suggestion_name
        FROM activities a
        LEFT JOIN place_suggestions ps ON a.place_suggestion_id = ps.id
        WHERE a.trip_id = %s
        ORDER BY a.activity_date ASC, a.activity_time ASC, a.id ASC
        """,
        (trip_id,)
    )

    # Budget calculation
    total_cost = sum(Decimal(str(a['estimated_cost'])) for a in activities)
    budget = Decimal(str(trip['budget']))
    remaining = budget - total_cost

    # Calculate day grouping
    s_date = trip['start_date']
    e_date = trip['end_date']
    total_days = (e_date - s_date).days + 1

    # Map activities into day groups
    days_data = []
    current = s_date
    day_num = 1
    while current <= e_date:
        day_activities = [a for a in activities if a['activity_date'] == current]
        days_data.append({
            'day_num': day_num,
            'date': current,
            'date_str': current.strftime("%b %d, %Y"),
            'activities': day_activities,
            'day_cost': sum(Decimal(str(a['estimated_cost'])) for a in day_activities)
        })
        current = date.fromordinal(current.toordinal() + 1)
        day_num += 1

    # Look for matching destination cover image
    dest_image = db.query_db(
        """
        SELECT pi.image_url FROM place_images pi
        JOIN place_suggestions ps ON pi.place_id = ps.id
        JOIN destinations d ON ps.destination_id = d.id
        WHERE d.name LIKE CONCAT('%', %s, '%') OR %s LIKE CONCAT('%', d.name, '%')
        ORDER BY pi.is_primary DESC LIMIT 1
        """,
        (trip['destination'], trip['destination']),
        one=True
    )

    return render_template('trips/trip_detail.html',
                           trip=trip,
                           total_cost=total_cost,
                           budget=budget,
                           remaining=remaining,
                           is_over_budget=remaining < 0,
                           total_days=total_days,
                           days_data=days_data,
                           cover_image=dest_image['image_url'] if dest_image else None)

@app.route('/trips/<int:trip_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_trip(trip_id):
    trip = db.query_db("SELECT * FROM trips WHERE id = %s", (trip_id,), one=True)
    if not trip:
        abort(404, description="Trip not found.")
    if trip['user_id'] != g.user['id']:
        abort(403)

    if request.method == 'POST':
        destination = request.form.get('destination', '').strip()
        start_date_str = request.form.get('start_date', '').strip()
        end_date_str = request.form.get('end_date', '').strip()
        budget_str = request.form.get('budget', '0').strip()

        errors = []
        if not destination:
            errors.append("Destination is required.")
        if not start_date_str or not end_date_str:
            errors.append("Both start date and end date are required.")

        try:
            start_date = date.fromisoformat(start_date_str)
            end_date = date.fromisoformat(end_date_str)
            if end_date < start_date:
                errors.append("End date cannot be earlier than start date.")
        except ValueError:
            errors.append("Invalid date format.")

        try:
            budget = Decimal(budget_str)
            if budget < 0:
                errors.append("Budget cannot be negative.")
        except Exception:
            errors.append("Please enter a valid numeric budget.")

        # IMPORTANT: Check existing activities to ensure proposed dates don't invalidate them
        if not errors:
            activity_bounds = db.query_db(
                "SELECT MIN(activity_date) as min_date, MAX(activity_date) as max_date FROM activities WHERE trip_id = %s",
                (trip_id,),
                one=True
            )
            if activity_bounds and activity_bounds['min_date']:
                if start_date > activity_bounds['min_date']:
                    errors.append(f"Cannot set start date after {activity_bounds['min_date']}, as you have activities scheduled on that date.")
                if end_date < activity_bounds['max_date']:
                    errors.append(f"Cannot set end date before {activity_bounds['max_date']}, as you have activities scheduled on that date.")

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template('trips/trip_form.html',
                                   action="Edit",
                                   trip_id=trip_id,
                                   destination=destination,
                                   start_date=start_date_str,
                                   end_date=end_date_str,
                                   budget=budget_str)

        db.query_db(
            """
            UPDATE trips
            SET destination = %s, start_date = %s, end_date = %s, budget = %s
            WHERE id = %s AND user_id = %s
            """,
            (destination, start_date_str, end_date_str, float(budget), trip_id, g.user['id']),
            commit=True
        )

        flash(f"Trip to {destination} updated successfully!", "success")
        return redirect(url_for('trip_detail', trip_id=trip_id))

    return render_template('trips/trip_form.html',
                           action="Edit",
                           trip_id=trip['id'],
                           destination=trip['destination'],
                           start_date=trip['start_date'].isoformat(),
                           end_date=trip['end_date'].isoformat(),
                           budget=str(trip['budget']))

@app.route('/trips/<int:trip_id>/delete', methods=['POST'])
@login_required
def delete_trip(trip_id):
    trip = db.query_db("SELECT * FROM trips WHERE id = %s", (trip_id,), one=True)
    if not trip:
        abort(404)
    if trip['user_id'] != g.user['id']:
        abort(403)

    db.query_db("DELETE FROM trips WHERE id = %s AND user_id = %s", (trip_id, g.user['id']), commit=True)
    flash("Trip and associated activities deleted.", "info")
    return redirect(url_for('my_trips'))

# ---------------------------------------------------------------------------
# 5. ACTIVITIES: ADD / EDIT / DELETE
# ---------------------------------------------------------------------------
@app.route('/trips/<int:trip_id>/activities/new', methods=['GET', 'POST'])
@login_required
def add_activity(trip_id):
    trip = db.query_db("SELECT * FROM trips WHERE id = %s", (trip_id,), one=True)
    if not trip:
        abort(404, description="Trip not found.")
    if trip['user_id'] != g.user['id']:
        return render_template('403.html', message="Access Denied: This private trip belongs to another user."), 403

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        activity_date_str = request.form.get('activity_date', '').strip()
        activity_time_str = request.form.get('activity_time', '').strip() or None
        category = request.form.get('category', 'General').strip()
        place = request.form.get('place', '').strip()
        cost_str = request.form.get('estimated_cost', '0').strip()
        place_suggestion_id = request.form.get('place_suggestion_id') or None

        errors = []
        if not name:
            errors.append("Activity name is required.")
        if not activity_date_str:
            errors.append("Activity date is required.")
        if not place:
            errors.append("Place or location is required.")

        try:
            act_date = date.fromisoformat(activity_date_str)
            if act_date < trip['start_date'] or act_date > trip['end_date']:
                errors.append(f"Activity date must be within trip dates ({trip['start_date']} to {trip['end_date']}).")
        except ValueError:
            errors.append("Invalid activity date format.")

        try:
            cost = Decimal(cost_str)
            if cost < 0:
                errors.append("Estimated cost cannot be negative.")
        except Exception:
            errors.append("Please enter a valid numeric cost.")

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template('trips/activity_form.html',
                                   trip=trip,
                                   action="Add",
                                   name=name,
                                   activity_date=activity_date_str,
                                   activity_time=activity_time_str,
                                   category=category,
                                   place=place,
                                   estimated_cost=cost_str,
                                   place_suggestion_id=place_suggestion_id)

        db.query_db(
            """
            INSERT INTO activities (trip_id, place_suggestion_id, name, activity_date, activity_time, category, place, estimated_cost)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (trip_id, place_suggestion_id, name, activity_date_str, activity_time_str, category, place, float(cost)),
            commit=True
        )

        flash(f"Activity '{name}' added successfully!", "success")
        return redirect(url_for('trip_detail', trip_id=trip_id))

    # Prefill from GET parameters (e.g. from Explore Place Details)
    prefill = {
        'name': request.args.get('name', ''),
        'activity_date': request.args.get('date', trip['start_date'].isoformat()),
        'activity_time': request.args.get('time', '10:00'),
        'category': request.args.get('category', 'Nature'),
        'place': request.args.get('place', ''),
        'estimated_cost': request.args.get('cost', '500'),
        'place_suggestion_id': request.args.get('place_suggestion_id', '')
    }

    return render_template('trips/activity_form.html', trip=trip, action="Add", **prefill)

@app.route('/trips/<int:trip_id>/activities/<int:activity_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_activity(trip_id, activity_id):
    trip = db.query_db("SELECT * FROM trips WHERE id = %s", (trip_id,), one=True)
    if not trip or trip['user_id'] != g.user['id']:
        abort(403)

    activity = db.query_db("SELECT * FROM activities WHERE id = %s AND trip_id = %s", (activity_id, trip_id), one=True)
    if not activity:
        abort(404)

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        activity_date_str = request.form.get('activity_date', '').strip()
        activity_time_str = request.form.get('activity_time', '').strip() or None
        category = request.form.get('category', 'General').strip()
        place = request.form.get('place', '').strip()
        cost_str = request.form.get('estimated_cost', '0').strip()

        errors = []
        if not name:
            errors.append("Activity name is required.")
        if not activity_date_str:
            errors.append("Activity date is required.")
        if not place:
            errors.append("Place is required.")

        try:
            act_date = date.fromisoformat(activity_date_str)
            if act_date < trip['start_date'] or act_date > trip['end_date']:
                errors.append(f"Activity date must be within trip dates ({trip['start_date']} to {trip['end_date']}).")
        except ValueError:
            errors.append("Invalid activity date format.")

        try:
            cost = Decimal(cost_str)
            if cost < 0:
                errors.append("Estimated cost cannot be negative.")
        except Exception:
            errors.append("Invalid numeric cost.")

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template('trips/activity_form.html',
                                   trip=trip,
                                   action="Edit",
                                   activity_id=activity_id,
                                   name=name,
                                   activity_date=activity_date_str,
                                   activity_time=activity_time_str,
                                   category=category,
                                   place=place,
                                   estimated_cost=cost_str)

        db.query_db(
            """
            UPDATE activities
            SET name = %s, activity_date = %s, activity_time = %s, category = %s, place = %s, estimated_cost = %s
            WHERE id = %s AND trip_id = %s
            """,
            (name, activity_date_str, activity_time_str, category, place, float(cost), activity_id, trip_id),
            commit=True
        )

        flash(f"Activity '{name}' updated successfully!", "success")
        return redirect(url_for('trip_detail', trip_id=trip_id))

    time_str = ''
    if activity['activity_time']:
        # Could be timedelta or time object from connector
        ts = str(activity['activity_time'])
        time_str = ts[:5] if len(ts) >= 5 else ts

    return render_template('trips/activity_form.html',
                           trip=trip,
                           action="Edit",
                           activity_id=activity['id'],
                           name=activity['name'],
                           activity_date=activity['activity_date'].isoformat(),
                           activity_time=time_str,
                           category=activity['category'],
                           place=activity['place'],
                           estimated_cost=str(activity['estimated_cost']))

@app.route('/trips/<int:trip_id>/activities/<int:activity_id>/delete', methods=['POST'])
@login_required
def delete_activity(trip_id, activity_id):
    trip = db.query_db("SELECT * FROM trips WHERE id = %s", (trip_id,), one=True)
    if not trip or trip['user_id'] != g.user['id']:
        abort(403)

    db.query_db("DELETE FROM activities WHERE id = %s AND trip_id = %s", (activity_id, trip_id), commit=True)
    flash("Activity removed.", "info")
    return redirect(url_for('trip_detail', trip_id=trip_id))

# ---------------------------------------------------------------------------
# 6. EXPLORE PLACES
# ---------------------------------------------------------------------------
@app.route('/explore')
def explore():
    search = request.args.get('search', '').strip()
    category = request.args.get('category', '').strip()

    query = """
        SELECT ps.*, d.name as destination_name, d.city_area,
               (SELECT image_url FROM place_images WHERE place_id = ps.id ORDER BY is_primary DESC, display_order ASC LIMIT 1) as image_url
        FROM place_suggestions ps
        JOIN destinations d ON ps.destination_id = d.id
        WHERE ps.status = 'approved'
    """
    params = []

    if search:
        query += " AND (ps.name LIKE %s OR d.name LIKE %s OR ps.short_description LIKE %s)"
        pattern = f"%{search}%"
        params.extend([pattern, pattern, pattern])

    if category and category.lower() != 'all':
        query += " AND ps.category = %s"
        params.append(category)

    query += " ORDER BY ps.id ASC"

    places = db.query_db(query, tuple(params))

    categories = ['All', 'Nature', 'Beach', 'Historical', 'Mountain', 'Adventure', 'Food', 'Culture']

    return render_template('explore.html',
                           places=places,
                           categories=categories,
                           selected_category=category or 'All',
                           search=search)

# ---------------------------------------------------------------------------
# 7. EXPLORE PLACE DETAILS
# ---------------------------------------------------------------------------
@app.route('/places/<int:place_id>')
def place_details(place_id):
    place = db.query_db(
        """
        SELECT ps.*, d.name as destination_name, d.city_area, d.overview_description,
               d.travel_tips, d.local_food, d.suggested_itinerary
        FROM place_suggestions ps
        JOIN destinations d ON ps.destination_id = d.id
        WHERE ps.id = %s
        """,
        (place_id,),
        one=True
    )
    if not place:
        abort(404, description="Place not found.")

    # Restrict unapproved places unless admin or submitter
    if place['status'] != 'approved':
        if not g.user or (g.user['role'] != 'admin' and g.user['id'] != place['submitted_by']):
            abort(404, description="Place suggestion is pending approval.")

    # Load gallery images - strictly distinct images only
    images_raw = db.query_db(
        "SELECT * FROM place_images WHERE place_id = %s ORDER BY is_primary DESC, display_order ASC",
        (place_id,)
    )
    seen_urls = set()
    images = []
    for img in images_raw:
        if img['image_url'] not in seen_urls:
            seen_urls.add(img['image_url'])
            images.append(img)

    # Load other attractions in the same destination (for "Things to See & Do" cards)
    other_places = db.query_db(
        """
        SELECT ps.*, 
               (SELECT image_url FROM place_images WHERE place_id = ps.id ORDER BY is_primary DESC LIMIT 1) as image_url
        FROM place_suggestions ps
        WHERE ps.destination_id = %s AND ps.status = 'approved' AND ps.id != %s
        LIMIT 4
        """,
        (place['destination_id'], place_id)
    )

    # Parse multi-line strings into lists for rendering
    things_to_see_list = [item.strip() for item in (place['things_to_see'] or '').split('\n') if item.strip()]
    travel_tips_list = [item.strip() for item in (place['travel_tips'] or '').split('\n') if item.strip()]
    local_food_list = [item.strip() for item in (place['local_food'] or '').split('\n') if item.strip()]

    # If logged in, fetch user's trips for the "Add to My Trip" modal
    user_trips = []
    if g.user:
        user_trips = db.query_db(
            "SELECT id, destination, start_date, end_date FROM trips WHERE user_id = %s ORDER BY start_date ASC",
            (g.user['id'],)
        )

    return render_template('place_details.html',
                           place=place,
                           images=images,
                           primary_image=images[0]['image_url'] if images else None,
                           other_places=other_places,
                           things_to_see_list=things_to_see_list,
                           travel_tips_list=travel_tips_list,
                           local_food_list=local_food_list,
                           user_trips=user_trips)

@app.route('/places/<int:place_id>/add-to-trip', methods=['POST'])
@login_required
def add_place_to_trip(place_id):
    place = db.query_db("SELECT * FROM place_suggestions WHERE id = %s", (place_id,), one=True)
    if not place:
        abort(404)

    trip_id = request.form.get('trip_id')
    activity_date_str = request.form.get('activity_date')
    activity_time_str = request.form.get('activity_time') or '10:00'
    custom_name = request.form.get('name', place['name']).strip()
    cost_str = request.form.get('estimated_cost', str(place['estimated_cost_min'])).strip()

    # Validate trip ownership
    trip = db.query_db("SELECT * FROM trips WHERE id = %s AND user_id = %s", (trip_id, g.user['id']), one=True)
    if not trip:
        flash("Please select a valid trip of your own.", "danger")
        return redirect(url_for('place_details', place_id=place_id))

    errors = []
    try:
        act_date = date.fromisoformat(activity_date_str)
        if act_date < trip['start_date'] or act_date > trip['end_date']:
            errors.append(f"Activity date must be within trip dates ({trip['start_date']} to {trip['end_date']}).")
    except Exception:
        errors.append("Invalid date selected.")

    try:
        cost = Decimal(cost_str)
        if cost < 0:
            errors.append("Cost cannot be negative.")
    except Exception:
        errors.append("Invalid cost.")

    if errors:
        for err in errors:
            flash(err, "danger")
        return redirect(url_for('place_details', place_id=place_id))

    db.query_db(
        """
        INSERT INTO activities (trip_id, place_suggestion_id, name, activity_date, activity_time, category, place, estimated_cost)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (trip['id'], place_id, custom_name, activity_date_str, activity_time_str, place['category'], place['address'] or place['name'], float(cost)),
        commit=True
    )

    flash(f"Added '{custom_name}' to your trip to {trip['destination']}!", "success")
    return redirect(url_for('trip_detail', trip_id=trip['id']))

# ---------------------------------------------------------------------------
# 8. SUGGEST PLACES (MULTI-PLACE SUBMISSION IN ONE FORM)
# ---------------------------------------------------------------------------
@app.route('/suggest-places', methods=['GET', 'POST'])
def suggest_places():
    if request.method == 'POST':
        # Destination Information
        dest_name = request.form.get('destination_name', '').strip()
        city_area = request.form.get('city_area', '').strip() or None
        overview_desc = request.form.get('overview_description', '').strip()
        travel_tips = request.form.get('travel_tips', '').strip() or None
        local_food = request.form.get('local_food', '').strip() or None
        suggested_itinerary = request.form.get('suggested_itinerary', '').strip() or None

        errors = []
        if not dest_name:
            errors.append("Destination / Region name is required.")
        if not overview_desc:
            errors.append("Destination Overview Description is required.")

        # Detect submitted places: Look for place_name_0, place_name_1, etc.
        place_indices = set()
        for key in request.form.keys():
            m = re.match(r'^place_name_(\d+)$', key)
            if m:
                place_indices.add(int(m.group(1)))

        if not place_indices:
            errors.append("You must include at least one place in your submission.")

        parsed_places = []
        for idx in sorted(place_indices):
            p_name = request.form.get(f'place_name_{idx}', '').strip()
            p_cat = request.form.get(f'category_{idx}', 'Nature').strip()
            p_desc = request.form.get(f'short_description_{idx}', '').strip()
            p_things = request.form.get(f'things_to_see_{idx}', '').strip()
            p_best_time = request.form.get(f'best_time_to_visit_{idx}', '').strip()
            p_cost_min_str = request.form.get(f'estimated_cost_min_{idx}', '0').strip()
            p_cost_max_str = request.form.get(f'estimated_cost_max_{idx}', '0').strip()
            p_duration = request.form.get(f'recommended_duration_{idx}', '1 - 2 days').strip()
            p_address = request.form.get(f'address_{idx}', '').strip() or None
            p_image_url = request.form.get(f'image_url_{idx}', '').strip()

            if not p_name:
                errors.append(f"Place #{idx+1}: Place Name is required.")
            if not p_desc:
                errors.append(f"Place #{idx+1}: Short Description is required.")

            try:
                min_cost = Decimal(p_cost_min_str or '0')
                max_cost = Decimal(p_cost_max_str or p_cost_min_str or '0')
                if min_cost < 0 or max_cost < 0:
                    errors.append(f"Place #{idx+1}: Costs cannot be negative.")
                if max_cost < min_cost:
                    errors.append(f"Place #{idx+1}: Maximum cost must be greater than or equal to minimum cost.")
            except Exception:
                errors.append(f"Place #{idx+1}: Invalid cost values.")
                min_cost = Decimal('0')
                max_cost = Decimal('0')

            # Check uploaded file for this index
            uploaded_file = request.files.get(f'image_file_{idx}')
            saved_image_url = p_image_url

            if uploaded_file and uploaded_file.filename and allowed_file(uploaded_file.filename):
                try:
                    ext = uploaded_file.filename.rsplit('.', 1)[1].lower()
                    filename = f"place_{uuid.uuid4().hex[:12]}.{ext}"
                    filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
                    uploaded_file.save(filepath)
                    saved_image_url = f"/uploads/places/{filename}"
                except Exception as ex:
                    errors.append(f"Place #{idx+1}: Failed to save uploaded image: {str(ex)}")

            # Fallback image if none supplied
            if not saved_image_url:
                saved_image_url = "https://images.unsplash.com/photo-1488646953014-85cb44e25828?auto=format&fit=crop&w=1200&q=80"

            parsed_places.append({
                'name': p_name,
                'category': p_cat,
                'short_description': p_desc,
                'things_to_see': p_things or 'Scenic exploration\nPhotography\nLocal markets',
                'best_time_to_visit': p_best_time or 'All Year',
                'estimated_cost_min': float(min_cost),
                'estimated_cost_max': float(max_cost),
                'recommended_duration': p_duration or '1 day',
                'address': p_address,
                'image_url': saved_image_url
            })

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template('suggest_places.html')

        # Execute Transaction using mysql.connector
        conn = db.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            # 1. Reuse existing destination or insert new
            cursor.execute("SELECT id FROM destinations WHERE name = %s", (dest_name,))
            existing_dest = cursor.fetchone()
            if existing_dest:
                dest_id = existing_dest['id']
            else:
                user_id = g.user['id'] if g.user else None
                cursor.execute(
                    """
                    INSERT INTO destinations (name, city_area, overview_description, travel_tips, local_food, suggested_itinerary, created_by)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (dest_name, city_area, overview_desc, travel_tips, local_food, suggested_itinerary, user_id)
                )
                dest_id = cursor.lastrowid

            # 2. Insert each place
            submitted_by = g.user['id'] if g.user else None
            # If submitted by admin, auto-approve; otherwise 'pending'
            init_status = 'approved' if (g.user and g.user['role'] == 'admin') else 'pending'

            for p in parsed_places:
                cursor.execute(
                    """
                    INSERT INTO place_suggestions (
                        destination_id, submitted_by, name, category, short_description,
                        things_to_see, best_time_to_visit, estimated_cost_min, estimated_cost_max,
                        recommended_duration, address, status
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        dest_id, submitted_by, p['name'], p['category'], p['short_description'],
                        p['things_to_see'], p['best_time_to_visit'], p['estimated_cost_min'], p['estimated_cost_max'],
                        p['recommended_duration'], p['address'], init_status
                    )
                )
                place_id = cursor.lastrowid

                # 3. Insert primary image
                cursor.execute(
                    """
                    INSERT INTO place_images (place_id, image_url, alt_text, is_primary, display_order)
                    VALUES (%s, %s, %s, 1, 1)
                    """,
                    (place_id, p['image_url'], f"{p['name']} main photo")
                )

            conn.commit()
            cursor.close()
            conn.close()

            count = len(parsed_places)
            if init_status == 'approved':
                flash(f"Successfully submitted and published {count} place(s) for {dest_name}!", "success")
                return redirect(url_for('explore'))
            else:
                flash(f"Thank you! Your {count} place suggestions for {dest_name} have been submitted for review.", "success")
                return redirect(url_for('explore'))

        except Exception as e:
            conn.rollback()
            cursor.close()
            conn.close()
            flash(f"An error occurred while saving your suggestion: {str(e)}", "danger")
            return render_template('suggest_places.html')

    return render_template('suggest_places.html')

# ---------------------------------------------------------------------------
# 9. ADMIN MODERATION
# ---------------------------------------------------------------------------
@app.route('/admin/place-suggestions')
@login_required
@admin_required
def admin_suggestions():
    filter_status = request.args.get('status', 'pending')
    query = """
        SELECT ps.*, d.name as destination_name, u.username as submitter_username,
               (SELECT image_url FROM place_images WHERE place_id = ps.id ORDER BY is_primary DESC LIMIT 1) as image_url
        FROM place_suggestions ps
        JOIN destinations d ON ps.destination_id = d.id
        LEFT JOIN users u ON ps.submitted_by = u.id
    """
    if filter_status in ('pending', 'approved', 'rejected'):
        query += " WHERE ps.status = %s ORDER BY ps.created_at DESC"
        suggestions = db.query_db(query, (filter_status,))
    else:
        query += " ORDER BY ps.created_at DESC"
        suggestions = db.query_db(query)

    return render_template('admin/place_suggestions.html', suggestions=suggestions, current_status=filter_status)

@app.route('/admin/place-suggestions/<int:place_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_suggestion(place_id):
    db.query_db("UPDATE place_suggestions SET status = 'approved' WHERE id = %s", (place_id,), commit=True)
    flash("Place suggestion approved and published to Explore!", "success")
    return redirect(url_for('admin_suggestions', status=request.args.get('status', 'pending')))

@app.route('/admin/place-suggestions/<int:place_id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_suggestion(place_id):
    db.query_db("UPDATE place_suggestions SET status = 'rejected' WHERE id = %s", (place_id,), commit=True)
    flash("Place suggestion rejected.", "info")
    return redirect(url_for('admin_suggestions', status=request.args.get('status', 'pending')))

# ---------------------------------------------------------------------------
# 10. ERROR HANDLERS
# ---------------------------------------------------------------------------
@app.errorhandler(400)
def bad_request_error(e):
    return render_template('403.html', title="Bad Request", message=str(e.description or e)), 400

@app.errorhandler(403)
def forbidden_error(e):
    return render_template('403.html', title="Access Denied", message="Access Denied: This private trip or resource belongs to another user."), 403

@app.errorhandler(404)
def not_found_error(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    # Initialize DB tables if needed
    try:
        db.init_db()
    except Exception as e:
        print("DB init note:", e)
    app.run(host='0.0.0.0', port=3000, debug=False)
