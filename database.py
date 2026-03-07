"""
Database module for venue scraper
Creates and manages SQLite database for venues, artists, and shows
"""

import sqlite3
from datetime import datetime
from typing import Optional, Dict, List
import os
import time

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

    def get_upcoming_shows(self, limit: int = 100, artist_filter: str = None, country_filter: str = None) -> List[Dict]:
        """Get upcoming shows with artist and venue info"""
        cursor = self.conn.cursor()
        query = '''
            SELECT s.show_date, s.show_url, a.name AS artist_name,
                   v.name AS venue_name, v.city, v.state, v.country, v.venue_url
            FROM shows s
            JOIN artists a ON s.artist_id = a.id
            JOIN venues v ON s.venue_id = v.id
            WHERE s.show_date >= date('now')
        '''
        params = []
        if artist_filter:
            query += ' AND a.name = ?'
            params.append(artist_filter)
        if country_filter:
            query += ' AND v.country = ?'
            params.append(country_filter)
        query += ' ORDER BY s.show_date ASC LIMIT ?'
        params.append(limit)
        rows = cursor.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def get_all_shows(self) -> List[Dict]:
        """Get all shows with artist and venue info"""
        cursor = self.conn.cursor()
        rows = cursor.execute('''
            SELECT s.show_date, s.show_url, a.name AS artist_name,
                   v.name AS venue_name, v.city, v.state, v.country, v.venue_url
            FROM shows s
            JOIN artists a ON s.artist_id = a.id
            JOIN venues v ON s.venue_id = v.id
            ORDER BY s.show_date DESC
        ''').fetchall()
        return [dict(row) for row in rows]

    def get_shows_for_venue(self, venue_id: int) -> List[Dict]:
        """Get all shows at a specific venue"""
        cursor = self.conn.cursor()
        rows = cursor.execute('''
            SELECT s.show_date, s.show_url, a.name AS artist_name, s.source
            FROM shows s
            JOIN artists a ON s.artist_id = a.id
            WHERE s.venue_id = ?
            ORDER BY s.show_date ASC
        ''', (venue_id,)).fetchall()
        return [dict(row) for row in rows]

    def get_venues_for_artist(self, artist_name: str) -> List[Dict]:
        """Get all venues where an artist has shows"""
        cursor = self.conn.cursor()
        rows = cursor.execute('''
            SELECT DISTINCT v.id, v.name, v.city, v.state, v.country, v.venue_url,
                   s.show_date, s.show_url
            FROM venues v
            JOIN shows s ON v.id = s.venue_id
            JOIN artists a ON s.artist_id = a.id
            WHERE a.name = ?
            ORDER BY s.show_date ASC
        ''', (artist_name,)).fetchall()
        return [dict(row) for row in rows]

    def get_distinct_countries(self) -> List[str]:
        """Get distinct countries from venues"""
        cursor = self.conn.cursor()
        rows = cursor.execute('SELECT DISTINCT country FROM venues WHERE country IS NOT NULL ORDER BY country').fetchall()
        return [row[0] for row in rows]

    def get_distinct_sources(self) -> List[str]:
        """Get distinct sources from venues"""
        cursor = self.conn.cursor()
        rows = cursor.execute('SELECT DISTINCT source FROM venues WHERE source IS NOT NULL ORDER BY source').fetchall()
        return [row[0] for row in rows]

    def get_venues_with_coordinates(self) -> List[Dict]:
        """Get venues that have lat/lon coordinates"""
        cursor = self.conn.cursor()
        rows = cursor.execute('''
            SELECT * FROM venues
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
            ORDER BY name
        ''').fetchall()
        return [dict(row) for row in rows]

    def get_distinct_artists(self) -> List[str]:
        """Get distinct artist names from the database"""
        cursor = self.conn.cursor()
        rows = cursor.execute('SELECT DISTINCT name FROM artists ORDER BY name').fetchall()
        return [row[0] for row in rows]

    def geocode_venues(self, progress_callback=None):
        """Geocode venues that have no coordinates using geopy"""
        try:
            from geopy.geocoders import Nominatim
            from geopy.exc import GeocoderTimedOut
        except ImportError:
            return {"error": "geopy not installed. Run: pip install geopy"}

        geolocator = Nominatim(user_agent="venue_scraper")
        cursor = self.conn.cursor()
        rows = cursor.execute('''
            SELECT id, name, city, state, country FROM venues
            WHERE latitude IS NULL OR longitude IS NULL
        ''').fetchall()

        updated = 0
        total = len(rows)
        for i, row in enumerate(rows):
            venue = dict(row)
            query_parts = [p for p in [venue.get('city'), venue.get('state'), venue.get('country')] if p]
            query = ", ".join(query_parts)
            if not query:
                continue
            try:
                location = geolocator.geocode(query, timeout=5)
                if location:
                    cursor.execute('''
                        UPDATE venues SET latitude = ?, longitude = ? WHERE id = ?
                    ''', (location.latitude, location.longitude, venue['id']))
                    updated += 1
            except (GeocoderTimedOut, Exception):
                pass
            if progress_callback:
                progress_callback(i + 1, total)
            time.sleep(1)  # Rate limit

        self.conn.commit()
        return {"updated": updated, "total": total}

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
