# 🌐 Web App Guide

## Beautiful Web Interface - No Coding Required!

Your venue scraper now has a gorgeous web interface that anyone can use!

---

## 🚀 Quick Start (3 Steps)

### Step 1: Install Streamlit
```bash
pip3 install streamlit pandas
```

### Step 2: Launch the Web App
```bash
cd ~/Downloads/venue-scraper  # or wherever your folder is
streamlit run webapp.py
```

### Step 3: Use it!
Your browser will automatically open to the app. If not, go to: **http://localhost:8501**

---

## ✨ Features

### 🎸 Artist Management (Sidebar)
- **Add artists** - Just type the name and click "Add Artist"
- **Remove artists** - Click the trash icon next to any artist
- **See your list** - All your tracked artists in one place

### ▶️ Run Scraper (Sidebar)
- Click the big **"Start Scraping"** button
- Watch live progress as it finds venues
- See results immediately when done

### 📊 Dashboard Tab
**Statistics Box:**
- Total venues in your database
- Total shows tracked
- Number of artists

**Last Scraping Results:**
- See what was found in the last run
- Per-artist breakdown
- New venues added

**Recently Added Venues:**
- See the 10 most recent venues
- Quick overview of what's new

### 📋 Venues Tab
**All Your Venues:**
- Beautiful searchable table
- Search by venue name, city, or country
- Sort by any column
- See source (which website it came from)
- See when it was added

**Chart:**
- Bar chart showing venues by country
- Quickly see geographic distribution

### 💾 Export (Sidebar)
- Click **"Export to CSV"**
- Download button appears
- Open in Excel, Google Sheets, or any spreadsheet app

---

## 📸 What It Looks Like

**The interface has:**
- 🎵 Big beautiful header
- 📊 Colorful statistics boxes
- 📋 Clean, professional tables
- 🔍 Search functionality
- 📈 Charts and visualizations
- 🎨 Modern, friendly design

---

## 🎯 Common Tasks

### Add Your First Artists
1. Look at the sidebar (left side)
2. Find "Add Artist" section
3. Type artist name (e.g., "Esperanza Spalding")
4. Click "➕ Add Artist"
5. Repeat for more artists

### Run Your First Scrape
1. Make sure you have artists added
2. Click **"▶️ Start Scraping"** in the sidebar
3. Wait for it to finish (you'll see progress)
4. Check the Dashboard tab for results!

### Search for a Venue
1. Go to the "Venues" tab
2. Use the search box at the top
3. Type city, venue name, or country
4. Table filters automatically!

### Export Your Data
1. Click **"📥 Export to CSV"** in sidebar
2. Click the "Download CSV" button that appears
3. Open the file in Excel or Google Sheets
4. Analyze, sort, filter as you like!

### Clear and Start Over
1. Close the web app (Ctrl+C in Terminal)
2. Delete `venues.db` file
3. Restart the app: `streamlit run webapp.py`
4. Fresh start!

---

## 🎨 What Makes It Beautiful?

- **No Code Required** - Point, click, done!
- **Live Updates** - See results in real-time
- **Color-Coded Stats** - Easy to understand at a glance
- **Responsive Design** - Works on any screen size
- **Search & Filter** - Find what you need instantly
- **Export Ready** - One-click CSV download
- **Professional Look** - Looks like a real product!

---

## 💡 Tips & Tricks

### For Best Results:
- Add artists one at a time and check the list
- Run the scraper when artists announce new tours
- Use the search to find specific cities or venues
- Export regularly to back up your data
- Keep the app running while scraping (don't close the browser)

### If Something Goes Wrong:
- **Scraper stuck?** - Refresh the page (F5)
- **No results?** - Check artist name spelling on songkick.com
- **App won't start?** - Make sure you installed streamlit: `pip3 install streamlit`

---

## 🌟 Sharing with Others

Want to share this with friends or team members?

### Option 1: Local Use (Easy)
1. Share the `venue-scraper` folder
2. They install: `pip3 install streamlit pandas requests beautifulsoup4`
3. They run: `streamlit run webapp.py`
4. Done!

### Option 2: Cloud Deployment (Advanced)
Deploy to Streamlit Cloud for free:
1. Push your code to GitHub
2. Go to share.streamlit.io
3. Connect your repo
4. Deploy!
5. Get a public URL anyone can access

---

## 🆚 Command Line vs Web App

**Use Command Line When:**
- Running automated/scheduled scrapes
- Scripting or integration with other tools
- You're comfortable with Terminal

**Use Web App When:**
- You want a beautiful interface
- Sharing with non-technical users
- Exploring and visualizing data
- Quick ad-hoc scraping

**Pro Tip:** Use both! Command line for automation, web app for viewing results!

---

## 🛠️ Troubleshooting

### App won't start
```bash
# Make sure you're in the right folder
cd ~/Downloads/venue-scraper

# Install dependencies
pip3 install streamlit pandas

# Try running again
streamlit run webapp.py
```

### Port already in use
```bash
# Use a different port
streamlit run webapp.py --server.port 8502
```

### Browser doesn't open automatically
Open manually: http://localhost:8501

### Changes not showing up
Click the "🔄 Refresh Data" button in the sidebar

---

## 🎉 You're Ready!

Launch it with:
```bash
streamlit run webapp.py
```

Enjoy your beautiful venue scraper! 🎵✨
