import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.parse import quote

# Configuration
URL = "https://epg-cdn.production-public.tubi.io/content/epg/programming?platform=web&device_id=dac210c3-7209-475a-bbe8-984bf3462007&lookahead=1&content_id=400000122"
CHANNEL_ID = "400000122"
OUTPUT_FILE = "tubi_fox.xml"
CHANNEL_NAME = "FOX en Tubi"  # Default from sample; can be overridden from data
LANG = "es"  # From sample lang: ["Spanish"]

def fetch_epg_data():
    """Fetch JSON data from the URL."""
    try:
        response = requests.get(URL)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def parse_time(iso_time):
    """Convert ISO time (e.g., '2025-10-08T18:00:03Z') to XMLTV format (YYYYMMDDHHMMSS +0000)."""
    if not iso_time:
        return ""
    dt = datetime.fromisoformat(iso_time.replace('Z', '+00:00'))
    return dt.strftime("%Y%m%d%H%M%S +0000")

def build_xmltv(data):
    """Build XMLTV from the JSON data."""
    if not data or 'rows' not in data or not data['rows']:
        print("No data available.")
        return None

    row = data['rows'][0]  # Assuming single row for the channel
    programs = row.get('programs', [])

    # Create root <tv> element
    tv = ET.Element('tv', {
        'generator-info-name': 'Tubi EPG to XMLTV Converter',
        'source-info-url': URL,
        'source-info-name': 'Tubi EPG'
    })

    # Channel element
    channel = ET.SubElement(tv, 'channel', {'id': CHANNEL_ID})
    display_name = ET.SubElement(channel, 'display-name')
    display_name.text = row.get('title', CHANNEL_NAME)
    # Logo from thumbnail (fallback to custom if available, but sample uses images.thumbnail)
    thumbnail_url = ""
    if 'images' in row and 'thumbnail' in row['images'] and row['images']['thumbnail']:
        thumbnail_url = row['images']['thumbnail'][0]
    elif 'images' in row and 'custom' in row['images'] and 'thumbnail' in row['images']['custom'] and row['images']['custom']['thumbnail']:
        thumbnail_url = row['images']['custom']['thumbnail'][0]
    if thumbnail_url:
        icon = ET.SubElement(channel, 'icon', {'src': thumbnail_url})

    # Programme elements
    for program in programs:
        start_time = parse_time(program.get('start_time'))
        end_time = parse_time(program.get('end_time'))
        if not start_time or not end_time:
            continue  # Skip invalid programs

        programme = ET.SubElement(tv, 'programme', {
            'start': start_time,
            'stop': end_time,
            'channel': CHANNEL_ID
        })

        # Title
        title = ET.SubElement(programme, 'title', {'lang': LANG})
        title.text = program.get('title', '')

        # Description
        desc = ET.SubElement(programme, 'desc', {'lang': LANG})
        desc.text = program.get('description', '')

        # Date (year)
        year = program.get('year')
        if year and year != '0':
            date_elem = ET.SubElement(programme, 'date')
            date_elem.text = year

        # Episode (season and episode)
        season_num = program.get('season_number')
        episode_num = program.get('episode_number')
        if season_num is not None and episode_num is not None:
            # XMLTV episode-num: format is SxxEyy (0-based, but adjust if needed)
            ep_num_text = f"{int(season_num):02d}{int(episode_num):02d}" if season_num != 0 or episode_num != 0 else None
            if ep_num_text:
                episode_elem = ET.SubElement(programme, 'episode-num', {'system': 'xmltv_ns'})
                episode_elem.text = ep_num_text

        # Ratings
        ratings = program.get('ratings', [])
        if ratings:
            rating = ratings[0]  # Take first rating
            rating_elem = ET.SubElement(programme, 'rating', {'system': rating.get('system', 'mpaa')})
            value_elem = ET.SubElement(rating_elem, 'value')
            value_elem.text = rating.get('value', '')

        # Poster (non-standard, but add as <icon> for programme if available)
        poster_url = ""
        if 'images' in program and 'poster' in program['images'] and program['images']['poster']:
            poster_url = program['images']['poster'][0]
        if poster_url:
            prog_icon = ET.SubElement(programme, 'icon', {'src': poster_url})

    return tv

def save_xml(tv_root, filename):
    """Save XML to file with proper formatting."""
    rough_string = ET.tostring(tv_root, 'unicode')
    reparsed = ET.fromstring(rough_string)
    ET.indent(reparsed, space="  ", level=0)  # Pretty print (Python 3.9+)
    tree = ET.ElementTree(reparsed)
    tree.write(filename, encoding='utf-8', xml_declaration=True)

def main():
    data = fetch_epg_data()
    if data:
        tv = build_xmltv(data)
        if tv:
            save_xml(tv, OUTPUT_FILE)
            print(f"XMLTV file generated: {OUTPUT_FILE}")
        else:
            print("Failed to build XMLTV.")
    else:
        print("No data fetched.")

if __name__ == "__main__":
    main()
