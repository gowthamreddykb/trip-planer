"""
Configuration settings for the Trip Planner application.
Only standard library and specified packages used.
"""
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Helper to load simple KEY=VALUE pairs from .env if present
env_file = os.path.join(BASE_DIR, '.env')
if os.path.exists(env_file):
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, val = line.split('=', 1)
                os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'trip-planner-secure-secret-key-2026')
    
    # Database Configuration
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = int(os.environ.get('DB_PORT', 3306))
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'gowtham@69')
    DB_NAME = os.environ.get('DB_NAME', 'trip_planner')
    
    # Upload settings
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads', 'places')
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 Megabytes
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}
    
    # Session security for localhost and iframe support
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = False
    PERMANENT_SESSION_LIFETIME = 86400 * 7
