#!/usr/bin/env python3
"""
Demo/test script showing venue scraper functionality with mock data
Use this to verify the system works before running live scrapers
"""

from database import VenueDatabase
from venue_manager import VenueManager
import os

def main():
    print("=" * 60)
    print("VENUE SCRAPER DEMO")
    print("=" * 60)

    # Create a test database
    test_db_path = "test_venues.db"

    # Remove old test database if it exists
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

    # Initialize database and manager
    db = VenueDatabase(test_db_path)
    manager = VenueManager(db)

    print("\n1. Database initialized")
    print(f"   Database: {test_db_path}")
    print(f"   Venue count: {db.get_venues_count()}")

    # Mock data - simulating scraped data from Bandsintown
    mock_artist = "Radiohead"
    mock_scraped_data = [
        # Event 1: Red Rocks
        (
            {  # Venue data
                'name': 'Red Rocks Amphitheatre',
                'city': 'Morrison',
                'state': 'CO',
                'country': 'United States',
                'latitude': 39.6654,
                'longitude': -105.2057,
                'address': '18300 W Alameda Pkwy',
                'venue_url': 'https://www.bandsintown.com/v/1234',
                'source': 'bandsintown',
                'external_id': 'bandsintown_1234'
            },
            {  # Show data
                'show_date': '2026-06-15T19:00:00',
                'show_url': 'https://www.bandsintown.com/e/1234',
                'source': 'bandsintown',
                'external_id': 'event_1234'
            }
        ),
        # Event 2: Greek Theatre
        (
            {
                'name': 'Greek Theatre',
                'city': 'Berkeley',
                'state': 'CA',
                'country': 'United States',
                'latitude': 37.8735,
                'longitude': -122.2544,
                'address': '2001 Gayley Rd',
                'venue_url': 'https://www.bandsintown.com/v/5678',
                'source': 'bandsintown',
                'external_id': 'bandsintown_5678'
            },
            {
                'show_date': '2026-06-20T20:00:00',
                'show_url': 'https://www.bandsintown.com/e/5678',
                'source': 'bandsintown',
                'external_id': 'event_5678'
            }
        ),
        # Event 3: Madison Square Garden
        (
            {
                'name': 'Madison Square Garden',
                'city': 'New York',
                'state': 'NY',
                'country': 'United States',
                'latitude': 40.7505,
                'longitude': -73.9934,
                'address': '4 Pennsylvania Plaza',
                'venue_url': 'https://www.bandsintown.com/v/9999',
                'source': 'bandsintown',
                'external_id': 'bandsintown_9999'
            },
            {
                'show_date': '2026-07-01T20:00:00',
                'show_url': 'https://www.bandsintown.com/e/9999',
                'source': 'bandsintown',
                'external_id': 'event_9999'
            }
        )
    ]

    print(f"\n2. Processing {len(mock_scraped_data)} events for {mock_artist}")

    # Process the mock data
    stats = manager.process_scraped_data(mock_artist, mock_scraped_data)

    print(f"\n3. Processing complete!")
    print(f"   Events processed: {stats['total_events']}")
    print(f"   New venues added: {stats['new_venues']}")
    print(f"   Existing venues: {stats['existing_venues']}")
    print(f"   New shows added: {stats['new_shows']}")

    # Show venues in database
    print(f"\n4. Venues in database:")
    venues = db.get_all_venues()
    for venue in venues:
        print(f"   - {venue['name']}")
        print(f"     {venue['city']}, {venue['state']}, {venue['country']}")
        print(f"     Source: {venue['source']}")
        print()

    # Test deduplication by processing same data again
    print("5. Testing deduplication - processing same events again...")
    stats2 = manager.process_scraped_data(mock_artist, mock_scraped_data)

    print(f"\n6. Deduplication test results:")
    print(f"   New venues added: {stats2['new_venues']} (should be 0)")
    print(f"   Existing venues found: {stats2['existing_venues']} (should be {len(mock_scraped_data)})")
    print(f"   Total venues in DB: {db.get_venues_count()} (should still be {len(mock_scraped_data)})")

    # Test fuzzy matching with slight name variation
    print("\n7. Testing fuzzy matching with name variation...")
    fuzzy_test_data = [
        (
            {
                'name': 'Red Rocks Amphitheater',  # Slightly different spelling
                'city': 'Morrison',
                'state': 'CO',
                'country': 'United States',
                'latitude': 39.6654,
                'longitude': -105.2057,
                'address': '18300 W Alameda Pkwy',
                'venue_url': 'https://www.songkick.com/venues/123',
                'source': 'songkick',
                'external_id': 'songkick_123'
            },
            {
                'show_date': '2026-08-01T19:00:00',
                'show_url': 'https://www.songkick.com/concerts/123',
                'source': 'songkick',
                'external_id': 'sk_event_123'
            }
        )
    ]

    stats3 = manager.process_scraped_data(mock_artist, fuzzy_test_data)
    print(f"\n8. Fuzzy match results:")
    print(f"   New venues: {stats3['new_venues']} (fuzzy matching may catch this)")
    print(f"   Total venues in DB: {db.get_venues_count()}")

    # Summary
    summary = manager.get_summary()
    print("\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)
    print(f"Total venues in database: {summary['total_venues']}")
    print(f"\nRecent venues:")
    for venue in summary['recent_venues']:
        print(f"  • {venue['name']} ({venue['city']}, {venue['country']})")

    print(f"\n✓ Demo completed successfully!")
    print(f"✓ Test database saved to: {test_db_path}")
    print(f"\nThe scraper is ready to use with live data.")
    print(f"Edit config.json with your artists and run: python venue_scraper.py")

    db.close()


if __name__ == "__main__":
    main()
