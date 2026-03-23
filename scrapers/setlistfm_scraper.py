"""
Setlist.fm web scraper
Scrapes upcoming concert dates and venue information from setlist.fm
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Tuple
import time
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SetlistfmScraper:
    """Web scraper for Setlist.fm concert listings"""

    BASE_URL = "https://www.setlist.fm"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        })

    def search_artist(self, artist_name: str) -> Optional[str]:
        """
        Search for an artist and return their Setlist.fm URL.
        Returns None if not found.
        """
        try:
            params = {'query': artist_name, 'type': 'artists'}
            response = self.session.get(f"{self.BASE_URL}/search", params=params, timeout=15)

            if response.status_code != 200:
                logger.warning(f"Setlist.fm search returned {response.status_code}")
                return None

            soup = BeautifulSoup(response.content, 'html.parser')

            # Look for artist link in search results
            # Pattern: setlists/artist-name-hexid.html (relative or absolute)
            artist_link = soup.select_one('a[href*="setlists/"][href$=".html"]')
            if artist_link:
                href = artist_link.get('href', '')
                # Normalize to full URL
                href = href.lstrip('./').lstrip('/')
                url = f"{self.BASE_URL}/{href}"
                logger.info(f"Found artist on Setlist.fm: {url}")
                return url

        except requests.exceptions.RequestException as e:
            logger.error(f"Error searching Setlist.fm for {artist_name}: {e}")

        logger.warning(f"Could not find {artist_name} on Setlist.fm")
        return None

    def get_artist_events(self, artist_url: str) -> List[Dict]:
        """
        Scrape upcoming events from an artist's Setlist.fm page.
        """
        try:
            response = self.session.get(artist_url, timeout=15)
            if response.status_code != 200:
                logger.warning(f"Failed to fetch {artist_url}: {response.status_code}")
                return []

            soup = BeautifulSoup(response.content, 'html.parser')
            events = []

            # Find upcoming events section
            upcoming_header = soup.find('h2', string=re.compile('Upcoming', re.I))
            if not upcoming_header:
                logger.info("No upcoming events section found")
                return []

            # Get the container after the header
            container = upcoming_header.find_next('ul', class_='noList')
            if not container:
                return []

            # Parse each event list item
            for li in container.select('li.setlist'):
                event = self._parse_event_item(li)
                if event and event.get('venue_name'):
                    events.append(event)

            logger.info(f"Found {len(events)} upcoming events on Setlist.fm")
            return events

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching events from {artist_url}: {e}")
            return []

    def _parse_event_item(self, li_element) -> Optional[Dict]:
        """Parse a single event list item from the upcoming events section."""
        event = {}

        # Extract date from smallDateBlock
        date_block = li_element.select_one('span.smallDateBlock')
        if date_block:
            month_el = date_block.select_one('strong.text-uppercase')
            day_el = date_block.select_one('strong.big')
            year_el = date_block.select_one('span')
            if month_el and day_el and year_el:
                month = month_el.get_text(strip=True)
                day = day_el.get_text(strip=True)
                year = year_el.get_text(strip=True)
                event['datetime'] = f"{month} {day}, {year}"

        # Extract venue name
        content_div = li_element.select_one('div.column.content')
        if content_div:
            venue_strong = content_div.select_one('strong')
            if venue_strong:
                event['venue_name'] = venue_strong.get_text(strip=True)

            # Extract location from subline
            subline = content_div.select_one('span.subline > span')
            if subline:
                location_text = subline.get_text(strip=True)
                self._parse_location(location_text, event)

        # Extract event URL and ID
        event_link = li_element.select_one('a[href*="/upcoming/"]')
        if event_link:
            href = event_link.get('href', '')
            # Normalize URL
            if href.startswith('../'):
                href = href.replace('../', '/')
            if href.startswith('/'):
                event['url'] = self.BASE_URL + href
            else:
                event['url'] = href

            # Extract ID from URL (last hex part before .html)
            id_match = re.search(r'-([a-f0-9]+)\.html', href)
            if id_match:
                event['id'] = id_match.group(1)

        return event if event.get('venue_name') else None

    def _parse_location(self, location_text: str, event: Dict):
        """Parse location string like 'Washington, DC, USA' or 'Madrid, Spain'"""
        parts = [p.strip() for p in location_text.split(',')]

        if len(parts) >= 1:
            event['city'] = parts[0]

        if len(parts) == 2:
            # "City, Country" (international) or could be "City, State"
            part = parts[1].strip()
            if len(part) == 2 and part.isupper():
                event['state'] = part
                event['country'] = 'USA'
            else:
                event['country'] = part

        elif len(parts) >= 3:
            # "City, State, Country"
            event['state'] = parts[1].strip()
            event['country'] = parts[2].strip()

    def parse_venue_from_event(self, event: Dict) -> Optional[Dict]:
        """Extract venue data from an event."""
        if 'venue_name' not in event:
            return None

        return {
            'name': event.get('venue_name'),
            'city': event.get('city'),
            'state': event.get('state', ''),
            'country': event.get('country'),
            'latitude': None,
            'longitude': None,
            'address': '',
            'venue_url': event.get('url', ''),
            'source': 'setlistfm',
            'external_id': f"setlistfm_{event.get('id', '')}" if event.get('id') else None
        }

    def _detect_festival(self, venue_name: str) -> tuple:
        """Detect if a venue name is actually a festival. Returns (is_festival, festival_name)."""
        if not venue_name:
            return False, ''
        name_lower = venue_name.lower()
        festival_keywords = ['festival', 'fest ', 'supercruise']
        for keyword in festival_keywords:
            if keyword in name_lower:
                return True, venue_name
        # Check if name ends with a year (e.g., "Noches del Botánico 2026")
        if re.search(r'\b20\d{2}$', venue_name):
            return True, venue_name
        return False, ''

    def parse_show_from_event(self, event: Dict) -> Optional[Dict]:
        """Extract show data from an event."""
        is_festival, festival_name = self._detect_festival(event.get('venue_name', ''))
        return {
            'show_date': event.get('datetime'),
            'show_url': event.get('url'),
            'source': 'setlistfm',
            'external_id': event.get('id'),
            'is_festival': is_festival,
            'festival_name': festival_name
        }

    def scrape_artist(self, artist_name: str) -> List[Tuple[Dict, Dict]]:
        """
        Scrape all upcoming events and venues for an artist.
        Returns list of (venue_data, show_data) tuples.
        """
        artist_url = self.search_artist(artist_name)
        if not artist_url:
            return []

        # Rate limiting
        time.sleep(1.5)

        events = self.get_artist_events(artist_url)
        results = []

        for event in events:
            venue_data = self.parse_venue_from_event(event)
            show_data = self.parse_show_from_event(event)

            if venue_data and show_data:
                results.append((venue_data, show_data))

        # Rate limiting
        time.sleep(1.5)

        return results


if __name__ == "__main__":
    scraper = SetlistfmScraper()

    test_artist = "Snarky Puppy"
    print(f"Searching for {test_artist}...")
    events = scraper.scrape_artist(test_artist)
    print(f"\n{test_artist}: {len(events)} upcoming shows")
    for i, (venue, show) in enumerate(events[:10], 1):
        print(f"  {i}. {venue['name']} in {venue['city']}, {venue.get('state', '')} {venue.get('country', '')} ({show.get('show_date', 'no date')})")
