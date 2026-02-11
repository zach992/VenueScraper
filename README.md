# Venue Scraper

An automated tool that scrapes artist tour dates from multiple sources (Bandsintown, Songkick) and builds a database of venues. The scraper automatically checks for new shows, extracts venue information, compares against your existing database, and adds new venues.

## Features

- **Multi-source scraping**: Pulls data from Bandsintown API and Songkick
- **Smart deduplication**: Uses fuzzy matching to avoid duplicate venues
- **SQLite database**: Stores venues, artists, and shows in a portable database
- **Automated scheduling**: Can run on a schedule via cron jobs
- **Detailed logging**: Tracks all scraping activities and errors
- **Export capabilities**: Export your venue database to JSON

## Quick Start

### 1. Installation

```bash
# Install Python dependencies
pip install -r requirements.txt
```

### 2. Configuration

Edit `config.json` to add your artists:

```json
{
  "artists": [
    "Your Artist Name 1",
    "Your Artist Name 2",
    "Your Artist Name 3"
  ],
  "scrapers_enabled": {
    "bandsintown": true,
    "songkick": true
  },
  "scraper_delays": {
    "bandsintown": 1.0,
    "songkick": 2.0
  }
}
```

### 3. Run the Scraper

```bash
# Run once
python venue_scraper.py

# Run and export venues to JSON
python venue_scraper.py --export

# Just export existing venues (no scraping)
python venue_scraper.py --export-only
```

## How It Works

1. **Reads configuration**: Loads your list of artists from `config.json`
2. **Scrapes tour dates**: Queries Bandsintown and Songkick for upcoming shows
3. **Extracts venues**: Pulls venue name, city, country, coordinates, etc.
4. **Deduplicates**: Compares new venues against existing database using fuzzy matching
5. **Updates database**: Adds new venues and shows to SQLite database
6. **Logs results**: Creates detailed logs in `venue_scraper.log`

## Database Structure

The scraper creates a SQLite database (`venues.db`) with three main tables:

### Venues
- Venue name, city, state, country
- Coordinates (latitude/longitude)
- Address and URL
- Source (bandsintown/songkick)
- Timestamps

### Artists
- Artist name
- Last checked timestamp

### Shows
- Links artists to venues
- Show date
- Show URL
- Source information

## Automated Scheduling

### Using Cron (Linux/Mac)

Run the scraper daily at 2 AM:

```bash
# Edit your crontab
crontab -e

# Add this line (replace /path/to with actual path):
0 2 * * * cd /path/to/venue-scraper && /usr/bin/python3 venue_scraper.py >> scraper_cron.log 2>&1
```

Run weekly (every Monday at 3 AM):

```bash
0 3 * * 1 cd /path/to/venue-scraper && /usr/bin/python3 venue_scraper.py >> scraper_cron.log 2>&1
```

### Using Task Scheduler (Windows)

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (daily, weekly, etc.)
4. Set action:
   - Program: `python`
   - Arguments: `venue_scraper.py`
   - Start in: `C:\path\to\venue-scraper`

### Using Python Script (Cross-platform)

Create a scheduler script `run_scheduler.py`:

```python
import schedule
import time
import subprocess

def run_scraper():
    print("Running venue scraper...")
    subprocess.run(["python", "venue_scraper.py"])

# Run daily at 2 AM
schedule.every().day.at("02:00").do(run_scraper)

# Or run every 6 hours
# schedule.every(6).hours.do(run_scraper)

print("Scheduler started. Press Ctrl+C to stop.")
while True:
    schedule.run_pending()
    time.sleep(60)
```

Install schedule library:
```bash
pip install schedule
```

Run the scheduler:
```bash
python run_scheduler.py
```

## Working with the Database

### View venues in Python

```python
from database import VenueDatabase

db = VenueDatabase()

# Get total count
print(f"Total venues: {db.get_venues_count()}")

# Get recent venues
recent = db.get_recent_venues(10)
for venue in recent:
    print(f"{venue['name']} - {venue['city']}, {venue['country']}")

db.close()
```

### Export to JSON

```bash
python venue_scraper.py --export-only
```

This creates `venues_export.json` with all venue data.

### Query with SQLite

```bash
sqlite3 venues.db "SELECT name, city, country FROM venues ORDER BY created_at DESC LIMIT 10"
```

## Advanced Configuration

### Customize Scraper Behavior

In `config.json`:

- **scrapers_enabled**: Turn individual scrapers on/off
- **scraper_delays**: Adjust delays between requests (be respectful to APIs)

### Database Location

```bash
python venue_scraper.py --database /path/to/custom.db
```

### Custom Config File

```bash
python venue_scraper.py --config /path/to/custom-config.json
```

## Logs

The scraper creates two log files:

- `venue_scraper.log`: Detailed logs of all operations
- `last_run_results.json`: JSON summary of the last scraping run

## Troubleshooting

### "No events found for artist"

- Check that artist name matches exactly how it appears on Bandsintown/Songkick
- Some artists may not have upcoming shows
- Try searching the artist on Bandsintown.com to verify the name

### Duplicate venues still appearing

- Adjust the similarity threshold in `venue_manager.py`
- Default is 0.85 (85% similarity required)

### Rate limiting errors

- Increase delays in `config.json`
- Reduce the number of artists processed in one run

## File Structure

```
venue-scraper/
├── venue_scraper.py          # Main orchestration script
├── database.py                # Database management
├── venue_manager.py           # Venue deduplication logic
├── config.json                # Artist configuration
├── requirements.txt           # Python dependencies
├── scrapers/
│   ├── __init__.py
│   ├── bandsintown_scraper.py
│   └── songkick_scraper.py
├── venues.db                  # SQLite database (created on first run)
├── venue_scraper.log          # Log file
└── last_run_results.json      # Latest run statistics
```

## Extending the Scraper

### Add a New Scraper

1. Create new scraper class in `scrapers/` directory
2. Implement these methods:
   - `scrape_artist(artist_name)` → returns list of (venue_data, show_data) tuples
   - `parse_venue_from_event(event)` → returns venue dictionary
   - `parse_show_from_event(event)` → returns show dictionary

3. Register in `venue_scraper.py`:

```python
from scrapers.your_scraper import YourScraper

self.scrapers = {
    'bandsintown': BandsintownScraper(),
    'songkick': SongkickScraper(),
    'your_scraper': YourScraper()
}
```

4. Add to config:

```json
{
  "scrapers_enabled": {
    "your_scraper": true
  }
}
```

## License

Free to use and modify for personal or commercial purposes.

## Support

For issues or questions, check the logs first. Most problems are related to:
- Artist name formatting
- Network/API availability
- Rate limiting

Enjoy building your venue database!
