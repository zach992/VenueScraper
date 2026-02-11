#!/usr/bin/env python3
"""
Main venue scraper orchestration script
Coordinates scrapers, manages database, and generates reports
"""

import argparse
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict

from database import VenueDatabase
from venue_manager import VenueManager
from scrapers.songkick_improved_scraper import SongkickImprovedScraper

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('venue_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class VenueScraper:
    """Main orchestrator for venue scraping operations"""

    def __init__(self, config_path: str = "config.json", db_path: str = "venues.db"):
        """
        Initialize venue scraper

        Args:
            config_path: Path to configuration file
            db_path: Path to SQLite database
        """
        self.config_path = config_path
        self.db_path = db_path
        self.config = self.load_config()

        # Initialize database and manager
        self.db = VenueDatabase(db_path)
        self.manager = VenueManager(self.db)

        # Initialize scrapers
        self.scrapers = {
            'songkick': SongkickImprovedScraper()
        }

    def load_config(self) -> Dict:
        """Load configuration from file"""
        config_file = Path(self.config_path)

        if not config_file.exists():
            logger.warning(f"Config file not found: {self.config_path}")
            logger.info("Using default configuration")
            return self.get_default_config()

        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                logger.info(f"Loaded configuration from {self.config_path}")
                return config
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return self.get_default_config()

    def get_default_config(self) -> Dict:
        """Get default configuration"""
        return {
            "artists": [
                "Radiohead",
                "The National",
                "Arcade Fire"
            ],
            "scrapers_enabled": {
                "bandsintown": True,
                "songkick": True
            },
            "scraper_delays": {
                "bandsintown": 1.0,
                "songkick": 2.0
            }
        }

    def scrape_all_artists(self) -> Dict:
        """
        Scrape all configured artists from all enabled scrapers

        Returns:
            Dictionary with scraping results and statistics
        """
        logger.info("=" * 60)
        logger.info("Starting venue scraping run")
        logger.info("=" * 60)

        artists = self.config.get('artists', [])
        enabled_scrapers = self.config.get('scrapers_enabled', {})

        if not artists:
            logger.warning("No artists configured!")
            return {'error': 'No artists configured'}

        logger.info(f"Artists to scrape: {len(artists)}")
        logger.info(f"Artists: {', '.join(artists)}")

        overall_stats = {
            'start_time': datetime.now().isoformat(),
            'artists_processed': 0,
            'total_new_venues': 0,
            'total_new_shows': 0,
            'total_events': 0,
            'scrapers_used': [],
            'artist_details': {}
        }

        # Process each artist
        for artist in artists:
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing artist: {artist}")
            logger.info(f"{'='*60}")

            artist_stats = {
                'new_venues': 0,
                'existing_venues': 0,
                'new_shows': 0,
                'total_events': 0,
                'sources': []
            }

            # Try each enabled scraper
            for scraper_name, scraper in self.scrapers.items():
                if not enabled_scrapers.get(scraper_name, True):
                    logger.info(f"Skipping disabled scraper: {scraper_name}")
                    continue

                if scraper_name not in overall_stats['scrapers_used']:
                    overall_stats['scrapers_used'].append(scraper_name)

                logger.info(f"Using scraper: {scraper_name}")

                try:
                    # Scrape data
                    scraped_data = scraper.scrape_artist(artist)

                    if scraped_data:
                        logger.info(f"Found {len(scraped_data)} events from {scraper_name}")

                        # Process and add to database
                        stats = self.manager.process_scraped_data(artist, scraped_data)

                        # Update artist stats
                        artist_stats['new_venues'] += stats['new_venues']
                        artist_stats['existing_venues'] += stats['existing_venues']
                        artist_stats['new_shows'] += stats['new_shows']
                        artist_stats['total_events'] += stats['total_events']
                        artist_stats['sources'].append(scraper_name)

                    else:
                        logger.warning(f"No events found for {artist} on {scraper_name}")

                except Exception as e:
                    logger.error(f"Error scraping {artist} with {scraper_name}: {e}")
                    continue

            # Update overall stats
            overall_stats['artists_processed'] += 1
            overall_stats['total_new_venues'] += artist_stats['new_venues']
            overall_stats['total_new_shows'] += artist_stats['new_shows']
            overall_stats['total_events'] += artist_stats['total_events']
            overall_stats['artist_details'][artist] = artist_stats

            # Log artist summary
            logger.info(f"\nSummary for {artist}:")
            logger.info(f"  Events found: {artist_stats['total_events']}")
            logger.info(f"  New venues: {artist_stats['new_venues']}")
            logger.info(f"  New shows: {artist_stats['new_shows']}")

        # Final summary
        overall_stats['end_time'] = datetime.now().isoformat()
        overall_stats['database_stats'] = self.manager.get_summary()

        logger.info("\n" + "="*60)
        logger.info("SCRAPING RUN COMPLETE")
        logger.info("="*60)
        logger.info(f"Artists processed: {overall_stats['artists_processed']}")
        logger.info(f"Total events found: {overall_stats['total_events']}")
        logger.info(f"New venues added: {overall_stats['total_new_venues']}")
        logger.info(f"New shows added: {overall_stats['total_new_shows']}")
        logger.info(f"Total venues in database: {overall_stats['database_stats']['total_venues']}")
        logger.info("="*60)

        return overall_stats

    def export_venues(self, output_file: str = "venues_export.json"):
        """Export all venues to JSON file"""
        venues = self.db.get_all_venues()
        output_path = Path(output_file)

        with open(output_path, 'w') as f:
            json.dump(venues, f, indent=2, default=str)

        logger.info(f"Exported {len(venues)} venues to {output_file}")

    def close(self):
        """Clean up resources"""
        self.db.close()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Venue Scraper - Collect venue data from artist tour dates')
    parser.add_argument('--config', default='config.json', help='Path to configuration file')
    parser.add_argument('--database', default='venues.db', help='Path to SQLite database')
    parser.add_argument('--export', action='store_true', help='Export venues to JSON after scraping')
    parser.add_argument('--export-only', action='store_true', help='Only export venues, skip scraping')

    args = parser.parse_args()

    scraper = VenueScraper(config_path=args.config, db_path=args.database)

    try:
        if not args.export_only:
            # Run scraping
            results = scraper.scrape_all_artists()

            # Save results
            with open('last_run_results.json', 'w') as f:
                json.dump(results, f, indent=2, default=str)

        if args.export or args.export_only:
            scraper.export_venues()

    except KeyboardInterrupt:
        logger.info("\nScraping interrupted by user")
    except Exception as e:
        logger.error(f"Error during scraping: {e}", exc_info=True)
    finally:
        scraper.close()


if __name__ == "__main__":
    main()
