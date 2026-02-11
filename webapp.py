#!/usr/bin/env python3
"""
Venue Scraper Web App
Beautiful web interface for the venue scraper - no coding required!
"""

import streamlit as st
import pandas as pd
import json
from pathlib import Path
from datetime import datetime
import sqlite3
from database import VenueDatabase
from venue_manager import VenueManager
from scrapers.songkick_improved_scraper import SongkickImprovedScraper
import time

# Page configuration
st.set_page_config(
    page_title="Venue Scraper",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stat-box {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    .stat-number {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
    }
    .stat-label {
        font-size: 1rem;
        color: #666;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 15px;
        margin: 10px 0;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 5px;
        padding: 15px;
        margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'scraper_running' not in st.session_state:
    st.session_state.scraper_running = False
if 'last_run_stats' not in st.session_state:
    st.session_state.last_run_stats = None

def load_config():
    """Load configuration from file"""
    config_file = Path("config.json")
    if config_file.exists():
        with open(config_file, 'r') as f:
            return json.load(f)
    return {"artists": [], "scrapers_enabled": {"songkick": True}, "scraper_delays": {"songkick": 2.0}}

def save_config(config):
    """Save configuration to file"""
    with open("config.json", 'w') as f:
        json.dump(config, f, indent=2)

def get_database_stats():
    """Get statistics from the database"""
    try:
        db = VenueDatabase()
        total_venues = db.get_venues_count()
        recent_venues = db.get_recent_venues(10)

        # Get total shows
        conn = sqlite3.connect('venues.db')
        cursor = conn.cursor()
        total_shows = cursor.execute('SELECT COUNT(*) FROM shows').fetchone()[0]
        total_artists = cursor.execute('SELECT COUNT(DISTINCT name) FROM artists').fetchone()[0]
        conn.close()

        db.close()

        return {
            'total_venues': total_venues,
            'total_shows': total_shows,
            'total_artists': total_artists,
            'recent_venues': recent_venues
        }
    except:
        return {
            'total_venues': 0,
            'total_shows': 0,
            'total_artists': 0,
            'recent_venues': []
        }

def get_all_venues():
    """Get all venues as a DataFrame"""
    try:
        db = VenueDatabase()
        venues = db.get_all_venues()
        db.close()

        if venues:
            df = pd.DataFrame(venues)
            # Reorder and rename columns for better display
            display_cols = ['name', 'city', 'state', 'country', 'source', 'created_at']
            df = df[[col for col in display_cols if col in df.columns]]
            df.columns = ['Venue Name', 'City', 'State', 'Country', 'Source', 'Added On']
            return df
        return pd.DataFrame()
    except:
        return pd.DataFrame()

def run_scraper(artists):
    """Run the scraper for given artists"""
    progress_bar = st.progress(0)
    status_text = st.empty()

    db = VenueDatabase()
    manager = VenueManager(db)
    scraper = SongkickImprovedScraper()

    total_stats = {
        'total_events': 0,
        'total_new_venues': 0,
        'total_new_shows': 0,
        'artist_details': {}
    }

    for idx, artist in enumerate(artists):
        status_text.text(f"🎵 Scraping {artist}... ({idx + 1}/{len(artists)})")
        progress_bar.progress((idx) / len(artists))

        try:
            # Scrape data
            scraped_data = scraper.scrape_artist(artist)

            if scraped_data:
                # Process and add to database
                stats = manager.process_scraped_data(artist, scraped_data)

                total_stats['total_events'] += stats['total_events']
                total_stats['total_new_venues'] += stats['new_venues']
                total_stats['total_new_shows'] += stats['new_shows']
                total_stats['artist_details'][artist] = stats
            else:
                total_stats['artist_details'][artist] = {
                    'new_venues': 0,
                    'new_shows': 0,
                    'total_events': 0
                }
        except Exception as e:
            st.error(f"Error scraping {artist}: {str(e)}")
            total_stats['artist_details'][artist] = {
                'new_venues': 0,
                'new_shows': 0,
                'total_events': 0,
                'error': str(e)
            }

    progress_bar.progress(1.0)
    status_text.text("✅ Scraping complete!")
    db.close()

    return total_stats

# Main app layout
st.markdown('<h1 class="main-header">🎵 Venue Scraper</h1>', unsafe_allow_html=True)
st.markdown("### Discover and track concert venues from your favorite artists")

# Sidebar - Artist Management
with st.sidebar:
    st.header("🎸 Artist Management")

    config = load_config()
    current_artists = config.get('artists', [])

    # Add new artist
    st.subheader("Add Artist")
    new_artist = st.text_input("Artist name:", key="new_artist_input")
    if st.button("➕ Add Artist", use_container_width=True):
        if new_artist and new_artist not in current_artists:
            current_artists.append(new_artist)
            config['artists'] = current_artists
            save_config(config)
            st.success(f"Added {new_artist}!")
            st.rerun()
        elif new_artist in current_artists:
            st.warning("Artist already in list!")
        else:
            st.warning("Please enter an artist name")

    # Current artists list
    st.subheader("Current Artists")
    if current_artists:
        for artist in current_artists:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.text(f"🎤 {artist}")
            with col2:
                if st.button("🗑️", key=f"remove_{artist}", help=f"Remove {artist}"):
                    current_artists.remove(artist)
                    config['artists'] = current_artists
                    save_config(config)
                    st.rerun()
    else:
        st.info("No artists added yet. Add some above!")

    st.divider()

    # Run scraper button
    st.subheader("🚀 Run Scraper")
    if current_artists:
        if st.button("▶️ Start Scraping", type="primary", use_container_width=True, disabled=st.session_state.scraper_running):
            st.session_state.scraper_running = True
            with st.spinner("Scraping in progress..."):
                stats = run_scraper(current_artists)
                st.session_state.last_run_stats = stats
                st.session_state.scraper_running = False
                st.rerun()
    else:
        st.warning("Add artists first!")

    # Database actions
    st.divider()
    st.subheader("💾 Database")

    if st.button("🔄 Refresh Data", use_container_width=True):
        st.rerun()

    # Export button
    db_stats = get_database_stats()
    if db_stats['total_venues'] > 0:
        if st.button("📥 Export to CSV", use_container_width=True):
            df = get_all_venues()
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"venues_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )

# Main content area
tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📋 Venues", "ℹ️ About"])

with tab1:
    # Show last run stats if available
    if st.session_state.last_run_stats:
        st.markdown('<div class="success-box">', unsafe_allow_html=True)
        st.markdown("### ✅ Last Scraping Results")
        stats = st.session_state.last_run_stats

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Events Found", stats['total_events'])
        with col2:
            st.metric("New Venues", stats['total_new_venues'])
        with col3:
            st.metric("New Shows", stats['total_new_shows'])

        # Per-artist breakdown
        if stats['artist_details']:
            st.markdown("#### Per Artist:")
            for artist, artist_stats in stats['artist_details'].items():
                if 'error' in artist_stats:
                    st.error(f"**{artist}**: Error - {artist_stats['error']}")
                else:
                    st.write(f"**{artist}**: {artist_stats['total_events']} events, {artist_stats['new_venues']} new venues")

        st.markdown('</div>', unsafe_allow_html=True)
        st.divider()

    # Database statistics
    st.markdown("### 📈 Database Statistics")

    stats = get_database_stats()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown('<div class="stat-box">', unsafe_allow_html=True)
        st.markdown(f'<div class="stat-number">{stats["total_venues"]}</div>', unsafe_allow_html=True)
        st.markdown('<div class="stat-label">Total Venues</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="stat-box">', unsafe_allow_html=True)
        st.markdown(f'<div class="stat-number">{stats["total_shows"]}</div>', unsafe_allow_html=True)
        st.markdown('<div class="stat-label">Total Shows</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col3:
        st.markdown('<div class="stat-box">', unsafe_allow_html=True)
        st.markdown(f'<div class="stat-number">{stats["total_artists"]}</div>', unsafe_allow_html=True)
        st.markdown('<div class="stat-label">Artists Tracked</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Recent venues
    if stats['recent_venues']:
        st.markdown("### 🆕 Recently Added Venues")
        recent_df = pd.DataFrame(stats['recent_venues'])
        display_cols = ['name', 'city', 'country', 'created_at']
        recent_df = recent_df[[col for col in display_cols if col in recent_df.columns]]
        recent_df.columns = ['Venue Name', 'City', 'Country', 'Added On']
        st.dataframe(recent_df, use_container_width=True, hide_index=True)

with tab2:
    st.markdown("### 🏛️ All Venues")

    venues_df = get_all_venues()

    if not venues_df.empty:
        # Search box
        search = st.text_input("🔍 Search venues:", placeholder="Enter venue name, city, or country...")

        if search:
            mask = venues_df.apply(lambda row: row.astype(str).str.contains(search, case=False).any(), axis=1)
            filtered_df = venues_df[mask]
        else:
            filtered_df = venues_df

        # Display count
        st.caption(f"Showing {len(filtered_df)} of {len(venues_df)} venues")

        # Display table
        st.dataframe(
            filtered_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Venue Name": st.column_config.TextColumn("Venue Name", width="large"),
                "City": st.column_config.TextColumn("City", width="medium"),
                "State": st.column_config.TextColumn("State", width="small"),
                "Country": st.column_config.TextColumn("Country", width="medium"),
                "Source": st.column_config.TextColumn("Source", width="small"),
                "Added On": st.column_config.DatetimeColumn("Added On", format="MMM D, YYYY"),
            }
        )

        # Group by country
        st.markdown("### 🌍 Venues by Country")
        country_counts = venues_df['Country'].value_counts()
        st.bar_chart(country_counts)

    else:
        st.info("No venues in database yet. Add some artists and run the scraper!")

with tab3:
    st.markdown("### About Venue Scraper")

    st.markdown("""
    This web app automatically discovers and tracks concert venues from your favorite artists.

    **How it works:**
    1. Add your favorite artists in the sidebar
    2. Click "Start Scraping" to find their upcoming shows
    3. The app extracts venue information and stores it in a database
    4. View and export your venue collection anytime

    **Features:**
    - 🎵 Tracks venues from Songkick
    - 🔄 Smart deduplication (no duplicate venues)
    - 📊 Beautiful statistics and visualizations
    - 📥 Export to CSV for use in other apps
    - 🔍 Search and filter your venues

    **Tips:**
    - Run the scraper regularly to catch new tour announcements
    - Use the search feature to find specific venues
    - Export your data to analyze in Excel or Google Sheets

    **Built with:**
    - Python & Streamlit
    - SQLite database
    - Web scraping from Songkick
    """)

    st.divider()

    st.markdown("### 🛠️ Troubleshooting")

    with st.expander("No events found for my artist"):
        st.markdown("""
        This could mean:
        - The artist doesn't have upcoming shows scheduled
        - The artist name isn't spelled exactly as it appears on Songkick
        - Try searching for the artist on songkick.com to verify the exact name
        """)

    with st.expander("How do I clear the database?"):
        st.markdown("""
        To start fresh:
        1. Close this app
        2. Delete the `venues.db` file in the venue-scraper folder
        3. Restart the app
        """)

    with st.expander("Can I schedule automatic scraping?"):
        st.markdown("""
        Yes! Use the command-line version:
        ```bash
        python3 run_scheduler.py
        ```
        Edit that file to set your preferred schedule.
        """)

# Footer
st.divider()
st.markdown(
    '<div style="text-align: center; color: #666; padding: 20px;">Made with ❤️ for music lovers | Powered by Streamlit</div>',
    unsafe_allow_html=True
)
