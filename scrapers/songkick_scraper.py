"""
Songkick web scraper
Scrapes artist tour dates and venue information from Songkick public pages
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import time
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SongkickScraper:
    """
    Web scraper for Songkick concert listings
    Note: This scrapes public pages as Songkick API is closed to new applications
    """

    BASE_URL = "https://www.songkick.com"

    def __init__(self):
        """Initialize Songkick scraper"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def search_artist(self, artist_name: str) -> Optional[str]:
        """
        Search for an artist and get their Songkick URL

        Args:
            artist_name: Name of the artist

        Returns:
            Artist's Songkick URL or None
        """
        # Songkick artist URLs are typically formatted as /artists/artist-name
        search_name = artist_name.lower().replace(' ', '-').replace('&', 'and')
        search_name = re.sub(r'[^a-z0-9-]', '', search_name)

        # Try direct artist page first
        possible_url = f"{self.BASE_URL}/artists/{search_name}"

        try:
            response = self.session.get(possible_url, timeout=10)
            if response.status_code == 200:
                logger.info(f"Found artist page for {artist_name}: {possible_url}")
                return possible_url
        except requests.exceptions.RequestException as e:
            logger.warning(f"Direct URL failed for {artist_name}: {e}")

        # Fallback: use search
        try:
            search_url = f"{self.BASE_URL}/search"
            params = {'query': artist_name, 'type': 'artists'}
            response = self.session.get(search_url, params=params, timeout=10)

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                # Look for artist link in search results
                artist_link = soup.select_one('li.artist a[href*="/artists/"]')
                if artist_link:
                    url = self.BASE_URL + artist_link['href']
                    logger.info(f"Found artist via search: {url}")
                    return url
        except Exception as e:
            logger.error(f"Error searching for {artist_name}: {e}")

        logger.warning(f"Could not find artist page for {artist_name}")
        return None

    def get_artist_events(self, artist_url: str) -> List[Dict]:
        """
        Scrape events from an artist's Songkick page

        Args:
            artist_url: Full URL to artist's Songkick page

        Returns:
            List of event dictionaries
        """
        try:
            # Get calendar/upcoming shows page
            calendar_url = artist_url.rstrip('/') + '/calendar'
            logger.info(f"Fetching events from: {calendar_url}")

            response = self.session.get(calendar_url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            events = []

            # Find all event listings
            event_items = soup.select('li.event-listing')

            for event_item in event_items:
                try:
                    event_data = self._parse_event_item(event_item)
                    if event_data:
                        events.append(event_data)
                except Exception as e:
                    logger.warning(f"Error parsing event item: {e}")
                    continue

            logger.info(f"Found {len(events)} events")
            return events

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching events from {artist_url}: {e}")
            return []

    def _parse_event_item(self, event_item) -> Optional[Dict]:
        """Parse a single event listing element"""
        event_data = {}

        # Date
        date_elem = event_item.select_one('time[datetime]')
        if date_elem:
            event_data['datetime'] = date_elem.get('datetime')

        # Venue
        venue_elem = event_item.select_one('.venue-name')
        if venue_elem:
            event_data['venue_name'] = venue_elem.get_text(strip=True)

        # Location
        location_elem = event_item.select_one('.location')
        if location_elem:
            location_text = location_elem.get_text(strip=True)
            # Parse "City, Country" or "City, State, Country"
            parts = [p.strip() for p in location_text.split(',')]
            if len(parts) >= 2:
                event_data['city'] = parts[0]
                event_data['country'] = parts[-1]
                if len(parts) == 3:
                    event_data['state'] = parts[1]

        # Event URL
        event_link = event_item.select_one('a[href*="/concerts/"]')
        if event_link:
            event_data['url'] = self.BASE_URL + event_link['href']
            # Extract event ID from URL
            event_id = event_link['href'].split('/')[-1]
            event_data['id'] = event_id

        return event_data if event_data else None

    def parse_venue_from_event(self, event: Dict) -> Optional[Dict]:
        """
        Extract venue information from an event

        Args:
            event: Event dictionary from Songkick scraper

        Returns:
            Dictionary with venue information
        """
        if 'venue_name' not in event:
            return None

        return {
            'name': event.get('venue_name'),
            'city': event.get('city'),
            'state': event.get('state', ''),
            'country': event.get('country'),
            'latitude': None,  # Not available from basic scraping
            'longitude': None,
            'address': '',
            'venue_url': event.get('url', ''),
            'source': 'songkick',
            'external_id': f"songkick_{event.get('id', '')}" if event.get('id') else None
        }

    def parse_show_from_event(self, event: Dict) -> Optional[Dict]:
        """
        Extract show information from an event

        Args:
            event: Event dictionary from Songkick scraper

        Returns:
            Dictionary with show information
        """
        return {
            'show_date': event.get('datetime'),
            'show_url': event.get('url'),
            'source': 'songkick',
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
        # Find artist page
        artist_url = self.search_artist(artist_name)
        if not artist_url:
            return []

        # Get events
        events = self.get_artist_events(artist_url)
        results = []

        for event in events:
            venue_data = self.parse_venue_from_event(event)
            show_data = self.parse_show_from_event(event)

            if venue_data and show_data:
                results.append((venue_data, show_data))

        # Rate limiting - be respectful
        time.sleep(1.0)

        return results

    def scrape_multiple_artists(self, artist_names: List[str], delay: float = 2.0) -> Dict[str, List[tuple[Dict, Dict]]]:
        """
        Scrape events for multiple artists

        Args:
            artist_names: List of artist names
            delay: Delay between requests in seconds (higher for web scraping)

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
    scraper = SongkickScraper()

    # Example: Scrape an artist
    test_artist = "Radiohead"
    events = scraper.scrape_artist(test_artist)
    print(f"\n{test_artist}: {len(events)} upcoming shows")
    if events:
        venue, show = events[0]
        print(f"  Next show: {venue['name']} in {venue['city']}, {venue['country']}")
