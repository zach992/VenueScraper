# Complete Beginner's Guide to Running the Venue Scraper
## No Coding Experience Required!

This guide will walk you through everything step-by-step. Don't worry if you've never done anything like this before - just follow along!

---

## 🎯 What This Program Does

Think of this program like a robot assistant that:
1. Visits concert websites (like Bandsintown and Songkick)
2. Looks up your favorite artists
3. Writes down all the venues where they're playing
4. Saves them in a list on your computer
5. Makes sure it doesn't write down the same venue twice

Instead of you manually checking each website, the robot does it for you!

---

## 📋 Step 1: Make Sure You Have Python

Python is like the "engine" that makes this program run. It's free software that you need to install on your computer.

### Check if you already have Python:

**On Windows:**
1. Click the Windows Start button (bottom-left corner)
2. Type `cmd` and press Enter
3. A black window will appear - this is called the "Command Prompt"
4. Type this and press Enter:
   ```
   python --version
   ```
5. If you see something like "Python 3.11.5", you're good! Skip to Step 2.
6. If you see an error, you need to install Python (see below)

**On Mac:**
1. Press `Command + Space` to open Spotlight
2. Type `terminal` and press Enter
3. A white or black window will appear - this is the "Terminal"
4. Type this and press Enter:
   ```
   python3 --version
   ```
5. If you see something like "Python 3.11.5", you're good! Skip to Step 2.
6. If you see an error, you need to install Python (see below)

### If you need to install Python:

1. Go to [python.org/downloads](https://python.org/downloads)
2. Click the big yellow "Download Python" button
3. Run the installer file that downloads
4. **IMPORTANT:** Check the box that says "Add Python to PATH" before clicking Install
5. Click "Install Now"
6. Wait for it to finish
7. Restart your computer
8. Try the version check again

---

## 📋 Step 2: Find Your Venue Scraper Folder

You need to find where you saved the "venue-scraper" folder on your computer.

1. Open File Explorer (Windows) or Finder (Mac)
2. Find the `venue-scraper` folder
3. **Write down the full path** - for example:
   - Windows: `C:\Users\YourName\Downloads\venue-scraper`
   - Mac: `/Users/YourName/Downloads/venue-scraper`

**Tip:** On Windows, you can click the address bar at the top of File Explorer and copy the path. On Mac, right-click the folder and hold Option to see "Copy as Pathname".

---

## 📋 Step 3: Open Terminal/Command Prompt in Your Folder

This is where we'll type commands to run the program.

**On Windows:**
1. Open File Explorer
2. Navigate to your `venue-scraper` folder
3. Click on the address bar at the top (where it shows the folder path)
4. Type `cmd` and press Enter
5. A black Command Prompt window will open, already in your folder!

**On Mac:**
1. Open your `venue-scraper` folder in Finder
2. Right-click (or Control+click) on the folder
3. While holding the Option key, you'll see "Copy 'venue-scraper' as Pathname"
4. Open Terminal (use Spotlight - Command+Space, then type "terminal")
5. Type `cd ` (that's "cd" followed by a space)
6. Paste the path you copied (Command+V)
7. Press Enter

You should now see something like `C:\Users\YourName\Downloads\venue-scraper>` or `~/Downloads/venue-scraper $`

---

## 📋 Step 4: Install the Required Helper Programs

The scraper needs two "helper programs" called `requests` and `beautifulsoup4`. These help it talk to websites and read the information.

**Type this command and press Enter:**

**On Windows:**
```
pip install requests beautifulsoup4
```

**On Mac:**
```
pip3 install requests beautifulsoup4
```

### What you'll see:
- Lots of text scrolling by (this is normal!)
- Words like "Downloading..." and "Installing..."
- After 10-30 seconds, it will finish
- You'll see "Successfully installed..." - that means it worked!

### If you get an error:
- Make sure you're in the right folder
- Make sure you have internet connection
- Try running Terminal/Command Prompt as Administrator (Windows) or with `sudo` (Mac)

---

## 📋 Step 5: Tell the Program Which Artists to Track

You need to edit a file called `config.json` to add your favorite artists.

### The Easy Way - Using Notepad/TextEdit:

**On Windows:**
1. In your `venue-scraper` folder, find the file named `config.json`
2. Right-click it
3. Choose "Open with" → "Notepad"

**On Mac:**
1. In your `venue-scraper` folder, find `config.json`
2. Right-click it
3. Choose "Open With" → "TextEdit"

### What you'll see:
```json
{
  "artists": [
    "Radiohead",
    "The National",
    "Arcade Fire",
    "LCD Soundsystem",
    "Bon Iver"
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

### How to edit it:

1. Find the part that says `"artists": [`
2. Between the `[` and `]`, you'll see a list of artist names
3. Replace them with YOUR favorite artists
4. **IMPORTANT RULES:**
   - Each artist name must be in "quotes"
   - Put a comma after each artist (except the last one)
   - Spell the artist names exactly as they appear on concert sites

### Example:
```json
{
  "artists": [
    "Taylor Swift",
    "Beyoncé",
    "Harry Styles",
    "Billie Eilish"
  ],
```

5. Save the file (File → Save, or Ctrl+S / Command+S)
6. Close the editor

---

## 📋 Step 6: Run the Venue Scraper!

Now for the exciting part - actually running the program!

### In your Terminal/Command Prompt window, type:

**On Windows:**
```
python venue_scraper.py
```

**On Mac:**
```
python3 venue_scraper.py
```

Then press Enter!

### What you'll see:

The program will start running and you'll see messages like:
```
============================================================
Starting venue scraping run
============================================================
Artists to scrape: 4
Artists: Taylor Swift, Beyoncé, Harry Styles, Billie Eilish

============================================================
Processing artist: Taylor Swift
============================================================
Using scraper: bandsintown
Found 15 events from bandsintown
...
```

This will take a few minutes depending on how many artists you have.

### When it's done:

You'll see a summary like:
```
============================================================
SCRAPING RUN COMPLETE
============================================================
Artists processed: 4
Total events found: 58
New venues added: 42
Total venues in database: 42
============================================================
```

Congratulations! 🎉 You just ran the venue scraper!

---

## 📋 Step 7: See Your Results

The program created a file called `venues.db` - this is your database of venues!

### Option 1: Export to a readable file

In your Terminal/Command Prompt, type:

**On Windows:**
```
python venue_scraper.py --export
```

**On Mac:**
```
python3 venue_scraper.py --export
```

This creates a file called `venues_export.json` that you can open with Notepad/TextEdit to see all your venues!

### Option 2: Run the test demo

Want to see how it works with fake data first? Type:

**On Windows:**
```
python test_demo.py
```

**On Mac:**
```
python3 test_demo.py
```

This shows you exactly what the program does, step by step!

---

## 🔄 Running It Again

Every time you want to check for new shows and venues:

1. Open Terminal/Command Prompt in your `venue-scraper` folder (like in Step 3)
2. Run the command from Step 6
3. The program will find new shows and add new venues to your database!

The program is smart - it won't add the same venue twice, even if the spelling is slightly different!

---

## ⏰ Running It Automatically (Advanced)

Once you're comfortable running it manually, you can set it up to run automatically every day. This is more advanced, but here's the simple version:

**The easiest way:**
1. Open `run_scheduler.py` in Notepad/TextEdit
2. Find the line that says `schedule.every().day.at("02:00").do(run_scraper)`
3. Change "02:00" to whatever time you want (use 24-hour format, like "14:00" for 2 PM)
4. Save and close
5. In Terminal/Command Prompt, run:
   - Windows: `python run_scheduler.py`
   - Mac: `python3 run_scheduler.py`
6. Leave this window open - the program will now run automatically at your chosen time!

---

## ❓ Common Questions

**Q: How do I know if it's working?**
A: Look for the summary at the end showing "New venues added". Also check the `venue_scraper.log` file - it has every detail!

**Q: It says "No events found" for my artist. Why?**
A: Make sure you spelled the artist name exactly right. Try searching for them on bandsintown.com to see the correct spelling.

**Q: Can I run this every day?**
A: Yes! Just run the command again. It will only add NEW venues, not duplicates.

**Q: Where is my database saved?**
A: In the same `venue-scraper` folder, in a file called `venues.db`

**Q: Can I see the venues in a normal format?**
A: Yes! Use the `--export` command (from Step 7) to create a readable JSON file.

**Q: I got an error. What do I do?**
A: Check the `venue_scraper.log` file in your folder. It will tell you exactly what went wrong.

---

## 🎉 You Did It!

You just:
- ✅ Set up Python
- ✅ Installed helper programs
- ✅ Edited a configuration file
- ✅ Ran a real program
- ✅ Created a database

You're now running automated code! That's awesome! 🌟

If you get stuck, check the `README.md` file for more detailed explanations, or look at your `venue_scraper.log` file to see what happened.

Happy venue tracking! 🎵
