"""
Database module for venue scraper
Creates and manages SQLite database for venues, artists, and shows
"""

import sqlite3
from datetime import datetime
from typing import Optional, Dict, List
import os

class VenueDatabase:
    def __init__(self, db_path: str = "venues.db"):
        """Initialize database connection and create tables if needed"""
        self.db_path = db_path
        self.conn = None
        self.connect()
        self.create_tables()

    def connect(self):
        """Connect to SQLite database"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

    def create_tables(self):
        """Create database tables if they don't exist"""
        cursor = self.conn.cursor()

        # Venues table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS venues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                city TEXT,
                state TEXT,
                country TEXT,
                latitude REAL,
                longitude REAL,
                address TEXT,
                venue_url TEXT,
                source TEXT,
                external_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(name, city, country)
            )
        ''')

        # Artists table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS artists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_checked TIMESTAMP
            )
        ''')

        # Shows table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS shows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                artist_id INTEGER,
                venue_id INTEGER,
                show_date TEXT,
                show_url TEXT,
                source TEXT,
                external_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (artist_id) REFERENCES artists (id),
                FOREIGN KEY (venue_id) REFERENCES venues (id),
                UNIQUE(artist_id, venue_id, show_date, source)
            )
        ''')

        self.conn.commit()

    def add_venue(self, venue_data: Dict) -> Optional[int]:
        """
        Add a new venue to the database or return existing venue ID

        Args:
            venue_data: Dictionary with venue information

        Returns:
            Venue ID (new or existing)
        """
        cursor = self.conn.cursor()

        # Check if venue already exists
        existing = cursor.execute('''
            SELECT id FROM venues
            WHERE name = ? AND city = ? AND country = ?
        ''', (venue_data.get('name'), venue_data.get('city'), venue_data.get('country'))).fetchone()

        if existing:
            return existing[0]

        # Insert new venue
        cursor.execute('''
            INSERT INTO venues (name, city, state, country, latitude, longitude, address, venue_url, source, external_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            venue_data.get('name'),
            venue_data.get('city'),
            venue_data.get('state'),
            venue_data.get('country'),
            venue_data.get('latitude'),
            venue_data.get('longitude'),
            venue_data.get('address'),
            venue_data.get('venue_url'),
            venue_data.get('source'),
            venue_data.get('external_id')
        ))

        self.conn.commit()
        return cursor.lastrowid

    def add_artist(self, artist_name: str) -> int:
        """Add or get artist ID"""
        cursor = self.conn.cursor()

        # Check if artist exists
        existing = cursor.execute('SELECT id FROM artists WHERE name = ?', (artist_name,)).fetchone()

        if existing:
            return existing[0]

        # Insert new artist
        cursor.execute('INSERT INTO artists (name) VALUES (?)', (artist_name,))
        self.conn.commit()
        return cursor.lastrowid

    def update_artist_check_time(self, artist_name: str):
        """Update the last_checked timestamp for an artist"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE artists
            SET last_checked = CURRENT_TIMESTAMP
            WHERE name = ?
        ''', (artist_name,))
        self.conn.commit()

    def add_show(self, artist_name: str, venue_id: int, show_data: Dict) -> Optional[int]:
        """Add a show to the database"""
        cursor = self.conn.cursor()

        # Get or create artist
        artist_id = self.add_artist(artist_name)

        # Check if show already exists
        existing = cursor.execute('''
            SELECT id FROM shows
            WHERE artist_id = ? AND venue_id = ? AND show_date = ? AND source = ?
        ''', (artist_id, venue_id, show_data.get('show_date'), show_data.get('source'))).fetchone()

        if existing:
            return existing[0]

        # Insert new show
        cursor.execute('''
            INSERT INTO shows (artist_id, venue_id, show_date, show_url, source, external_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            artist_id,
            venue_id,
            show_data.get('show_date'),
            show_data.get('show_url'),
            show_data.get('source'),
            show_data.get('external_id')
        ))

        self.conn.commit()
        return cursor.lastrowid

    def get_all_venues(self) -> List[Dict]:
        """Get all venues from the database"""
        cursor = self.conn.cursor()
        venues = cursor.execute('SELECT * FROM venues ORDER BY created_at DESC').fetchall()
        return [dict(venue) for venue in venues]

    def get_venues_count(self) -> int:
        """Get total number of venues"""
        cursor = self.conn.cursor()
        result = cursor.execute('SELECT COUNT(*) FROM venues').fetchone()
        return result[0]

    def get_recent_venues(self, limit: int = 10) -> List[Dict]:
        """Get most recently added venues"""
        cursor = self.conn.cursor()
        venues = cursor.execute('''
            SELECT * FROM venues
            ORDER BY created_at DESC
            LIMIT ?
        ''', (limit,)).fetchall()
        return [dict(venue) for venue in venues]

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


if __name__ == "__main__":
    # Test database creation
    db = VenueDatabase()
    print(f"Database created successfully at {db.db_path}")
    print(f"Current venue count: {db.get_venues_count()}")
    db.close()
