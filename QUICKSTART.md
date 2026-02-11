# Quick Start Guide

## What You Have

A complete venue scraper that:
- ✅ Scrapes artist tour dates from Bandsintown and Songkick
- ✅ Builds a SQLite database of venues
- ✅ Automatically deduplicates venues (even with fuzzy name matching)
- ✅ Can run on a schedule automatically
- ✅ Exports data to JSON

## Immediate Next Steps

### 1. Install Dependencies (30 seconds)

```bash
pip install requests beautifulsoup4
```

Optional (for scheduling):
```bash
pip install schedule
```

### 2. Customize Your Artist List (1 minute)

Edit `config.json`:
```json
{
  "artists": [
    "Your Favorite Artist 1",
    "Your Favorite Artist 2",
    "Add more here..."
  ]
}
```

### 3. Run It! (2 minutes)

```bash
python venue_scraper.py
```

That's it! Your database will be created and populated with venues.

## What Just Happened?

The scraper:
1. Queried Bandsintown and Songkick for each artist
2. Extracted venue information from their tour dates
3. Created a SQLite database (`venues.db`)
4. Added all unique venues to the database
5. Logged everything to `venue_scraper.log`

## See Your Results

### View in Python
```python
from database import VenueDatabase

db = VenueDatabase()
venues = db.get_all_venues()

for venue in venues:
    print(f"{venue['name']} - {venue['city']}, {venue['country']}")
```

### Export to JSON
```bash
python venue_scraper.py --export
# Creates venues_export.json
```

### Query with SQLite
```bash
sqlite3 venues.db "SELECT name, city, country FROM venues LIMIT 10"
```

## Set Up Automation

### Quick Method (Python scheduler)

```bash
# Edit run_scheduler.py to set your schedule, then:
python run_scheduler.py
```

### Using Cron (Linux/Mac)

```bash
crontab -e
# Add: 0 2 * * * cd /path/to/venue-scraper && python venue_scraper.py
```

## Test First

Run the demo to see how it works:
```bash
python test_demo.py
```

This creates a test database with mock data so you can verify everything works.

## Common Commands

```bash
# Run scraper once
python venue_scraper.py

# Run and export to JSON
python venue_scraper.py --export

# Use custom config file
python venue_scraper.py --config my-artists.json

# Use custom database location
python venue_scraper.py --database /path/to/venues.db
```

## File Overview

| File | Purpose |
|------|---------|
| `venue_scraper.py` | Main script - run this |
| `config.json` | Your artist list |
| `database.py` | Database management |
| `venue_manager.py` | Deduplication logic |
| `scrapers/` | Bandsintown & Songkick scrapers |
| `run_scheduler.py` | Optional: automated scheduling |
| `test_demo.py` | Test with mock data |

## Getting Help

1. Check `venue_scraper.log` for detailed logs
2. Run `python test_demo.py` to verify setup
3. See `README.md` for full documentation

## What's Next?

- Add more artists to `config.json`
- Set up automated scheduling with `run_scheduler.py`
- Export your venue database to JSON
- Query the database with SQL
- Add additional scrapers (extend the system)

Happy venue hunting! 🎵
