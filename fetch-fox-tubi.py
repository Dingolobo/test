import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime
import uuid  # Nueva: para generar device_id aleatorio
import sys

# Configuration
BASE_URL = "https://epg-cdn.production-public.tubi.io/content/epg/programming"
PARAMS = {
    "platform": "web",
    "lookahead": "1",
    "content_id": "400000122"
}
CHANNEL_ID = "400000122"
OUTPUT_FILE = "tubi_fox.xml"
CHANNEL_NAME = "FOX en Tubi"  # Default from sample
LANG = "es"  # From sample lang: ["Spanish"]

def generate_device_id():
    """Generate a random UUID for device_id."""
    return str(uuid.uuid4())

def fetch_epg_data():
    """Fetch JSON data from the URL with dynamic device_id."""
    device_id = generate_device_id()
    url = f"{BASE_URL}?platform={PARAMS['platform']}&device_id={device_id}&lookahead={PARAMS['lookahead']}&content_id={PARAMS['content_id']}"
    
    print(f"Fetching from URL: {url}")  # Debug: muestra la URL generada
    
    try:
        response = requests.get(url, timeout=10)
        print(f"HTTP Status: {response.status_code}")  # Debug: código de estado
        
        if response.status_code != 200:
            print(f"Error: HTTP {response.status_code}. Response: {response.text[:500]}...")  # Debug: muestra parte del error
            return None
        
        data = response.json()
        print(f"JSON keys: {list(data.keys()) if data else 'No JSON'}")  # Debug: estructura del JSON
        print(f"Rows count: {len(data.get('rows', [])) if data else 0}")  # Debug: número de rows
        
        return data
    except requests.RequestException as e:
        print(f"Request error: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}. Response: {response.text[:500]}...")
        return None

def parse_time(iso_time):
    """Convert ISO time (e.g., '2025-10-08T18:00:03Z') to XMLTV format (YYYYMMDDHHMMSS +0000)."""
    if not iso_time:
        return ""
    try:
        dt = datetime.fromisoformat(iso_time.replace('Z', '+00:00'))
        return dt.strftime("%Y%m%d%H%M%S +0000")
    except ValueError:
        print(f"Invalid time format: {iso_time}")
        return ""

def build_xmltv(data):
    """Build XMLTV from the JSON data."""
    if not data or 'rows' not in data or not data['rows']:
        print("No 'rows' in data or empty. Cannot build XMLTV.")
        return None

    row = data['rows'][0]  # Assuming single row for the channel
    programs = row.get('programs', [])
    print(f"Programs count: {len(programs)}")  # Debug

    if not programs:
        print("No programs in row. Cannot build XMLTV.")
        return None

    # Create root <tv> element
    tv = ET.Element('tv', {
        'generator-info-name': 'Tubi EPG to XMLTV Converter',
        'source-info-url': BASE_URL,
        'source-info-name': 'Tubi EPG'
    })

    # Channel element
    channel = ET.SubElement(tv, 'channel', {'id': CHANNEL_ID})
    display_name = ET.SubElement(channel, 'display-name')
    display_name.text = row.get('title', CHANNEL_NAME)
    
    # Logo from thumbnail (prefer custom, fallback to images.thumbnail)
    thumbnail_url = ""
    images = row.get('images', {})
    custom = images.get('custom', {})
    if 'thumbnail' in custom and custom['thumbnail']:
        thumbnail_url = custom['thumbnail'][0]
    elif 'thumbnail' in images and images['thumbnail']:
        thumbnail_url = images['thumbnail'][0]
    if thumbnail_url:
        icon = ET.SubElement(channel, 'icon', {'src': thumbnail_url})
        print(f"Channel logo: {thumbnail_url}")  # Debug

    # Programme elements
    for i, program in enumerate(programs):
        start_time = parse_time(program.get('start_time'))
        end_time = parse_time(program.get('end_time'))
        if not start_time or not end_time:
            print(f"Skipping program {i}: invalid times")
            continue

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
        if season_num is not None and episode_num is not None and (season_num != 0 or episode_num != 0):
            ep_num_text = f"{int(season_num):02d}{int(episode_num):02d}"
            episode_elem = ET.SubElement(programme, 'episode-num', {'system': 'xmltv_ns'})
            episode_elem.text = ep_num_text

        # Ratings
        ratings = program.get('ratings', [])
        if ratings:
            rating = ratings[0]
            rating_elem = ET.SubElement(programme, 'rating', {'system': rating.get('system', 'mpaa')})
            value_elem = ET.SubElement(rating_elem, 'value')
            value_elem.text = rating.get('value', '')

        # Poster
        poster_url = ""
        prog_images = program.get('images', {})
        if 'poster' in prog_images and prog_images['poster']:
            poster_url = prog_images['poster'][0]
        if poster_url:
            prog_icon = ET.SubElement(programme, 'icon', {'src': poster_url})
            print(f"Program {i} poster: {poster_url}")  # Debug

    print(f"Built XMLTV with {len(tv)} channels and {len(tv.findall('programme'))} programmes")
    return tv

def save_xml(tv_root, filename):
    """Save XML to file with proper formatting."""
    rough_string = ET.tostring(tv_root, 'unicode', short_empty_elements=False)
    reparsed = ET.fromstring(rough_string)
    try:
        ET.indent(reparsed, space="  ", level=0)  # Pretty print (Python 3.9+)
    except AttributeError:
        pass  # Fallback if indent not available
    tree = ET.ElementTree(reparsed)
    tree.write(filename, encoding='utf-8', xml_declaration=True, short_empty_elements=False)
    print(f"XML saved to {filename}")

def main():
    data = fetch_epg_data()
    if data:
        tv = build_xmltv(data)
        if tv:
            save_xml(tv, OUTPUT_FILE)
            print("Success: XMLTV generated.")
            sys.exit(0)  # Exit success
        else:
            print("Failed to build XMLTV (but data was fetched).")
            sys.exit(1)
    else:
        print("No data fetched. Skipping XML generation.")
        # No exit 1 aquí para no fallar Actions si no hay datos
        sys.exit(0)

if __name__ == "__main__":
    main()
