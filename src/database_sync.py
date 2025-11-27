#!/usr/bin/env python3
"""
Database Sync Module
Handles local SQLite database and sync with cloud database (Neon.com)
"""
import sqlite3
import os
import json
import time
from pathlib import Path
from datetime import datetime
import psycopg2
from psycopg2.extras import execute_values

BASE_DIR = Path(__file__).parent.parent
DB_DIR = BASE_DIR / "db"
DB_DIR.mkdir(exist_ok=True)
LOCAL_DB = DB_DIR / "robot_telemetry.db"
SYNC_STATUS_FILE = DB_DIR / "sync_status.json"

def init_local_db():
    """Initialize local SQLite database"""
    conn = sqlite3.connect(LOCAL_DB)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS sensor_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            ultrasonic_cm REAL,
            ir_left INTEGER,
            ir_center INTEGER,
            ir_right INTEGER,
            line_state TEXT,
            synced INTEGER DEFAULT 0,
            sync_timestamp TEXT
        )
    ''')
    # Create index for faster queries
    c.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON sensor_data(timestamp)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_synced ON sensor_data(synced)')
    conn.commit()
    conn.close()

def save_to_local_db(timestamp, ultrasonic=None, ir_left=None, ir_center=None, ir_right=None, line_state=None):
    """Save sensor data to local SQLite database"""
    try:
        conn = sqlite3.connect(LOCAL_DB)
        c = conn.cursor()
        c.execute('''
            INSERT INTO sensor_data (timestamp, ultrasonic_cm, ir_left, ir_center, ir_right, line_state, synced)
            VALUES (?, ?, ?, ?, ?, ?, 0)
        ''', (timestamp, ultrasonic, ir_left, ir_center, ir_right, line_state))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error saving to local DB: {e}")
        return False

def get_unsynced_records():
    """Get all unsynced records from local database"""
    try:
        conn = sqlite3.connect(LOCAL_DB)
        c = conn.cursor()
        c.execute('SELECT id, timestamp, ultrasonic_cm, ir_left, ir_center, ir_right, line_state FROM sensor_data WHERE synced = 0 ORDER BY id')
        records = c.fetchall()
        conn.close()
        return records
    except Exception as e:
        print(f"Error getting unsynced records: {e}")
        return []

def mark_as_synced(record_ids):
    """Mark records as synced"""
    try:
        conn = sqlite3.connect(LOCAL_DB)
        c = conn.cursor()
        sync_time = datetime.now().isoformat()
        placeholders = ','.join('?' * len(record_ids))
        c.execute(f'UPDATE sensor_data SET synced = 1, sync_timestamp = ? WHERE id IN ({placeholders})', 
                 [sync_time] + list(record_ids))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error marking as synced: {e}")
        return False

def sync_to_cloud():
    """Sync unsynced records to cloud database (Neon.com)"""
    cloud_db_url = os.environ.get("DATABASE_URL", "")
    if not cloud_db_url:
        print("No DATABASE_URL set, skipping cloud sync")
        return False
    
    unsynced = get_unsynced_records()
    if not unsynced:
        return True
    
    try:
        # Connect to cloud database
        conn = psycopg2.connect(cloud_db_url)
        c = conn.cursor()
        
        # Ensure table exists
        c.execute('''
            CREATE TABLE IF NOT EXISTS sensor_data (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP NOT NULL,
                ultrasonic_cm REAL,
                ir_left INTEGER,
                ir_center INTEGER,
                ir_right INTEGER,
                line_state TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        
        # Insert unsynced records
        records = [(r[1], r[2], r[3], r[4], r[5], r[6]) for r in unsynced]
        execute_values(
            c,
            '''INSERT INTO sensor_data (timestamp, ultrasonic_cm, ir_left, ir_center, ir_right, line_state)
               VALUES %s ON CONFLICT DO NOTHING''',
            records
        )
        conn.commit()
        conn.close()
        
        # Mark as synced
        record_ids = [r[0] for r in unsynced]
        mark_as_synced(record_ids)
        
        print(f"Synced {len(unsynced)} records to cloud")
        return True
    except Exception as e:
        print(f"Error syncing to cloud: {e}")
        return False

def check_internet():
    """Check if internet connection is available"""
    try:
        import socket
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False

def sync_worker():
    """Background worker to periodically sync data"""
    init_local_db()
    while True:
        if check_internet():
            sync_to_cloud()
        time.sleep(300)  # Sync every 5 minutes

if __name__ == "__main__":
    # Initialize database
    init_local_db()
    
    # Try to sync immediately
    if check_internet():
        sync_to_cloud()
    else:
        print("No internet connection, data will be synced when connection is restored")

