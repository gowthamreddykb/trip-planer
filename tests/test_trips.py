"""
Trip Management Tests for Trip Planner.
"""
from tests.conftest import login_client
import db

def test_create_and_view_trip(client):
    login_client(client, "john", "password123")

    response = client.post('/trips/new', data={
        'csrf_token': 'test-csrf-token',
        'destination': 'Shimla Hills',
        'start_date': '2025-07-01',
        'end_date': '2025-07-05',
        'budget': '8000'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Shimla Hills" in response.data

    # Verify in DB
    trip = db.query_db("SELECT * FROM trips WHERE destination = 'Shimla Hills'", one=True)
    assert trip is not None
    assert str(trip['budget']) == '8000.00'

def test_reject_invalid_trip_dates(client):
    login_client(client, "john", "password123")

    # End date before start date
    response = client.post('/trips/new', data={
        'csrf_token': 'test-csrf-token',
        'destination': 'Invalid Date Trip',
        'start_date': '2025-08-10',
        'end_date': '2025-08-05',
        'budget': '5000'
    }, follow_redirects=True)

    assert b"End date cannot be earlier than start date" in response.data

def test_reject_negative_budget(client):
    login_client(client, "john", "password123")

    response = client.post('/trips/new', data={
        'csrf_token': 'test-csrf-token',
        'destination': 'Negative Budget Trip',
        'start_date': '2025-09-01',
        'end_date': '2025-09-05',
        'budget': '-1000'
    }, follow_redirects=True)

    assert b"Budget cannot be negative" in response.data

def test_prevent_cross_user_trip_access(client):
    # John tries to access an unowned trip or another user tries to access John's trip
    # Create another user 'alice'
    db.query_db(
        "INSERT INTO users (username, email, password_hash, role) VALUES ('alice', 'alice@example.com', 'dummy_hash', 'user') ON DUPLICATE KEY UPDATE id=id",
        commit=True
    )
    alice = db.query_db("SELECT id FROM users WHERE username = 'alice'", one=True)

    # Trip 2 belongs to John (user_id=2)
    # Login as Alice
    with client.session_transaction() as sess:
        sess.clear()
        sess['user_id'] = alice['id']
        sess['username'] = 'alice'
        sess['_csrf_token'] = 'test-csrf-token'

    # Alice tries to view John's trip (trip_id=2)
    response = client.get('/trips/2')
    assert response.status_code == 403
    assert b"Access Denied" in response.data

def test_reject_date_edit_violating_activities(client):
    login_client(client, "john", "password123")

    # Trip 2 (Kerala) has activities on 2025-05-05 and 2025-05-06
    # Try moving start date to 2025-05-06 or end date to 2025-05-05
    response = client.post('/trips/2/edit', data={
        'csrf_token': 'test-csrf-token',
        'destination': 'Kerala',
        'start_date': '2025-05-06',  # Conflicts with activity on 2025-05-05
        'end_date': '2025-05-07',
        'budget': '6000'
    }, follow_redirects=True)

    assert b"Cannot set start date after" in response.data
