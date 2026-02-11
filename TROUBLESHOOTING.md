# Troubleshooting Guide

## Issue: "403 Forbidden" Error from Bandsintown

### What You Saw
```
ERROR: Error fetching events for Esperanza Spalding: 403 Client Error: Forbidden for url: https://rest.bandsintown.com/artists/...
```

### What This Means
Bandsintown blocked the API request. The "403 Forbidden" error means their server refused to give us data. This happens because:
- Bandsintown changed their API requirements
- They now require authentication or a registered API key
- They're blocking simple app_ids like "venue_scraper"

### The Fix
**I've already fixed this for you!** The scraper now uses a **web scraper** instead of the API. This means:
- Instead of using Bandsintown's API, it reads their website directly
- Just like a web browser would
- No API key needed!

### What Changed
The program now uses `BandsintownWebScraper` instead of `BandsintownScraper`. This:
- Visits the artist's Bandsintown page (like `bandsintown.com/a/radiohead`)
- Reads the HTML code of the page
- Extracts venue information from the page
- Works even when the API is blocked!

---

## Issue: LibreSSL Warning

### What You Saw
```
NotOpenSSLWarning: urllib3 v2 only supports OpenSSL 1.1.1+, currently the 'ssl' module is compiled with 'LibreSSL 2.8.3'
```

### What This Means
This is just a **warning** (not an error). Your Mac has LibreSSL instead of OpenSSL. It's totally fine and won't break anything!

### Should You Fix It?
**No, you can ignore it.** The program works fine with this warning. If it bothers you, you can:

**Option 1: Hide the warning (easiest)**
Add this to the top of `venue_scraper.py`, right after the imports:
```python
import warnings
warnings.filterwarnings('ignore', category=Warning)
```

**Option 2: Upgrade urllib3 (more complex)**
```bash
pip3 install --upgrade urllib3
```

---

## Issue: Songkick Finding 0 Events

### What You Saw
```
INFO: Found artist via search: https://www.songkick.com/artists/560672-esperanza-spalding
INFO: Fetching events from: https://www.songkick.com/artists/560672-esperanza-spalding/calendar
INFO: Found 0 events
```

### What This Could Mean
**Three possibilities:**

1. **The artist truly has no upcoming shows scheduled**
   - Check manually: Visit the Songkick URL shown in the log
   - If you see "No upcoming events", then the artist just doesn't have shows right now

2. **Songkick changed their website layout**
   - Their HTML structure changed and our scraper can't find the events anymore
   - This is common with web scraping

3. **Songkick is blocking automated scraping**
   - They might have bot detection

### How to Check
1. Copy the URL from the log (example: `https://www.songkick.com/artists/560672-esperanza-spalding`)
2. Open it in your web browser
3. Do you see upcoming events on the page?
   - **NO**: The artist really has no shows scheduled (not a bug!)
   - **YES**: The scraper needs an update (see below)

### If The Scraper Needs Updating
The Songkick website layout may have changed. Solutions:

**Option 1: Try Different Artists**
Some artists tour more than others. Try artists you KNOW have upcoming shows:
```json
{
  "artists": [
    "Taylor Swift",
    "Ed Sheeran",
    "Coldplay"
  ]
}
```

**Option 2: Disable Songkick Temporarily**
Edit `config.json`:
```json
{
  "scrapers_enabled": {
    "bandsintown": true,
    "songkick": false
  }
}
```

**Option 3: Debug the HTML Structure**
I can help you update the Songkick scraper if you send me:
1. The artist URL that should have events
2. Confirmation that you see events when you visit it in your browser

---

## Testing Your Fixed Scraper

### Try the Test Demo First
```bash
python3 test_demo.py
```

This uses **fake data** to verify the database and deduplication work correctly. Should take 5 seconds and show:
- ✓ 3 new venues added
- ✓ Deduplication working
- ✓ Fuzzy matching working

### Try Real Artists With Lots of Shows
Update your `config.json` with popular artists who tour frequently:

```json
{
  "artists": [
    "Taylor Swift",
    "Metallica",
    "Dead & Company",
    "Phish"
  ]
}
```

Then run:
```bash
python3 venue_scraper.py
```

These artists typically have many upcoming shows, so you should see results like:
```
New venues added: 25
Total venues in database: 25
```

---

## Common Debugging Steps

### 1. Check Your Internet Connection
```bash
ping bandsintown.com
```

### 2. Check if the Websites Are Up
- Visit [bandsintown.com](https://www.bandsintown.com) in your browser
- Visit [songkick.com](https://www.songkick.com) in your browser
- If they're down, the scraper won't work

### 3. Look at the Log File
Open `venue_scraper.log` in a text editor. Look for lines that say:
- `ERROR` - something broke
- `WARNING` - something's odd but not broken
- `INFO` - just information

### 4. Verify Artist Names
Artist names must match EXACTLY how they appear on the websites:
- ❌ `Tigran Hamasayan` (typo)
- ✅ `Tigran Hamasyan` (correct)

Visit Bandsintown or Songkick and search for your artist to get the exact spelling.

### 5. Try One Artist at a Time
Narrow down problems by testing with just one artist:
```json
{
  "artists": ["Taylor Swift"]
}
```

---

## Still Having Issues?

### Gather This Info:
1. What error message you see
2. What's in `venue_scraper.log` (last 20 lines)
3. Which artists you're trying to scrape
4. Whether those artists have shows when you check manually

### Quick Fixes to Try:
1. **Update your libraries:**
   ```bash
   pip3 install --upgrade requests beautifulsoup4
   ```

2. **Delete and recreate the database:**
   ```bash
   rm venues.db
   python3 venue_scraper.py
   ```

3. **Try the web scraper directly:**
   ```bash
   cd scrapers
   python3 bandsintown_web_scraper.py
   ```

---

## What Changed in Your Scraper (Summary)

✅ **Fixed:** Bandsintown now uses web scraping instead of blocked API
✅ **Added:** New `bandsintown_web_scraper.py` file
✅ **Updated:** Main script now uses the web scraper
⚠️ **Note:** LibreSSL warning is harmless
⚠️ **Note:** Songkick may show 0 events if artists have no upcoming shows

The scraper should now work! Try it with popular touring artists to verify.
