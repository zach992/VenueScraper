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
                status TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(name, city, country)
            )
        ''')

        # Add status and notes columns if they don't exist (migration for existing DBs)
        try:
            cursor.execute('ALTER TABLE venues ADD COLUMN status TEXT DEFAULT "New"')
        except sqlite3.OperationalError:
            pass  # Column already exists
        try:
            cursor.execute('ALTER TABLE venues ADD COLUMN notes TEXT DEFAULT ""')
        except sqlite3.OperationalError:
            pass  # Column already exists

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
                is_festival INTEGER DEFAULT 0,
                festival_name TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (artist_id) REFERENCES artists (id),
                FOREIGN KEY (venue_id) REFERENCES venues (id),
                UNIQUE(artist_id, venue_id, show_date, source)
            )
        ''')

        # Add festival columns if they don't exist (migration for existing DBs)
        try:
            cursor.execute('ALTER TABLE shows ADD COLUMN is_festival INTEGER DEFAULT 0')
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute('ALTER TABLE shows ADD COLUMN festival_name TEXT DEFAULT ""')
        except sqlite3.OperationalError:
            pass

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
            INSERT INTO shows (artist_id, venue_id, show_date, show_url, source, external_id, is_festival, festival_name)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            artist_id,
            venue_id,
            show_data.get('show_date'),
            show_data.get('show_url'),
            show_data.get('source'),
            show_data.get('external_id'),
            1 if show_data.get('is_festival') else 0,
            show_data.get('festival_name', '')
        ))

        self.conn.commit()
        return cursor.lastrowid

    def get_venue_by_exact_match(self, name: str, city: str, country: str) -> Optional[Dict]:
        """Find venue by exact name/city/country match (case-insensitive)"""
        cursor = self.conn.cursor()
        result = cursor.execute('''
            SELECT * FROM venues
            WHERE LOWER(name) = LOWER(?) AND LOWER(COALESCE(city,'')) = LOWER(COALESCE(?,''))
              AND LOWER(COALESCE(country,'')) = LOWER(COALESCE(?,''))
        ''', (name or '', city or '', country or '')).fetchone()
        return dict(result) if result else None

    def get_venues_by_city_country(self, city: str, country: str) -> List[Dict]:
        """Get venues in a specific city/country for fuzzy matching"""
        cursor = self.conn.cursor()
        venues = cursor.execute('''
            SELECT * FROM venues
            WHERE LOWER(COALESCE(city,'')) = LOWER(?) AND LOWER(COALESCE(country,'')) = LOWER(?)
        ''', (city or '', country or '')).fetchall()
        return [dict(v) for v in venues]

    def get_venues_with_no_city(self) -> List[Dict]:
        """Get venues with missing city info (for name-only matching)"""
        cursor = self.conn.cursor()
        venues = cursor.execute('''
            SELECT * FROM venues
            WHERE city IS NULL OR TRIM(city) = '' OR city = 'None'
        ''').fetchall()
        return [dict(v) for v in venues]

    def get_all_venues(self) -> List[Dict]:
        """Get all venues from the database"""
        cursor = self.conn.cursor()
        venues = cursor.execute('SELECT * FROM venues ORDER BY created_at DESC').fetchall()
        return [dict(venue) for venue in venues]

    def get_all_venues_with_artists(self) -> List[Dict]:
        """Get all venues with the artists that play there and festival info"""
        cursor = self.conn.cursor()
        venues = cursor.execute('''
            SELECT v.*,
                   GROUP_CONCAT(DISTINCT a.name) as artists,
                   MAX(s.is_festival) as has_festival,
                   MIN(CASE WHEN s.is_festival = 0 THEN 1 ELSE NULL END) as has_regular,
                   GROUP_CONCAT(DISTINCT CASE WHEN s.festival_name != '' THEN s.festival_name END) as festival_names
            FROM venues v
            LEFT JOIN shows s ON v.id = s.venue_id
            LEFT JOIN artists a ON s.artist_id = a.id
            GROUP BY v.id
            ORDER BY v.created_at DESC
        ''').fetchall()
        results = []
        for venue in venues:
            d = dict(venue)
            # Compute venue_type from festival data
            has_fest = d.get('has_festival', 0) or 0
            has_reg = d.get('has_regular') is not None
            fest_names = d.get('festival_names', '') or ''
            if has_fest and has_reg:
                d['venue_type'] = 'Both'
            elif has_fest:
                if fest_names:
                    d['venue_type'] = f"Festival: {fest_names}"
                else:
                    d['venue_type'] = 'Festival'
            else:
                d['venue_type'] = 'Show'
            results.append(d)
        return results

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

    def update_venue_status(self, venue_id: int, status: str):
        """Update venue status"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE venues SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (status, venue_id))
        self.conn.commit()

    def update_venue_notes(self, venue_id: int, notes: str):
        """Update venue notes"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE venues SET notes = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (notes, venue_id))
        self.conn.commit()

    def update_venue(self, venue_id: int, city: str = None, state: str = None, country: str = None):
        """Update venue fields (used to fill in missing data)"""
        cursor = self.conn.cursor()
        if city:
            cursor.execute('UPDATE venues SET city = ? WHERE id = ? AND (city IS NULL OR city = "")', (city, venue_id))
        if state:
            cursor.execute('UPDATE venues SET state = ? WHERE id = ? AND (state IS NULL OR state = "")', (state, venue_id))
        if country:
            cursor.execute('UPDATE venues SET country = ? WHERE id = ? AND (country IS NULL OR country = "")', (country, venue_id))
        self.conn.commit()

    def delete_venue(self, venue_id: int):
        """Delete a venue and its associated shows"""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM shows WHERE venue_id = ?', (venue_id,))
        cursor.execute('DELETE FROM venues WHERE id = ?', (venue_id,))
        self.conn.commit()

    def merge_duplicate_venues(self):
        """Merge venues that have the same name but one has None/empty city"""
        cursor = self.conn.cursor()
        # Find venues with empty city that have a duplicate with a real city
        dupes = cursor.execute('''
            SELECT empty.id as empty_id, filled.id as filled_id
            FROM venues empty
            JOIN venues filled ON LOWER(empty.name) = LOWER(filled.name)
            WHERE (empty.city IS NULL OR empty.city = '' OR empty.city = 'None')
              AND filled.city IS NOT NULL AND filled.city != '' AND filled.city != 'None'
              AND empty.id != filled.id
        ''').fetchall()

        for dupe in dupes:
            # Move shows from empty-city venue to the one with city info (skip duplicates)
            cursor.execute('''
                UPDATE OR IGNORE shows SET venue_id = ? WHERE venue_id = ?
            ''', (dupe['filled_id'], dupe['empty_id']))
            # Delete any remaining shows that couldn't be moved (were duplicates)
            cursor.execute('DELETE FROM shows WHERE venue_id = ?', (dupe['empty_id'],))
            cursor.execute('DELETE FROM venues WHERE id = ?', (dupe['empty_id'],))

        # Also delete venues with completely empty names
        cursor.execute('DELETE FROM venues WHERE name IS NULL OR TRIM(name) = ""')

        self.conn.commit()
        return len(dupes)

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
