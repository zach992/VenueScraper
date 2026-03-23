"""
Improved Songkick web scraper
Updated to work with Songkick's current HTML structure (2026)
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import time
import logging
import re
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SongkickImprovedScraper:
    """
    Improved web scraper for Songkick concert listings
    Updated for current website structure
    """

    BASE_URL = "https://www.songkick.com"

    def __init__(self):
        """Initialize Songkick scraper"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
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
            logger.debug(f"Direct URL failed for {artist_name}: {e}")

        # Fallback: use search
        try:
            search_url = f"{self.BASE_URL}/search"
            params = {'query': artist_name, 'type': 'artists'}
            response = self.session.get(search_url, params=params, timeout=10)

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')

                # Try multiple possible selectors
                artist_links = (
                    soup.select('li.artist a[href*="/artists/"]') or
                    soup.select('a[href*="/artists/"]')
                )

                # Verify the result actually matches the search query
                query_lower = artist_name.lower()
                for artist_link in artist_links:
                    link_text = artist_link.get_text(strip=True).lower()
                    href = artist_link.get('href', '')
                    # Check if link text or URL slug matches the query
                    slug_from_href = href.split('/')[-1].replace('-', ' ') if '/artists/' in href else ''
                    # Remove numeric prefix from slug (e.g., "29793-snarky-puppy" -> "snarky puppy")
                    slug_from_href = re.sub(r'^\d+-', '', slug_from_href)

                    if (query_lower in link_text or link_text in query_lower or
                            query_lower in slug_from_href or slug_from_href in query_lower):
                        if href.startswith('/'):
                            url = self.BASE_URL + href
                        else:
                            url = href
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
            logger.info(f"Fetching events from: {artist_url}")

            response = self.session.get(artist_url, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            events = []

            # Method 1: Try to find JSON-LD structured data
            script_tags = soup.find_all('script', type='application/ld+json')
            for script in script_tags:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, list):
                        for item in data:
                            if item.get('@type') == 'MusicEvent':
                                events.append(self._parse_json_event(item))
                    elif data.get('@type') == 'MusicEvent':
                        events.append(self._parse_json_event(data))
                except:
                    continue

            # Method 2: Try various CSS selectors for event listings
            event_selectors = [
                'li[class*="event"]',
                'div[class*="event"]',
                '[data-testid*="event"]',
                'article',
                '.event-listings li',
                'li.event-listing',
            ]

            for selector in event_selectors:
                event_items = soup.select(selector)
                if event_items:
                    logger.info(f"Found {len(event_items)} potential events using selector: {selector}")
                    for event_item in event_items:
                        try:
                            event_data = self._parse_event_item(event_item)
                            if event_data and event_data.get('venue_name'):
                                # Avoid duplicates
                                if not any(e.get('id') == event_data.get('id') for e in events):
                                    events.append(event_data)
                        except Exception as e:
                            logger.debug(f"Error parsing event item: {e}")
                            continue

                    if events:
                        break  # Stop trying selectors if we found events

            # Method 3: Look for any links to /concerts/ which indicate events
            if not events:
                concert_links = soup.select('a[href*="/concerts/"]')
                logger.info(f"Found {len(concert_links)} concert links")

                for link in concert_links[:20]:  # Limit to avoid processing too many
                    try:
                        event_data = self._parse_from_link(link)
                        if event_data and event_data.get('venue_name'):
                            if not any(e.get('id') == event_data.get('id') for e in events):
                                events.append(event_data)
                    except Exception as e:
                        logger.debug(f"Error parsing concert link: {e}")
                        continue

            logger.info(f"Found {len(events)} total events")
            return events

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching events from {artist_url}: {e}")
            return []

    def _parse_json_event(self, event_json: Dict) -> Dict:
        """Parse event from JSON-LD structured data"""
        location = event_json.get('location', {})
        address = location.get('address', {})

        return {
            'datetime': event_json.get('startDate'),
            'url': event_json.get('url', ''),
            'venue_name': location.get('name', ''),
            'city': address.get('addressLocality', ''),
            'state': address.get('addressRegion', ''),
            'country': address.get('addressCountry', ''),
            'id': event_json.get('url', '').split('/')[-1] if event_json.get('url') else None
        }

    def _parse_event_item(self, event_item) -> Optional[Dict]:
        """Parse a single event listing element"""
        event_data = {}

        # Date - try multiple selectors
        date_elem = (
            event_item.select_one('time[datetime]') or
            event_item.select_one('[datetime]') or
            event_item.select_one('[class*="date"]')
        )
        if date_elem:
            event_data['datetime'] = date_elem.get('datetime') or date_elem.get_text(strip=True)

        # Venue - try multiple selectors
        venue_elem = (
            event_item.select_one('[class*="venue"]') or
            event_item.select_one('[data-testid*="venue"]') or
            event_item.find(text=re.compile(r'\w+\s+(Hall|Theatre|Theater|Arena|Center|Club|Bar)', re.I))
        )
        if venue_elem:
            if hasattr(venue_elem, 'get_text'):
                event_data['venue_name'] = venue_elem.get_text(strip=True)
            else:
                # It's a text node, find parent
                parent = venue_elem.parent
                event_data['venue_name'] = parent.get_text(strip=True) if parent else str(venue_elem)

        # Location - try multiple selectors
        location_elem = (
            event_item.select_one('[class*="location"]') or
            event_item.select_one('[class*="city"]') or
            event_item.select_one('[class*="where"]')
        )
        if location_elem:
            location_text = location_elem.get_text(strip=True)
            self._parse_location(location_text, event_data)

        # URL - try to find event link
        link_elem = (
            event_item.select_one('a[href*="/concerts/"]') or
            event_item.find('a', href=True)
        )
        if link_elem:
            href = link_elem.get('href', '')
            if '/concerts/' in href:
                if href.startswith('/'):
                    event_data['url'] = self.BASE_URL + href
                else:
                    event_data['url'] = href
                event_data['id'] = href.split('/')[-1]

        return event_data if event_data else None

    def _parse_from_link(self, link_elem) -> Optional[Dict]:
        """Extract event data from a concert link element"""
        event_data = {}

        href = link_elem.get('href', '')
        if '/concerts/' in href:
            if href.startswith('/'):
                event_data['url'] = self.BASE_URL + href
            else:
                event_data['url'] = href
            event_data['id'] = href.split('/')[-1]

        # Try to extract info from link text or nearby elements
        link_text = link_elem.get_text(strip=True)
        parent = link_elem.parent

        if parent:
            # Look for venue in parent or siblings
            venue_text = parent.get_text(strip=True)
            # Extract potential venue name (usually contains venue-like words)
            venue_match = re.search(r'(\w+\s+(?:Hall|Theatre|Theater|Arena|Center|Centre|Club|Bar|Room|Garden|Stadium|Festival))', venue_text, re.I)
            if venue_match:
                event_data['venue_name'] = venue_match.group(1)

            # Look for location
            location_match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*([A-Z]{2})', venue_text)
            if location_match:
                event_data['city'] = location_match.group(1)
                event_data['state'] = location_match.group(2)

        return event_data if event_data.get('venue_name') else None

    def _parse_location(self, location_text: str, event_data: Dict):
        """Parse location string into city, state, country"""
        # Parse "City, Country" or "City, State, Country"
        parts = [p.strip() for p in location_text.split(',')]
        if len(parts) >= 1:
            event_data['city'] = parts[0]
        if len(parts) >= 2:
            # Check if it's a US state (2 letters) or country
            if len(parts[1]) == 2:
                event_data['state'] = parts[1]
            else:
                event_data['country'] = parts[1]
        if len(parts) >= 3:
            event_data['country'] = parts[2]

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
            'latitude': None,
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
        url = event.get('url', '')
        is_festival = '/festivals/' in url
        festival_name = ''
        if is_festival:
            # Extract festival name from URL like /festivals/1048-big-ears/
            match = re.search(r'/festivals/\d+-([^/]+)', url)
            if match:
                festival_name = match.group(1).replace('-', ' ').title()

        return {
            'show_date': event.get('datetime'),
            'show_url': url,
            'source': 'songkick',
            'external_id': event.get('id'),
            'is_festival': is_festival,
            'festival_name': festival_name
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

        # Rate limiting
        time.sleep(1.5)

        return results


    def get_related_artists(self, artist_name: str) -> List[str]:
        """
        Get related/similar artists from an artist's Songkick page.
        Returns list of artist name strings.
        """
        artist_url = self.search_artist(artist_name)
        if not artist_url:
            return []

        try:
            response = self.session.get(artist_url, timeout=15)
            if response.status_code != 200:
                return []

            soup = BeautifulSoup(response.content, 'html.parser')

            # Find the "Related artists" section
            related_section = soup.select_one('div.related-artists-v2')
            if not related_section:
                return []

            # Extract artist names
            name_elements = related_section.select('div.related-artists-v2__artist-name')
            names = [el.get_text(strip=True) for el in name_elements if el.get_text(strip=True)]

            logger.info(f"Found {len(names)} related artists for {artist_name}")
            time.sleep(1.0)
            return names

        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting related artists for {artist_name}: {e}")
            return []


if __name__ == "__main__":
    # Test the scraper
    scraper = SongkickImprovedScraper()

    # Test with Esperanza Spalding since we know she has shows
    test_artist = "Esperanza Spalding"
    events = scraper.scrape_artist(test_artist)
    print(f"\n{test_artist}: {len(events)} upcoming shows")
    for i, (venue, show) in enumerate(events[:5], 1):
        print(f"  {i}. {venue['name']} in {venue['city']}, {venue.get('state', venue.get('country', ''))}")
