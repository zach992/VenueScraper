# 🚀 Deployment Guide - Share Your Venue Scraper with the World!

## Option 1: Streamlit Community Cloud (FREE & EASY!) ⭐

**Perfect for:** Sharing with friends, team, or the public
**Cost:** FREE forever
**URL:** You get a public link like `venue-scraper.streamlit.app`
**Time:** 15-20 minutes

### What You'll Need
- GitHub account (free)
- Your venue-scraper folder
- 15 minutes

---

## 📋 Step-by-Step Instructions

### Step 1: Create a GitHub Account (5 minutes)

**If you don't have GitHub:**
1. Go to [github.com](https://github.com)
2. Click "Sign up"
3. Enter your email, create a password
4. Choose a username
5. Verify your email

**If you already have GitHub:**
Skip to Step 2! ✅

---

### Step 2: Install Git (One-time setup)

**On Mac:**
```bash
# Check if you already have it
git --version

# If not installed, install with Homebrew
brew install git

# Or download from: https://git-scm.com/download/mac
```

**Configure Git (first time only):**
```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

---

### Step 3: Create a GitHub Repository

1. Go to [github.com](https://github.com) and log in
2. Click the **"+"** in top-right corner
3. Select **"New repository"**
4. Fill in:
   - **Repository name:** `venue-scraper` (or whatever you want)
   - **Description:** "Web app for discovering concert venues"
   - **Public** (must be public for free Streamlit hosting)
   - ✅ Check "Add a README file"
5. Click **"Create repository"**

**Copy the repository URL** - you'll need it! It looks like:
```
https://github.com/YOUR-USERNAME/venue-scraper.git
```

---

### Step 4: Prepare Your Files

**Create a `.gitignore` file** (tells Git which files to ignore):

In your `venue-scraper` folder, create a file called `.gitignore`:

```bash
cd ~/Downloads/venue-scraper  # or wherever your folder is
nano .gitignore
```

Paste this content:
```
# Database and data files
*.db
*.sqlite
*.sqlite3
venues_export.json
last_run_results.json
venue_scraper.log
scheduler.log

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv

# macOS
.DS_Store

# IDE
.vscode/
.idea/
*.swp
*.swo
```

Save: Press `Ctrl+X`, then `Y`, then `Enter`

---

### Step 5: Push Your Code to GitHub

**In Terminal, in your venue-scraper folder:**

```bash
# Initialize Git
git init

# Add all files
git add .

# Create your first commit
git commit -m "Initial commit - venue scraper web app"

# Connect to your GitHub repo (replace with YOUR URL from Step 3)
git remote add origin https://github.com/YOUR-USERNAME/venue-scraper.git

# Push to GitHub
git branch -M main
git push -u origin main
```

**Enter your GitHub username and password when prompted.**

**Note:** If you get an authentication error, you need to use a Personal Access Token instead of your password:
1. Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token
3. Give it `repo` permissions
4. Copy the token
5. Use it as your password when pushing

---

### Step 6: Deploy to Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click **"Sign in with GitHub"**
3. Authorize Streamlit to access your GitHub
4. Click **"New app"**
5. Fill in the deployment form:
   - **Repository:** Select your `venue-scraper` repo
   - **Branch:** `main`
   - **Main file path:** `webapp.py`
6. Click **"Deploy!"**

**Wait 2-3 minutes** while Streamlit builds and deploys your app!

---

### Step 7: Share Your App! 🎉

Once deployed, you'll get a URL like:
```
https://YOUR-USERNAME-venue-scraper.streamlit.app
```

**You can now share this link with anyone!** They can:
- Add their own artists
- Run the scraper
- View venues
- Export data
- All without installing anything!

---

## 🔄 Updating Your Deployed App

When you make changes to your code:

```bash
cd ~/Downloads/venue-scraper

# Add your changes
git add .

# Commit with a message
git commit -m "Updated scraper or fixed bug"

# Push to GitHub
git push
```

**Streamlit automatically redeploys** when you push to GitHub!
(Takes 2-3 minutes)

---

## 🎨 Customizing Your Deployment

### Custom Domain (Optional)
You can add a custom domain in Streamlit Cloud settings:
- Go to your app dashboard
- Click "Settings"
- Add custom domain

### Make App Private (Paid)
Free tier = public apps
Streamlit for Teams ($250/month) = private apps with authentication

### Add App Secrets (For API Keys)
If you add API keys later:
1. Go to app settings in Streamlit Cloud
2. Click "Secrets"
3. Add your secrets in TOML format
4. Access in code with: `st.secrets["api_key"]`

---

## 🛡️ Important Notes

### Database Persistence
⚠️ **Important:** The database (venues.db) is **NOT persistent** on Streamlit Cloud!

When the app restarts (happens automatically), the database resets.

**Solutions:**

**Option A: Accept it (simplest)**
- Users can export to CSV regularly
- Good for demo/exploration use

**Option B: Use Cloud Database (advanced)**
- Set up PostgreSQL on Heroku (free tier)
- Or use SQLite with Streamlit's file uploader
- Modify code to use cloud storage

**Option C: Local Only**
- Keep database on your computer
- Only deploy the interface
- Run scraper locally, upload results

### Rate Limiting
Songkick might block the scraper if too many people use it simultaneously.

**Solutions:**
- Add delays (already implemented)
- Tell users to use it during off-peak hours
- Add a queue system (advanced)

### Costs
- **Streamlit Community Cloud:** FREE
- **Custom domain:** ~$10-15/year (optional)
- **Private apps:** $250/month (optional)

---

## Option 2: Run on Your Own Server

If you have a server (VPS, AWS, etc.):

```bash
# Install dependencies
pip3 install -r requirements.txt

# Run with custom port and host
streamlit run webapp.py --server.port=8080 --server.address=0.0.0.0

# Keep it running with screen or tmux
screen -S streamlit
streamlit run webapp.py
# Ctrl+A, D to detach
```

**Access at:** `http://YOUR-SERVER-IP:8080`

### Make it permanent with systemd:

Create `/etc/systemd/system/venue-scraper.service`:
```ini
[Unit]
Description=Venue Scraper Web App
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/venue-scraper
ExecStart=/usr/bin/streamlit run webapp.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable venue-scraper
sudo systemctl start venue-scraper
```

---

## Option 3: Docker (Advanced)

Create `Dockerfile`:
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "webapp.py", "--server.address=0.0.0.0"]
```

Build and run:
```bash
docker build -t venue-scraper .
docker run -p 8501:8501 venue-scraper
```

Deploy to:
- Google Cloud Run
- AWS ECS
- DigitalOcean App Platform

---

## 🎯 Which Option Should You Choose?

### Choose Streamlit Cloud if:
✅ You want it to be FREE
✅ You want the easiest setup
✅ You're okay with public access
✅ You don't need persistent database
✅ You want automatic updates

### Choose Your Own Server if:
✅ You need private access
✅ You want database persistence
✅ You have technical knowledge
✅ You have a server already

### Choose Docker if:
✅ You're deploying to cloud platforms
✅ You want containerization
✅ You're technical/developer
✅ You need scalability

---

## 📱 Mobile Access

Once deployed, the Streamlit app works great on mobile!
- Responsive design
- Touch-friendly
- Works on phones and tablets

---

## 🆘 Troubleshooting Deployment

### "Build failed" on Streamlit Cloud
- Check your `requirements.txt` is correct
- Make sure all imports in `webapp.py` are installed
- Look at the build logs for specific errors

### "Module not found" error
Add the missing module to `requirements.txt`

### Database not persisting
This is normal on Streamlit Cloud - see "Database Persistence" section above

### App is slow
- Free tier has limited resources
- Consider upgrading to paid tier
- Or optimize your scraper code

### Can't push to GitHub
- Make sure you're using a Personal Access Token, not password
- Check your Git remote: `git remote -v`
- Try: `git push origin main --force` (careful with --force!)

---

## 🎉 You're Live!

Once deployed, your venue scraper is:
- ✅ Accessible from anywhere
- ✅ Mobile-friendly
- ✅ No installation required for users
- ✅ Automatically updated when you push changes
- ✅ Professional-looking
- ✅ Free to host!

**Share your URL and let people discover venues!** 🎵

---

## 📚 Resources

- [Streamlit Cloud Documentation](https://docs.streamlit.io/streamlit-community-cloud)
- [GitHub Documentation](https://docs.github.com)
- [Git Tutorial](https://git-scm.com/docs/gittutorial)
- [Streamlit Forums](https://discuss.streamlit.io)

---

**Need help?** Check the Streamlit Community forums or GitHub issues!
