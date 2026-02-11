#!/usr/bin/env python3
"""
Simple scheduler for venue scraper
Runs the scraper on a configurable schedule
"""

import schedule
import time
import subprocess
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def run_scraper():
    """Execute the venue scraper"""
    logger.info("="*60)
    logger.info(f"Starting scheduled scraper run at {datetime.now()}")
    logger.info("="*60)

    try:
        result = subprocess.run(
            ["python", "venue_scraper.py"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            logger.info("Scraper completed successfully")
        else:
            logger.error(f"Scraper failed with exit code {result.returncode}")
            logger.error(f"Error output: {result.stderr}")

    except Exception as e:
        logger.error(f"Error running scraper: {e}")

    logger.info("Scheduled run complete\n")


def main():
    """Main scheduler loop"""
    # Configure your schedule here:

    # Option 1: Run daily at specific time
    schedule.every().day.at("02:00").do(run_scraper)

    # Option 2: Run every N hours
    # schedule.every(6).hours.do(run_scraper)

    # Option 3: Run weekly
    # schedule.every().monday.at("03:00").do(run_scraper)

    # Option 4: Run every day at multiple times
    # schedule.every().day.at("09:00").do(run_scraper)
    # schedule.every().day.at("21:00").do(run_scraper)

    logger.info("Venue Scraper Scheduler started")
    logger.info("Press Ctrl+C to stop")
    logger.info("\nScheduled jobs:")
    for job in schedule.get_jobs():
        logger.info(f"  - {job}")

    # Optional: Run once immediately on startup
    # run_scraper()

    # Main loop
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

    except KeyboardInterrupt:
        logger.info("\nScheduler stopped by user")


if __name__ == "__main__":
    main()
