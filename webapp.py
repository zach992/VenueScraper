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
import os

# Page configuration
st.set_page_config(
    page_title="Venue Scraper",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Minimal custom CSS (removed stat-box styles in favor of st.metric)
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
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

# Load persistent run history from disk on first load
if st.session_state.last_run_stats is None:
    results_file = Path("last_run_results.json")
    if results_file.exists():
        try:
            with open(results_file, 'r') as f:
                st.session_state.last_run_stats = json.load(f)
        except (json.JSONDecodeError, IOError):
            pass

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
            col_map = {'name': 'Venue Name', 'city': 'City', 'state': 'State',
                       'country': 'Country', 'venue_url': 'Venue URL',
                       'source': 'Source', 'created_at': 'Added On'}
            display_cols = [c for c in col_map if c in df.columns]
            df = df[display_cols].rename(columns=col_map)
            return df
        return pd.DataFrame()
    except:
        return pd.DataFrame()

def run_scraper(artists):
    """Run the scraper for given artists with live progress"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    live_counter = st.empty()

    db = VenueDatabase()
    manager = VenueManager(db)
    scraper = SongkickImprovedScraper()

    total_stats = {
        'total_events': 0,
        'total_new_venues': 0,
        'total_new_shows': 0,
        'artist_details': {}
    }

    start_time = time.time()

    for idx, artist in enumerate(artists):
        status_text.text(f"🎵 Scraping {artist}... ({idx + 1}/{len(artists)})")
        progress_bar.progress((idx) / len(artists))

        try:
            scraped_data = scraper.scrape_artist(artist)

            if scraped_data:
                stats = manager.process_scraped_data(artist, scraped_data)

                total_stats['total_events'] += stats['total_events']
                total_stats['total_new_venues'] += stats['new_venues']
                total_stats['total_new_shows'] += stats['new_shows']
                total_stats['artist_details'][artist] = stats
                live_counter.text(
                    f"Found {total_stats['total_events']} events, "
                    f"{total_stats['total_new_venues']} new venues, "
                    f"{total_stats['total_new_shows']} new shows so far"
                )
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

    elapsed = time.time() - start_time
    progress_bar.progress(1.0)
    status_text.text(f"✅ Scraping complete! ({elapsed:.1f}s)")
    live_counter.empty()
    db.close()

    return total_stats

# Main app layout
st.markdown('<h1 class="main-header">🎵 Venue Scraper</h1>', unsafe_allow_html=True)
st.markdown("### Discover and track concert venues from your favorite artists")

config = load_config()
current_artists = config.get('artists', [])

# Sidebar - reorganized by action frequency
with st.sidebar:
    # 1. Primary action: Run Scraper (at top)
    st.header("🚀 Run Scraper")
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

    st.divider()

    # 2. Data Export (single-click)
    st.subheader("💾 Data")
    db_stats = get_database_stats()

    if st.button("🔄 Refresh Data", use_container_width=True):
        st.rerun()

    if db_stats['total_venues'] > 0:
        df_export = get_all_venues()
        if not df_export.empty:
            csv = df_export.to_csv(index=False)
            st.download_button(
                label="📥 Export to CSV",
                data=csv,
                file_name=f"venues_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )

    # Geocode button
    try:
        import geopy
        has_geopy = True
    except ImportError:
        has_geopy = False

    if has_geopy and db_stats['total_venues'] > 0:
        if st.button("🌍 Geocode Venues", use_container_width=True, help="Add map coordinates to venues"):
            with st.spinner("Geocoding venues..."):
                db = VenueDatabase()
                result = db.geocode_venues()
                db.close()
                if 'error' in result:
                    st.error(result['error'])
                else:
                    st.success(f"Updated {result['updated']}/{result['total']} venues")
                    st.rerun()

    st.divider()

    # 3. Artist Management (collapsible)
    with st.expander(f"🎸 Artists ({len(current_artists)})", expanded=False):
        # Bulk add
        new_artists_text = st.text_area("Add artists (one per line):", height=80, key="bulk_artists")
        if st.button("➕ Add Artists", use_container_width=True):
            if new_artists_text.strip():
                added = []
                for name in new_artists_text.strip().split('\n'):
                    name = name.strip()
                    if name and name not in current_artists:
                        current_artists.append(name)
                        added.append(name)
                if added:
                    config['artists'] = current_artists
                    save_config(config)
                    st.success(f"Added {len(added)} artist(s)")
                    st.rerun()
                else:
                    st.warning("All artists already in list")
            else:
                st.warning("Enter at least one artist name")

        # Current artists with bulk remove
        if current_artists:
            st.caption(f"{len(current_artists)} artists tracked")
            to_remove = st.multiselect("Select to remove:", current_artists, key="remove_artists")
            if to_remove and st.button("🗑️ Remove Selected", use_container_width=True):
                for artist in to_remove:
                    current_artists.remove(artist)
                config['artists'] = current_artists
                save_config(config)
                st.rerun()
        else:
            st.info("No artists added yet")

# Main content area
stats = get_database_stats()

# Empty state / first-run experience
if stats['total_venues'] == 0 and stats['total_shows'] == 0:
    st.markdown("---")
    st.markdown("### 👋 Welcome! Let's get started")
    st.markdown("""
    **Step 1:** Add your favorite artists in the sidebar (click the Artists expander)

    **Step 2:** Click **Start Scraping** to find their upcoming shows

    **Step 3:** Explore venues, upcoming shows, and map visualizations!
    """)
    if not current_artists:
        st.info("Open the sidebar and add some artists to begin.")
    else:
        st.success(f"You have {len(current_artists)} artist(s) ready. Click **Start Scraping** in the sidebar!")
else:
    # Normal tabbed view
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Dashboard", "🎶 Upcoming Shows", "🏛️ Venues", "🗺️ Map", "ℹ️ About"])

    with tab1:
        # Show last run stats if available
        if st.session_state.last_run_stats:
            st.markdown("### ✅ Last Scraping Results")
            run_stats = st.session_state.last_run_stats

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Events Found", run_stats['total_events'])
            with col2:
                st.metric("New Venues", run_stats['total_new_venues'])
            with col3:
                st.metric("New Shows", run_stats['total_new_shows'])

            # Per-artist breakdown
            if run_stats.get('artist_details'):
                with st.expander("Per Artist Breakdown"):
                    for artist, artist_stats in run_stats['artist_details'].items():
                        if 'error' in artist_stats:
                            st.error(f"**{artist}**: Error - {artist_stats['error']}")
                        else:
                            st.write(f"✅ **{artist}**: {artist_stats['total_events']} events, {artist_stats['new_venues']} new venues")

            st.divider()

        # Database statistics using st.metric
        st.markdown("### 📈 Database Statistics")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Venues", stats["total_venues"])
        with col2:
            st.metric("Total Shows", stats["total_shows"])
        with col3:
            st.metric("Artists Tracked", stats["total_artists"])

        # Recent venues
        if stats['recent_venues']:
            st.markdown("### 🆕 Recently Added Venues")
            recent_df = pd.DataFrame(stats['recent_venues'])
            display_cols = ['name', 'city', 'country', 'created_at']
            recent_df = recent_df[[col for col in display_cols if col in recent_df.columns]]
            recent_df.columns = ['Venue Name', 'City', 'Country', 'Added On']
            st.dataframe(recent_df, use_container_width=True, hide_index=True)

    with tab2:
        # Upcoming Shows tab
        st.markdown("### 🎶 Upcoming Shows")

        try:
            db = VenueDatabase()

            # Filters
            filter_col1, filter_col2 = st.columns(2)
            with filter_col1:
                db_artists = db.get_distinct_artists()
                artist_options = ["All"] + db_artists
                selected_artist = st.selectbox("Filter by Artist", artist_options, key="shows_artist_filter")
            with filter_col2:
                countries = db.get_distinct_countries()
                country_options = ["All"] + countries
                selected_country = st.selectbox("Filter by Country", country_options, key="shows_country_filter")

            artist_f = selected_artist if selected_artist != "All" else None
            country_f = selected_country if selected_country != "All" else None

            shows = db.get_upcoming_shows(limit=200, artist_filter=artist_f, country_filter=country_f)
            db.close()

            if shows:
                shows_df = pd.DataFrame(shows)
                shows_df.columns = ['Date', 'Ticket Link', 'Artist', 'Venue', 'City', 'State', 'Country', 'Venue URL']
                st.caption(f"Showing {len(shows_df)} upcoming shows")

                st.dataframe(
                    shows_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Date": st.column_config.TextColumn("Date", width="medium"),
                        "Artist": st.column_config.TextColumn("Artist", width="medium"),
                        "Venue": st.column_config.TextColumn("Venue", width="large"),
                        "City": st.column_config.TextColumn("City", width="medium"),
                        "State": st.column_config.TextColumn("State", width="small"),
                        "Country": st.column_config.TextColumn("Country", width="medium"),
                        "Ticket Link": st.column_config.LinkColumn("Tickets", display_text="🎟️ Link", width="small"),
                        "Venue URL": st.column_config.LinkColumn("Venue Page", display_text="🔗 Link", width="small"),
                    }
                )

                # Artist drill-down
                if selected_artist != "All":
                    with st.expander(f"All venues for {selected_artist}"):
                        db2 = VenueDatabase()
                        venues_for_artist = db2.get_venues_for_artist(selected_artist)
                        db2.close()
                        if venues_for_artist:
                            va_df = pd.DataFrame(venues_for_artist)
                            st.dataframe(va_df, use_container_width=True, hide_index=True)
                        else:
                            st.write("No venue data available")
            else:
                st.info("No upcoming shows found. Run the scraper to find events!")
        except Exception as e:
            st.error(f"Error loading shows: {str(e)}")

    with tab3:
        st.markdown("### 🏛️ All Venues")

        venues_df = get_all_venues()

        if not venues_df.empty:
            # Faceted filtering
            filter_col1, filter_col2, filter_col3 = st.columns(3)
            with filter_col1:
                if 'Country' in venues_df.columns:
                    venue_countries = ["All"] + sorted(venues_df['Country'].dropna().unique().tolist())
                    venue_country_filter = st.selectbox("Country", venue_countries, key="venue_country_filter")
                else:
                    venue_country_filter = "All"
            with filter_col2:
                if 'Source' in venues_df.columns:
                    venue_sources = ["All"] + sorted(venues_df['Source'].dropna().unique().tolist())
                    venue_source_filter = st.selectbox("Source", venue_sources, key="venue_source_filter")
                else:
                    venue_source_filter = "All"
            with filter_col3:
                search = st.text_input("🔍 Search venues:", placeholder="Enter venue name, city...", key="venue_search")

            filtered_df = venues_df.copy()
            if venue_country_filter != "All":
                filtered_df = filtered_df[filtered_df['Country'] == venue_country_filter]
            if venue_source_filter != "All":
                filtered_df = filtered_df[filtered_df['Source'] == venue_source_filter]
            if search:
                mask = filtered_df.apply(lambda row: row.astype(str).str.contains(search, case=False).any(), axis=1)
                filtered_df = filtered_df[mask]

            st.caption(f"Showing {len(filtered_df)} of {len(venues_df)} venues")

            st.dataframe(
                filtered_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Venue Name": st.column_config.TextColumn("Venue Name", width="large"),
                    "City": st.column_config.TextColumn("City", width="medium"),
                    "State": st.column_config.TextColumn("State", width="small"),
                    "Country": st.column_config.TextColumn("Country", width="medium"),
                    "Venue URL": st.column_config.LinkColumn("Venue URL", display_text="🔗 Link", width="small"),
                    "Source": st.column_config.TextColumn("Source", width="small"),
                    "Added On": st.column_config.DatetimeColumn("Added On", format="MMM D, YYYY"),
                }
            )

            # Venue drill-down
            st.markdown("### 🔍 Venue Details")
            try:
                db = VenueDatabase()
                all_venues_raw = db.get_all_venues()
                venue_names = [v['name'] for v in all_venues_raw]
                selected_venue = st.selectbox("Select a venue to see its shows:", [""] + venue_names, key="venue_drilldown")
                if selected_venue:
                    venue_id = next((v['id'] for v in all_venues_raw if v['name'] == selected_venue), None)
                    if venue_id:
                        venue_shows = db.get_shows_for_venue(venue_id)
                        if venue_shows:
                            vs_df = pd.DataFrame(venue_shows)
                            vs_df.columns = ['Date', 'Ticket Link', 'Artist', 'Source']
                            st.dataframe(
                                vs_df, use_container_width=True, hide_index=True,
                                column_config={
                                    "Ticket Link": st.column_config.LinkColumn("Tickets", display_text="🎟️ Link"),
                                }
                            )
                        else:
                            st.info("No shows found for this venue")
                db.close()
            except Exception:
                pass

            # Group by country
            st.markdown("### 🌍 Venues by Country")
            if 'Country' in venues_df.columns:
                country_counts = venues_df['Country'].value_counts()
                st.bar_chart(country_counts)

        else:
            st.info("No venues in database yet. Add some artists and run the scraper!")

    with tab4:
        # Map tab
        st.markdown("### 🗺️ Venue Map")

        try:
            db = VenueDatabase()
            venues_with_coords = db.get_venues_with_coordinates()
            db.close()

            if venues_with_coords:
                map_df = pd.DataFrame(venues_with_coords)
                map_df = map_df.rename(columns={'latitude': 'lat', 'longitude': 'lon'})
                st.caption(f"Showing {len(map_df)} venues on map")
                st.map(map_df)
            else:
                st.info("No venue coordinates available. Click **Geocode Venues** in the sidebar to add map coordinates, or run the scraper to collect new data with coordinates.")
        except Exception as e:
            st.error(f"Error loading map: {str(e)}")

    with tab5:
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
        - 🎶 Upcoming shows with ticket links
        - 🗺️ Map visualization of venues
        - 🔄 Smart deduplication (no duplicate venues)
        - 📊 Beautiful statistics and visualizations
        - 📥 One-click export to CSV
        - 🔍 Search and filter your venues

        **Tips:**
        - Run the scraper regularly to catch new tour announcements
        - Use the search feature to find specific venues
        - Export your data to analyze in Excel or Google Sheets
        - Click "Geocode Venues" to enable the map view

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
