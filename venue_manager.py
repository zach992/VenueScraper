"""
Venue manager module
Handles venue comparison, deduplication, and database updates
"""

from typing import Dict, List, Optional, Tuple
from difflib import SequenceMatcher
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VenueManager:
    """Manages venue deduplication and database operations"""

    def __init__(self, database):
        """
        Initialize venue manager

        Args:
            database: VenueDatabase instance
        """
        self.db = database

    def similarity_score(self, str1: str, str2: str) -> float:
        """
        Calculate similarity between two strings

        Args:
            str1: First string
            str2: Second string

        Returns:
            Similarity score between 0 and 1
        """
        if not str1 or not str2:
            return 0.0

        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()

    def is_duplicate_venue(self, new_venue: Dict, existing_venue: Dict, threshold: float = 0.85) -> bool:
        """
        Check if two venues are likely duplicates

        Args:
            new_venue: New venue data
            existing_venue: Existing venue from database
            threshold: Similarity threshold (0-1)

        Returns:
            True if likely duplicates
        """
        # Helper to safely get lowercase string
        def safe_lower(value):
            return (value or '').lower() if value else ''

        # Exact match on name, city, and country
        if (safe_lower(new_venue.get('name')) == safe_lower(existing_venue.get('name')) and
            safe_lower(new_venue.get('city')) == safe_lower(existing_venue.get('city')) and
            safe_lower(new_venue.get('country')) == safe_lower(existing_venue.get('country'))):
            return True

        # Fuzzy match on name if in same city/country
        if (safe_lower(new_venue.get('city')) == safe_lower(existing_venue.get('city')) and
            safe_lower(new_venue.get('country')) == safe_lower(existing_venue.get('country'))):

            name_similarity = self.similarity_score(
                new_venue.get('name', ''),
                existing_venue.get('name', '')
            )

            if name_similarity >= threshold:
                logger.info(f"Fuzzy match found: '{new_venue.get('name')}' ~ '{existing_venue.get('name')}' (score: {name_similarity:.2f})")
                return True

        # Check coordinates if available
        if (new_venue.get('latitude') and new_venue.get('longitude') and
            existing_venue.get('latitude') and existing_venue.get('longitude')):

            lat_diff = abs(new_venue['latitude'] - existing_venue['latitude'])
            lon_diff = abs(new_venue['longitude'] - existing_venue['longitude'])

            # If within ~100 meters (very rough approximation)
            if lat_diff < 0.001 and lon_diff < 0.001:
                logger.info(f"Coordinate match found for {new_venue.get('name')}")
                return True

        return False

    def find_duplicate_in_db(self, venue_data: Dict) -> Optional[int]:
        """
        Search database for potential duplicate venues

        Args:
            venue_data: Venue information to check

        Returns:
            Venue ID if duplicate found, None otherwise
        """
        # Get all venues (could be optimized with city/country filter for large DBs)
        all_venues = self.db.get_all_venues()

        for existing_venue in all_venues:
            if self.is_duplicate_venue(venue_data, existing_venue):
                return existing_venue['id']

        return None

    def add_or_get_venue(self, venue_data: Dict) -> Tuple[int, bool]:
        """
        Add venue to database or get existing venue ID

        Args:
            venue_data: Venue information

        Returns:
            Tuple of (venue_id, is_new)
        """
        # Check for duplicates
        existing_id = self.find_duplicate_in_db(venue_data)

        if existing_id:
            logger.info(f"Venue already exists: {venue_data.get('name')} (ID: {existing_id})")
            return existing_id, False

        # Add new venue
        venue_id = self.db.add_venue(venue_data)
        logger.info(f"New venue added: {venue_data.get('name')} in {venue_data.get('city')}, {venue_data.get('country')} (ID: {venue_id})")

        return venue_id, True

    def process_scraped_data(self, artist_name: str, scraped_data: List[Tuple[Dict, Dict]]) -> Dict[str, int]:
        """
        Process scraped data and update database

        Args:
            artist_name: Name of the artist
            scraped_data: List of (venue_data, show_data) tuples

        Returns:
            Dictionary with statistics
        """
        stats = {
            'new_venues': 0,
            'existing_venues': 0,
            'new_shows': 0,
            'total_events': len(scraped_data)
        }

        for venue_data, show_data in scraped_data:
            # Add or get venue
            venue_id, is_new = self.add_or_get_venue(venue_data)

            if is_new:
                stats['new_venues'] += 1
            else:
                stats['existing_venues'] += 1

            # Add show
            show_id = self.db.add_show(artist_name, venue_id, show_data)

            if show_id:
                stats['new_shows'] += 1

        # Update artist check time
        self.db.update_artist_check_time(artist_name)

        return stats

    def get_summary(self) -> Dict:
        """Get summary statistics from database"""
        return {
            'total_venues': self.db.get_venues_count(),
            'recent_venues': self.db.get_recent_venues(5)
        }


if __name__ == "__main__":
    from database import VenueDatabase

    # Test venue comparison
    db = VenueDatabase()
    manager = VenueManager(db)

    # Test similarity
    test_cases = [
        ("The Fillmore", "Fillmore", 0.85),
        ("Red Rocks Amphitheatre", "Red Rocks", 0.75),
        ("Madison Square Garden", "MSG", 0.45),
    ]

    print("Similarity tests:")
    for name1, name2, expected in test_cases:
        score = manager.similarity_score(name1, name2)
        print(f"  '{name1}' vs '{name2}': {score:.2f} (expected ~{expected})")

    db.close()
