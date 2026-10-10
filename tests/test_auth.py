"""
Authentication Tests for Trip Planner.
"""
import uuid
from werkzeug.security import check_password_hash
from tests.conftest import login_client
import db

def test_successful_registration(client):
    unique_user = f"user_{uuid.uuid4().hex[:6]}"
    unique_email = f"{unique_user}@example.com"

    response = client.post('/register', data={
        'csrf_token': 'test-csrf-token',
        'username': unique_user,
        'email': unique_email,
        'password': 'securepassword123',
        'confirm_password': 'securepassword123'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Welcome to Trip Planner" in response.data or b"My Trips" in response.data

    # Verify user in database and password hashed
    user = db.query_db("SELECT * FROM users WHERE username = %s", (unique_user,), one=True)
    assert user is not None
    assert user['email'] == unique_email
    assert user['role'] == 'user'
    assert check_password_hash(user['password_hash'], 'securepassword123')

def test_duplicate_registration_rejected(client):
    # Try registering existing user 'john'
    response = client.post('/register', data={
        'csrf_token': 'test-csrf-token',
        'username': 'john',
        'email': 'different_email@example.com',
        'password': 'password123',
        'confirm_password': 'password123'
    }, follow_redirects=True)

    assert b"already exists" in response.data

def test_duplicate_email_rejected(client):
    response = client.post('/register', data={
        'csrf_token': 'test-csrf-token',
        'username': f"user_{uuid.uuid4().hex[:6]}",
        'email': 'john@example.com',
        'password': 'password123',
        'confirm_password': 'password123'
    }, follow_redirects=True)

    assert b"already exists" in response.data

def test_successful_login(client):
    response = login_client(client, "john", "password123")
    assert response.status_code == 200
    assert b"Welcome back" in response.data or b"My Trips" in response.data

def test_invalid_login(client):
    response = login_client(client, "john", "wrongpassword")
    assert response.status_code == 200
    assert b"Invalid username/email or password" in response.data

def test_logout(client):
    login_client(client, "john", "password123")
    response = client.post('/logout', data={'csrf_token': 'test-csrf-token'}, follow_redirects=True)
    assert response.status_code == 200
    assert b"logged out successfully" in response.data

def test_private_routes_require_login(client):
    # Make sure session is clean
    with client.session_transaction() as sess:
        sess.clear()
        sess['_csrf_token'] = 'test-csrf-token'

    response = client.get('/my-trips', follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.headers['Location']
