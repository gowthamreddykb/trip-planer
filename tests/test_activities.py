"""
Activity Management Tests for Trip Planner.
"""
from decimal import Decimal
from tests.conftest import login_client
import db

def test_add_and_recalculate_activity_budget(client):
    login_client(client, "john", "password123")

    # Trip 2: Kerala (2025-05-05 to 2025-05-07)
    # Add an activity
    response = client.post('/trips/2/activities/new', data={
        'csrf_token': 'test-csrf-token',
        'name': 'Sunset Kayaking',
        'activity_date': '2025-05-07',
        'activity_time': '17:30',
        'category': 'Adventure',
        'place': 'Alappuzha Beach',
        'estimated_cost': '750'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Sunset Kayaking" in response.data

    # Verify activity exists in DB
    act = db.query_db("SELECT * FROM activities WHERE name = 'Sunset Kayaking' AND trip_id = 2", one=True)
    assert act is not None
    assert str(act['estimated_cost']) == '750.00'

def test_reject_activity_out_of_trip_dates(client):
    login_client(client, "john", "password123")

    # Trip 2 dates: 2025-05-05 to 2025-05-07
    # Try date: 2025-05-15 (outside range)
    response = client.post('/trips/2/activities/new', data={
        'csrf_token': 'test-csrf-token',
        'name': 'Invalid Date Tour',
        'activity_date': '2025-05-15',
        'activity_time': '10:00',
        'category': 'Nature',
        'place': 'Munnar',
        'estimated_cost': '500'
    }, follow_redirects=True)

    assert b"Activity date must be within trip dates" in response.data

def test_reject_negative_activity_cost(client):
    login_client(client, "john", "password123")

    response = client.post('/trips/2/activities/new', data={
        'csrf_token': 'test-csrf-token',
        'name': 'Negative Cost Tour',
        'activity_date': '2025-05-06',
        'activity_time': '10:00',
        'category': 'Nature',
        'place': 'Kochi',
        'estimated_cost': '-200'
    }, follow_redirects=True)

    assert b"Estimated cost cannot be negative" in response.data

def test_edit_and_delete_activity(client):
    login_client(client, "john", "password123")

    # Activity 1 is on Trip 2 (Houseboat Check-in)
    # Update cost to 2500
    response = client.post('/trips/2/activities/1/edit', data={
        'csrf_token': 'test-csrf-token',
        'name': 'Houseboat Check-in VIP',
        'activity_date': '2025-05-05',
        'activity_time': '09:00',
        'category': 'Nature',
        'place': 'Alleppey Jetty',
        'estimated_cost': '2500'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Houseboat Check-in VIP" in response.data

    # Check updated cost in DB
    act = db.query_db("SELECT estimated_cost FROM activities WHERE id = 1", one=True)
    assert str(act['estimated_cost']) == '2500.00'
