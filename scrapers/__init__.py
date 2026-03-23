"""
Scrapers package for venue data collection
"""

from .songkick_improved_scraper import SongkickImprovedScraper
from .setlistfm_scraper import SetlistfmScraper

__all__ = ['SongkickImprovedScraper', 'SetlistfmScraper']
