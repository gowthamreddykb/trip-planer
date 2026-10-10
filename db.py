"""
Database connection and operations module using mysql-connector-python.
Provides connection pooling, context management, and parameterized query execution.
"""
import os
import mysql.connector
from mysql.connector import pooling
from config import Config

_pool = None

def get_pool():
    global _pool
    if _pool is None:
        try:
            _pool = pooling.MySQLConnectionPool(
                pool_name="trip_planner_pool",
                pool_size=5,
                pool_reset_session=True,
                host=Config.DB_HOST,
                port=Config.DB_PORT,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                database=Config.DB_NAME,
                autocommit=False
            )
        except Exception:
            # Fallback if database doesn't exist yet
            pass
    return _pool

def get_db_connection():
    """
    Returns a MySQL database connection, attempting to use the pool first
    or falling back to a direct connection.
    """
    pool = get_pool()
    if pool:
        try:
            return pool.get_connection()
        except Exception:
            pass
    return mysql.connector.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        autocommit=False
    )

def query_db(query, args=(), one=False, commit=False):
    """
    Executes a parameterized SQL query safely.
    Returns list of dict rows or single dict if one=True.
    If commit=True, commits and returns lastrowid.
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, args)
        if commit:
            conn.commit()
            last_id = cursor.lastrowid
            cursor.close()
            conn.close()
            return last_id
        rv = cursor.fetchall()
        cursor.close()
        conn.close()
        return (rv[0] if rv else None) if one else rv
    except Exception as e:
        if commit:
            conn.rollback()
        cursor.close()
        conn.close()
        raise e

def init_db(schema_path=None):
    """
    Executes schema.sql statements against MySQL server to initialize tables & seed data.
    """
    if schema_path is None:
        schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
        
    conn = mysql.connector.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        autocommit=True
    )
    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{Config.DB_NAME}`;")
    cursor.execute(f"USE `{Config.DB_NAME}`;")
    
    if os.path.exists(schema_path):
        with open(schema_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()
            # Split commands by semicolon
            for statement in sql_script.split(';'):
                stmt = statement.strip()
                if stmt:
                    try:
                        cursor.execute(stmt)
                    except Exception as ex:
                        # Ignore duplicates or existing objects
                        pass
    cursor.close()
    conn.close()
