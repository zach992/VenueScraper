"""
Bandsintown Web Scraper (Alternative to API)
Scrapes artist tour dates directly from Bandsintown website
Use this when the API is blocked or unavailable
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import time
import logging
import json
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BandsintownWebScraper:
    """
    Web scraper for Bandsintown website
    This is an alternative when the API returns 403 errors
    """

    BASE_URL = "https://www.bandsintown.com"

    def __init__(self):
        """Initialize Bandsintown web scraper"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })

    def get_artist_events(self, artist_name: str) -> List[Dict]:
        """
        Get upcoming events for an artist by scraping their page

        Args:
            artist_name: Name of the artist

        Returns:
            List of event dictionaries
        """
        # Format artist name for URL
        artist_slug = artist_name.lower().replace(' ', '-')
        artist_slug = re.sub(r'[^a-z0-9-]', '', artist_slug)

        url = f"{self.BASE_URL}/a/{artist_slug}"

        try:
            logger.info(f"Fetching events for artist: {artist_name} from {url}")
            response = self.session.get(url, timeout=15)

            if response.status_code == 404:
                logger.warning(f"Artist page not found: {artist_name}")
                return []

            response.raise_for_status()

            # Parse the HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            events = []

            # Look for JSON data in script tags (Bandsintown often embeds data this way)
            script_tags = soup.find_all('script', type='application/ld+json')
            for script in script_tags:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and data.get('@type') == 'MusicEvent':
                        events.append(self._parse_json_event(data))
                    elif isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and item.get('@type') == 'MusicEvent':
                                events.append(self._parse_json_event(item))
                except:
                    continue

            # Also try to find events in HTML structure
            event_cards = soup.select('[data-testid="event-card"], .event-card, div[class*="EventCard"]')
            for card in event_cards:
                try:
                    event_data = self._parse_event_card(card)
                    if event_data:
                        events.append(event_data)
                except Exception as e:
                    logger.debug(f"Error parsing event card: {e}")
                    continue

            logger.info(f"Found {len(events)} events for {artist_name}")
            return events

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching events for {artist_name}: {e}")
            return []

    def _parse_json_event(self, event_json: Dict) -> Dict:
        """Parse event from JSON-LD structured data"""
        location = event_json.get('location', {})

        return {
            'datetime': event_json.get('startDate'),
            'url': event_json.get('url', ''),
            'venue_name': location.get('name', ''),
            'city': location.get('address', {}).get('addressLocality', ''),
            'state': location.get('address', {}).get('addressRegion', ''),
            'country': location.get('address', {}).get('addressCountry', ''),
            'id': event_json.get('url', '').split('/')[-1] if event_json.get('url') else None
        }

    def _parse_event_card(self, card) -> Optional[Dict]:
        """Parse event from HTML event card"""
        event_data = {}

        # Try to extract date/time
        date_elem = card.select_one('time, [datetime], [data-date]')
        if date_elem:
            event_data['datetime'] = date_elem.get('datetime') or date_elem.get('data-date')

        # Try to extract venue name
        venue_elem = card.select_one('[class*="venue"], [data-venue]')
        if venue_elem:
            event_data['venue_name'] = venue_elem.get_text(strip=True)

        # Try to extract location
        location_elem = card.select_one('[class*="location"], [class*="city"]')
        if location_elem:
            location_text = location_elem.get_text(strip=True)
            # Try to parse "City, State" or "City, Country"
            parts = [p.strip() for p in location_text.split(',')]
            if len(parts) >= 1:
                event_data['city'] = parts[0]
            if len(parts) >= 2:
                event_data['state'] = parts[1]
            if len(parts) >= 3:
                event_data['country'] = parts[2]

        # Try to extract URL
        link_elem = card.select_one('a[href*="/e/"]')
        if link_elem:
            href = link_elem.get('href', '')
            if href.startswith('/'):
                event_data['url'] = self.BASE_URL + href
            else:
                event_data['url'] = href

            # Extract event ID from URL
            event_data['id'] = href.split('/')[-1]

        return event_data if event_data.get('venue_name') else None

    def parse_venue_from_event(self, event: Dict) -> Optional[Dict]:
        """
        Extract venue information from an event

        Args:
            event: Event dictionary from scraper

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
            'latitude': None,  # Not available from web scraping
            'longitude': None,
            'address': '',
            'venue_url': event.get('url', ''),
            'source': 'bandsintown_web',
            'external_id': f"bandsintown_web_{event.get('id', '')}" if event.get('id') else None
        }

    def parse_show_from_event(self, event: Dict) -> Optional[Dict]:
        """
        Extract show information from an event

        Args:
            event: Event dictionary from scraper

        Returns:
            Dictionary with show information
        """
        return {
            'show_date': event.get('datetime'),
            'show_url': event.get('url'),
            'source': 'bandsintown_web',
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

        # Rate limiting
        time.sleep(1.0)

        return results


if __name__ == "__main__":
    # Test the scraper
    scraper = BandsintownWebScraper()

    # Example: Test with an artist
    test_artist = "Radiohead"
    events = scraper.scrape_artist(test_artist)
    print(f"\n{test_artist}: {len(events)} upcoming shows")
    if events:
        venue, show = events[0]
        print(f"  Next show: {venue['name']} in {venue['city']}, {venue['country']}")
