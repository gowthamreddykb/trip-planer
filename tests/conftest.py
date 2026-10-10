"""
Pytest configuration and fixtures for Trip Planner.
"""
import pytest
from app import app as flask_app
import db

@pytest.fixture(scope='session')
def app():
    flask_app.config['TESTING'] = True
    flask_app.config['WTF_CSRF_ENABLED'] = False
    return flask_app

@pytest.fixture
def client(app):
    test_client = app.test_client()
    with test_client.session_transaction() as sess:
        sess['_csrf_token'] = 'test-csrf-token'
    return test_client

def login_client(client, login_input="john", password="password123"):
    with client.session_transaction() as sess:
        sess['_csrf_token'] = 'test-csrf-token'
    return client.post('/login', data={
        'csrf_token': 'test-csrf-token',
        'login_input': login_input,
        'password': password
    }, follow_redirects=True)
