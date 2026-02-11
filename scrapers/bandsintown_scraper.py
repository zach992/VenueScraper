"""
Bandsintown API scraper
Fetches artist tour dates and venue information from Bandsintown
"""

import requests
from typing import List, Dict, Optional
from datetime import datetime
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BandsintownScraper:
    """
    Scraper for Bandsintown API
    API Documentation: https://www.bandsintown.com/api/overview
    """

    BASE_URL = "https://rest.bandsintown.com"

    def __init__(self, app_id: str = "venue_scraper"):
        """
        Initialize Bandsintown scraper

        Args:
            app_id: Your application identifier (required by Bandsintown)
        """
        self.app_id = app_id
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.bandsintown.com/'
        })

    def get_artist_events(self, artist_name: str) -> List[Dict]:
        """
        Get upcoming events for an artist

        Args:
            artist_name: Name of the artist

        Returns:
            List of event dictionaries
        """
        url = f"{self.BASE_URL}/artists/{requests.utils.quote(artist_name)}/events"
        params = {
            'app_id': self.app_id
        }

        try:
            logger.info(f"Fetching events for artist: {artist_name}")
            response = self.session.get(url, params=params, timeout=10)

            if response.status_code == 404:
                logger.warning(f"Artist not found: {artist_name}")
                return []

            response.raise_for_status()
            events = response.json()

            logger.info(f"Found {len(events)} events for {artist_name}")
            return events if isinstance(events, list) else []

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching events for {artist_name}: {e}")
            return []

    def parse_venue_from_event(self, event: Dict) -> Optional[Dict]:
        """
        Extract venue information from an event

        Args:
            event: Event dictionary from Bandsintown API

        Returns:
            Dictionary with venue information
        """
        if 'venue' not in event:
            return None

        venue_data = event['venue']

        return {
            'name': venue_data.get('name'),
            'city': venue_data.get('city'),
            'state': venue_data.get('region', ''),
            'country': venue_data.get('country'),
            'latitude': float(venue_data.get('latitude', 0)) if venue_data.get('latitude') else None,
            'longitude': float(venue_data.get('longitude', 0)) if venue_data.get('longitude') else None,
            'address': venue_data.get('location', ''),
            'venue_url': event.get('url', ''),
            'source': 'bandsintown',
            'external_id': f"bandsintown_{venue_data.get('id', '')}" if venue_data.get('id') else None
        }

    def parse_show_from_event(self, event: Dict) -> Optional[Dict]:
        """
        Extract show information from an event

        Args:
            event: Event dictionary from Bandsintown API

        Returns:
            Dictionary with show information
        """
        return {
            'show_date': event.get('datetime'),
            'show_url': event.get('url'),
            'source': 'bandsintown',
            'external_id': event.get('id')
        }

    def scrape_artist(self, artist_name: str) -> List[tuple[Dict, Dict]]:
        """
        Scrape all events and venues for an artist

        Args:
            artist_name: Name of the artist

        Returns:
            List of (venue_data, show_data) tuples
        """
        events = self.get_artist_events(artist_name)
        results = []

        for event in events:
            venue_data = self.parse_venue_from_event(event)
            show_data = self.parse_show_from_event(event)

            if venue_data and show_data:
                results.append((venue_data, show_data))

        # Rate limiting - be nice to the API
        time.sleep(0.5)

        return results

    def scrape_multiple_artists(self, artist_names: List[str], delay: float = 1.0) -> Dict[str, List[tuple[Dict, Dict]]]:
        """
        Scrape events for multiple artists

        Args:
            artist_names: List of artist names
            delay: Delay between requests in seconds

        Returns:
            Dictionary mapping artist names to their venues and shows
        """
        results = {}

        for artist in artist_names:
            results[artist] = self.scrape_artist(artist)
            time.sleep(delay)

        return results


if __name__ == "__main__":
    # Test the scraper
    scraper = BandsintownScraper()

    # Example: Scrape a few artists
    test_artists = ["Radiohead", "The National", "Taylor Swift"]

    for artist in test_artists:
        events = scraper.scrape_artist(artist)
        print(f"\n{artist}: {len(events)} upcoming shows")
        if events:
            venue, show = events[0]
            print(f"  Next show: {venue['name']} in {venue['city']}, {venue['country']}")
