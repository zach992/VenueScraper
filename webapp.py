#!/usr/bin/env python3
"""
Venue Scraper Web App
Web interface for the venue scraper - built for booking agents
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

# =============================================================================
# CUSTOM CSS
# =============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&family=Instrument+Serif:ital@0;1&display=swap');

    /* ── Global ────────────────────────────────────── */
    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif !important;
    }

    /* ── Hide Streamlit chrome ─────────────────────── */
    #MainMenu, footer, header { visibility: hidden; }
    .block-container { padding-top: 2rem; padding-bottom: 1rem; }

    /* ── App title ─────────────────────────────────── */
    .app-title {
        font-family: 'Instrument Serif', serif;
        font-size: 2.6rem;
        font-weight: 400;
        color: #e8e8e8;
        letter-spacing: -0.5px;
        margin: 0;
        line-height: 1.1;
    }
    .app-subtitle {
        font-family: 'DM Sans', sans-serif;
        font-size: 0.85rem;
        color: #888;
        font-weight: 400;
        margin-top: 0.25rem;
        letter-spacing: 0.3px;
    }

    /* ── Stat cards ─────────────────────────────────── */
    .stat-card {
        background: #242424;
        border: 1px solid #333;
        border-radius: 8px;
        padding: 1.1rem 1.2rem;
        text-align: center;
    }
    .stat-card:hover { border-color: #d4a04a44; }
    .stat-value {
        font-family: 'DM Sans', sans-serif;
        font-size: 2rem;
        font-weight: 700;
        color: #d4a04a;
        line-height: 1.2;
    }
    .stat-label {
        font-family: 'DM Sans', sans-serif;
        font-size: 0.75rem;
        color: #888;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        font-weight: 500;
        margin-top: 0.2rem;
    }

    /* ── Sidebar ───────────────────────────────────── */
    section[data-testid="stSidebar"] {
        background: #1e1e1e;
        border-right: 1px solid #2a2a2a;
    }
    section[data-testid="stSidebar"] .stMarkdown h2 {
        font-family: 'DM Sans', sans-serif;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 2px;
        color: #888;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }

    /* Artist list container */
    .artist-list {
        max-height: 280px;
        overflow-y: auto;
        padding-right: 4px;
        margin-bottom: 0.5rem;
    }
    .artist-list::-webkit-scrollbar { width: 4px; }
    .artist-list::-webkit-scrollbar-track { background: transparent; }
    .artist-list::-webkit-scrollbar-thumb { background: #444; border-radius: 4px; }
    .artist-item {
        font-family: 'DM Sans', sans-serif;
        font-size: 0.85rem;
        color: #ccc;
        padding: 0.3rem 0;
        border-bottom: 1px solid #2a2a2a;
    }
    .artist-count {
        font-family: 'DM Sans', sans-serif;
        font-size: 0.75rem;
        color: #d4a04a;
        font-weight: 600;
        letter-spacing: 0.5px;
        margin-bottom: 0.3rem;
    }

    /* ── Buttons ────────────────────────────────────── */
    .stButton > button[kind="primary"] {
        background: #d4a04a !important;
        color: #1a1a1a !important;
        font-weight: 600 !important;
        border: none !important;
        font-family: 'DM Sans', sans-serif !important;
        letter-spacing: 0.5px;
    }
    .stButton > button[kind="primary"]:hover {
        background: #e0b05e !important;
    }
    .stDownloadButton > button {
        background: transparent !important;
        border: 1px solid #444 !important;
        color: #ccc !important;
        font-family: 'DM Sans', sans-serif !important;
    }
    .stDownloadButton > button:hover {
        border-color: #d4a04a !important;
        color: #d4a04a !important;
    }

    /* ── Filters ────────────────────────────────────── */
    .filter-label {
        font-family: 'DM Sans', sans-serif;
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color: #666;
        font-weight: 600;
        margin-bottom: 0.2rem;
    }

    /* ── Last run banner ───────────────────────────── */
    .run-banner {
        background: #2a2a1e;
        border: 1px solid #3d3820;
        border-radius: 6px;
        padding: 0.6rem 1rem;
        margin-bottom: 1rem;
        font-family: 'DM Sans', sans-serif;
        font-size: 0.82rem;
        color: #d4a04a;
    }

    /* ── Data editor refinements ────────────────────── */
    [data-testid="stDataFrame"] {
        border: 1px solid #333;
        border-radius: 8px;
    }

    /* ── Remove artist buttons ──────────────────────── */
    section[data-testid="stSidebar"] [data-testid="stExpander"] .stButton > button {
        background: transparent !important;
        border: none !important;
        color: #555 !important;
        font-size: 0.85rem !important;
        padding: 0.2rem 0.4rem !important;
        min-height: 0 !important;
        line-height: 1 !important;
    }
    section[data-testid="stSidebar"] [data-testid="stExpander"] .stButton > button:hover {
        color: #e85555 !important;
    }

    /* ── Divider ───────────────────────────────────── */
    hr { border-color: #2a2a2a !important; }

    /* ── Toast-like result count ────────────────────── */
    .venue-count {
        font-family: 'DM Sans', sans-serif;
        font-size: 0.78rem;
        color: #666;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# STATUS OPTIONS
# =============================================================================
VENUE_STATUSES = ["", "Interested", "Contacted", "Not a Fit"]

# =============================================================================
# SESSION STATE
# =============================================================================
if 'scraper_running' not in st.session_state:
    st.session_state.scraper_running = False
if 'last_run_stats' not in st.session_state:
    st.session_state.last_run_stats = None


# =============================================================================
# DATA FUNCTIONS
# =============================================================================
def load_config():
    config_file = Path("config.json")
    if config_file.exists():
        with open(config_file, 'r') as f:
            return json.load(f)
    return {"artists": [], "scrapers_enabled": {"songkick": True, "setlistfm": True}}


def save_config(config):
    with open("config.json", 'w') as f:
        json.dump(config, f, indent=2)


def validate_artist(artist_name):
    results = []
    config = load_config()
    enabled = config.get('scrapers_enabled', {})
    if enabled.get('songkick', True):
        scraper = SongkickImprovedScraper()
        url = scraper.search_artist(artist_name)
        results.append({'source': 'Songkick', 'found': url is not None})
    if enabled.get('setlistfm', False):
        from scrapers.setlistfm_scraper import SetlistfmScraper
        scraper = SetlistfmScraper()
        url = scraper.search_artist(artist_name)
        results.append({'source': 'Setlist.fm', 'found': url is not None})
    return results


def get_enabled_scrapers():
    config = load_config()
    enabled = config.get('scrapers_enabled', {})
    scrapers = {}
    if enabled.get('songkick', True):
        scrapers['songkick'] = SongkickImprovedScraper()
    if enabled.get('setlistfm', False):
        from scrapers.setlistfm_scraper import SetlistfmScraper
        scrapers['setlistfm'] = SetlistfmScraper()
    return scrapers


def get_database_stats():
    try:
        db = VenueDatabase()
        total_venues = db.get_venues_count()
        conn = sqlite3.connect('venues.db')
        cursor = conn.cursor()
        total_shows = cursor.execute('SELECT COUNT(*) FROM shows').fetchone()[0]
        total_artists = cursor.execute('SELECT COUNT(DISTINCT name) FROM artists').fetchone()[0]
        conn.close()
        db.close()
        return {'total_venues': total_venues, 'total_shows': total_shows, 'total_artists': total_artists}
    except Exception:
        return {'total_venues': 0, 'total_shows': 0, 'total_artists': 0}


def get_all_venues_df():
    try:
        db = VenueDatabase()
        venues = db.get_all_venues_with_artists()
        db.close()
        if venues:
            df = pd.DataFrame(venues)
            display_cols = ['id', 'name', 'city', 'state', 'country', 'artists', 'venue_type', 'status', 'notes', 'created_at']
            df = df[[col for col in display_cols if col in df.columns]]
            df['status'] = df['status'].fillna('')
            df['status'] = df['status'].replace('New', '')
            df['notes'] = df['notes'].fillna('')
            df['artists'] = df['artists'].fillna('')
            df['city'] = df['city'].fillna('')
            df['state'] = df['state'].fillna('')
            df['country'] = df['country'].fillna('')
            if 'venue_type' in df.columns:
                df['venue_type'] = df['venue_type'].fillna('Show')
                # Truncate long festival names for display
                df['venue_type'] = df['venue_type'].apply(
                    lambda x: x if len(x) <= 25 else x[:22] + '...'
                )
            return df
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()


SCRAPING_QUIPS = [
    "Scouring the internet so you don't have to...",
    "Knocking on every venue's digital door...",
    "Doing the tedious work so you can do the fun stuff...",
    "Hunting down every last gig listing...",
    "Crawling through concert listings like a detective...",
    "Turning the internet inside out for venue intel...",
    "Bothering Songkick and Setlist.fm on your behalf...",
    "Building your venue empire one show at a time...",
    "Separating the festivals from the dive bars...",
    "Compiling the world's most useful spreadsheet...",
    "Making cold outreach slightly less cold...",
    "Doing hours of research in minutes...",
    "Finding where the magic happens, literally...",
    "Your personal booking assistant is on the case...",
    "This beats googling 29 artists by hand...",
    "Worth the wait, we promise...",
    "Meanwhile, you could be writing that perfect pitch email...",
    "Mapping the live music universe...",
]


def run_scraper(artists):
    import random
    quip_display = st.empty()
    progress_bar = st.progress(0)
    status_text = st.empty()
    db = VenueDatabase()
    manager = VenueManager(db)
    scrapers = get_enabled_scrapers()
    total_stats = {'total_events': 0, 'total_new_venues': 0, 'total_new_shows': 0, 'artist_details': {}}

    # Shuffle quips so they're different each run
    quips = random.sample(SCRAPING_QUIPS, len(SCRAPING_QUIPS))

    for idx, artist in enumerate(artists):
        quip = quips[idx % len(quips)]
        quip_display.markdown(f'<div style="font-size: 0.82rem; color: #d4a04a; font-style: italic; margin-bottom: 0.3rem;">{quip}</div>', unsafe_allow_html=True)
        status_text.text(f"Scraping {artist}... ({idx + 1}/{len(artists)})")
        progress_bar.progress(idx / len(artists))
        artist_stats = {'new_venues': 0, 'existing_venues': 0, 'new_shows': 0, 'total_events': 0, 'sources': []}
        for scraper_name, scraper in scrapers.items():
            try:
                scraped_data = scraper.scrape_artist(artist)
                if scraped_data:
                    stats = manager.process_scraped_data(artist, scraped_data)
                    artist_stats['new_venues'] += stats['new_venues']
                    artist_stats['existing_venues'] += stats['existing_venues']
                    artist_stats['new_shows'] += stats['new_shows']
                    artist_stats['total_events'] += stats['total_events']
                    artist_stats['sources'].append(scraper_name)
            except Exception as e:
                artist_stats['error'] = str(e)
        if artist_stats['total_events'] == 0 and 'error' not in artist_stats:
            artist_stats['message'] = 'No upcoming events found'
        total_stats['total_events'] += artist_stats['total_events']
        total_stats['total_new_venues'] += artist_stats['new_venues']
        total_stats['total_new_shows'] += artist_stats['new_shows']
        total_stats['artist_details'][artist] = artist_stats

    progress_bar.progress(1.0)
    quip_display.empty()
    status_text.text("Done")
    db.merge_duplicate_venues()
    db.close()
    return total_stats


# =============================================================================
# SIDEBAR
# =============================================================================
with st.sidebar:
    st.header("ARTISTS")

    config = load_config()
    current_artists = config.get('artists', [])

    # Add artist
    new_artist = st.text_input("Add an artist", placeholder="e.g. Snarky Puppy", label_visibility="collapsed")
    if st.button("Add Artist", use_container_width=True):
        if new_artist and new_artist not in current_artists:
            with st.spinner(f"Verifying '{new_artist}'..."):
                validation = validate_artist(new_artist)
            if any(v['found'] for v in validation):
                current_artists.append(new_artist)
                config['artists'] = current_artists
                save_config(config)
                found_on = [v['source'] for v in validation if v['found']]
                st.success(f"Added {new_artist} ({', '.join(found_on)})")
                st.rerun()
            else:
                checked = [v['source'] for v in validation]
                st.error(f"'{new_artist}' not found on {', '.join(checked)}. Check spelling.")
        elif new_artist in current_artists:
            st.warning("Already tracked")
        elif not new_artist:
            pass  # No empty submit noise

    # Artist list
    if current_artists:
        st.markdown(f'<div class="artist-count">{len(current_artists)} artists tracked</div>', unsafe_allow_html=True)
        with st.expander("Manage artists", expanded=False):
            for artist in current_artists:
                col1, col2 = st.columns([6, 1])
                with col1:
                    st.markdown(f'<div class="artist-item">{artist}</div>', unsafe_allow_html=True)
                with col2:
                    if st.button("🗑", key=f"rm_{artist}", help=f"Remove {artist}"):
                        current_artists.remove(artist)
                        config['artists'] = current_artists
                        save_config(config)
                        st.rerun()

        # Compact display when collapsed
        artist_preview = ", ".join(current_artists[:5])
        if len(current_artists) > 5:
            artist_preview += f" +{len(current_artists) - 5} more"
        st.caption(artist_preview)

    st.divider()

    # Scrape button
    st.header("ACTIONS")
    if current_artists:
        if st.button("Run Scraper", type="primary", use_container_width=True, disabled=st.session_state.scraper_running):
            st.session_state.scraper_running = True
            with st.spinner("Scraping..."):
                stats = run_scraper(current_artists)
                st.session_state.last_run_stats = stats
                st.session_state.scraper_running = False
                st.rerun()

    # Export
    venues_df = get_all_venues_df()
    if not venues_df.empty:
        export_df = venues_df.drop(columns=['id'], errors='ignore')
        export_df.columns = ['Venue', 'City', 'State', 'Country', 'Artists', 'Type', 'Status', 'Notes', 'Added']
        csv = export_df.to_csv(index=False)
        st.download_button(
            label="Export CSV",
            data=csv,
            file_name=f"venues_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )


# =============================================================================
# MAIN CONTENT
# =============================================================================

# Title
st.markdown('<h1 class="app-title">Venue Scraper</h1>', unsafe_allow_html=True)
st.markdown('<p class="app-subtitle">Find venues where similar artists play</p>', unsafe_allow_html=True)

# Last run banner
if st.session_state.last_run_stats:
    stats = st.session_state.last_run_stats
    st.markdown(
        f'<div class="run-banner">Last scrape: {stats["total_events"]} events found, '
        f'{stats["total_new_venues"]} new venues added</div>',
        unsafe_allow_html=True
    )

# Stats
db_stats = get_database_stats()
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(f'''<div class="stat-card">
        <div class="stat-value">{db_stats["total_venues"]}</div>
        <div class="stat-label">Venues</div>
    </div>''', unsafe_allow_html=True)
with c2:
    st.markdown(f'''<div class="stat-card">
        <div class="stat-value">{db_stats["total_shows"]}</div>
        <div class="stat-label">Shows</div>
    </div>''', unsafe_allow_html=True)
with c3:
    st.markdown(f'''<div class="stat-card">
        <div class="stat-value">{db_stats["total_artists"]}</div>
        <div class="stat-label">Artists</div>
    </div>''', unsafe_allow_html=True)

st.markdown("<div style='height: 1.2rem'></div>", unsafe_allow_html=True)

# =============================================================================
# VENUES TABLE
# =============================================================================
if not venues_df.empty:
    # Filters — single row
    f1, f2, f3 = st.columns([1, 1, 3])
    with f1:
        status_filter = st.selectbox("Status", ["All", "Interested", "Contacted", "Not a Fit", "No Status"], label_visibility="collapsed")
    with f2:
        type_filter = st.selectbox("Type", ["All Types", "Show", "Festival", "Both"], label_visibility="collapsed")
    with f3:
        search = st.text_input("Search", placeholder="Search venues, cities, countries...", label_visibility="collapsed")

    # Apply filters
    filtered_df = venues_df.copy()
    if status_filter == "No Status":
        filtered_df = filtered_df[filtered_df['status'] == '']
    elif status_filter != "All":
        filtered_df = filtered_df[filtered_df['status'] == status_filter]
    if type_filter != "All Types":
        if type_filter == "Festival":
            filtered_df = filtered_df[filtered_df['venue_type'].str.startswith('Festival')]
        else:
            filtered_df = filtered_df[filtered_df['venue_type'] == type_filter]
    if search:
        mask = filtered_df.apply(lambda row: row.astype(str).str.contains(search, case=False).any(), axis=1)
        filtered_df = filtered_df[mask]

    st.markdown(f'<div class="venue-count">{len(filtered_df)} of {len(venues_df)} venues</div>', unsafe_allow_html=True)

    # Data table
    edited_df = st.data_editor(
        filtered_df,
        use_container_width=True,
        hide_index=True,
        height=520,
        disabled=['id', 'name', 'city', 'state', 'country', 'artists', 'venue_type', 'created_at'],
        column_config={
            "id": None,
            "name": st.column_config.TextColumn("Venue", width="large"),
            "city": st.column_config.TextColumn("City", width="medium"),
            "state": st.column_config.TextColumn("State", width="small"),
            "country": st.column_config.TextColumn("Country", width="small"),
            "artists": st.column_config.TextColumn("Artists", width="medium"),
            "venue_type": st.column_config.TextColumn("Type", width="small"),
            "status": st.column_config.SelectboxColumn("Status", options=VENUE_STATUSES, width="small"),
            "notes": st.column_config.TextColumn("Notes", width="medium"),
            "created_at": st.column_config.DatetimeColumn("Added", format="MMM D, YYYY", width="small"),
        },
        key="venues_editor",
    )

    # Save edits
    if not edited_df.equals(filtered_df):
        db = VenueDatabase()
        for idx, row in edited_df.iterrows():
            original = filtered_df.loc[idx]
            venue_id = int(row['id'])
            if row['status'] != original['status']:
                db.update_venue_status(venue_id, row['status'])
            if row['notes'] != original['notes']:
                db.update_venue_notes(venue_id, row['notes'])
        db.close()
        st.rerun()

else:
    st.markdown("""
    <div style="text-align: center; padding: 4rem 2rem; color: #666;">
        <div style="font-size: 2.5rem; margin-bottom: 1rem;">🎵</div>
        <div style="font-family: 'DM Sans', sans-serif; font-size: 1.1rem; color: #888;">
            Add artists in the sidebar to get started
        </div>
    </div>
    """, unsafe_allow_html=True)
