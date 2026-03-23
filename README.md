# Venue Scraper

A tool for booking agents to discover venues where similar artists play. Add artists, scrape their tour dates from Songkick, and build a database of venues to target.

## Quick Start

```bash
pip install -r requirements.txt
streamlit run webapp.py
```

This opens a web UI where you can:
1. Add artists in the sidebar
2. Click "Run Scraper" to find their venues
3. Filter, search, and browse venues
4. Set venue status (New / Interested / Contacted / Not a Fit)
5. Add notes (contact info, capacity, etc.)
6. Export to CSV

## Command Line

```bash
# Run scraper directly
python3 venue_scraper.py

# Export venues to JSON
python3 venue_scraper.py --export
```

## How It Works

1. Scrapes artist tour dates from Songkick
2. Extracts venue name, city, state, country
3. Deduplicates using fuzzy matching (catches "Amphitheatre" vs "Amphitheater")
4. Stores in SQLite database with status tracking

## Files

```
venue_scraper.py              # Main scraper orchestration
webapp.py                     # Streamlit web UI
database.py                   # SQLite database (venues, artists, shows)
venue_manager.py              # Deduplication logic
config.json                   # Artist list and settings
scrapers/
  songkick_improved_scraper.py  # Songkick web scraper
```

## Adding a New Scraper

Create a class in `scrapers/` with a `scrape_artist(name)` method that returns `[(venue_data, show_data), ...]` tuples, then register it in `venue_scraper.py`.
