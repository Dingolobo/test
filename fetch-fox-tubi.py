import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.parse import quote  # Agregado: Para codificar params en URL
import sys

# Configuration (device_id vacío para que funcione)
BASE_URL = "https://epg-cdn.production-public.tubi.io/content/epg/programming"
PARAMS = {
    "platform": "web",
    "device_id": "",  # Vacío: funciona como en tu ejemplo
    "lookahead": "1",  # Funciona y devuelve programs
    "content_id": "400000122"
}
CHANNEL_ID = "400000122"
OUTPUT_FILE = "tubi_fox.xml"
CHANNEL_NAME = "FOX en Tubi"  # Default from sample
LANG = "es"  # From lang: ["Spanish"]

def build_url():
    """Build the full URL from params."""
    query_params = "&".join([f"{k}={quote(v)}" for k, v in PARAMS.items()])  # quote para URLs seguras
    return f"{BASE_URL}?{query_params}"

def fetch_epg_data():
    """Fetch data from the URL and log everything."""
    url = build_url()
    print(f"Fetching from URL: {url}")  # Log: URL completa
    
    try:
        response = requests.get(url, timeout=10)
        print(f"HTTP Status Code: {response.status_code}")  # Log: Código HTTP
        print(f"Content-Type: {response.headers.get('Content-Type', 'Unknown')}")  # Log: Tipo de contenido
        print(f"Response Length: {len(response.text)} characters")  # Log: Tamaño de respuesta
        
        if response.status_code != 200:
            print(f"ERROR: HTTP {response.status_code}")
            print(f"Response Body (first 1000 chars): {response.text[:1000]}...")
            return None
        
        # Intenta parsear como JSON
        try:
            data = response.json()
            print("SUCCESS: JSON parsed successfully.")
            print(f"JSON Top-Level Keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            
            rows = data.get('rows', [])
            print(f"Rows in JSON: {len(rows)}")
            
            if rows:
                first_row = rows[0]
                print(f"First Row Keys: {list(first_row.keys())}")
                programs = first_row.get('programs', [])
                print(f"Programs in First Row: {len(programs)}")
                if programs:
                    first_program = programs[0]
                    print(f"First Program Keys: {list(first_program.keys())}")
                    print(f"Sample First Program Title: {first_program.get('title', 'N/A')}")
                    print(f"Sample First Program Start Time: {first_program.get('start_time', 'N/A')}")
                else:
                    print("No programs in first row.")
            else:
                print("WARNING: 'rows' is empty. No programming data available.")
                print(f"Other JSON data: {data}")
            
            return data
        except json.JSONDecodeError as e:
            print(f"ERROR: Failed to parse JSON. Reason: {e}")
            print(f"Raw Response Body (first 1000 chars): {response.text[:1000]}...")
            return None
            
    except requests.RequestException as e:
        print(f"ERROR: Request failed. Reason: {e}")
        return None

def parse_time(iso_time):
    """Convert ISO time to XMLTV format (YYYYMMDDHHMMSS +0000)."""
    if not iso_time:
        return ""
    try:
        dt = datetime.fromisoformat(iso_time.replace('Z', '+00:00'))
        return dt.strftime("%Y%m%d%H%M%S +0000")
    except ValueError as e:
        print(f"WARNING: Invalid time format '{iso_time}': {e}")
        return ""

def build_xmltv(data):
    """Build XMLTV from the JSON data with logs."""
    print("Starting XMLTV build...")
    
    if not data or 'rows' not in data:
        print("ERROR: No 'rows' key in data. Cannot build XMLTV.")
        return None
    
    rows = data['rows']
    if not rows:
        print("ERROR: 'rows' is empty. Skipping XMLTV build.")
        return None
    
    row = rows[0]  # Single row for channel
    print(f"Processing row title: {row.get('title', 'N/A')}")
    programs = row.get('programs', [])
    print(f"Building with {len(programs)} programs.")

    if not programs:
        print("ERROR: No programs in row. Cannot build XMLTV.")
        return None

    # Create root <tv> element
    tv = ET.Element('tv', {
        'generator-info-name': 'Tubi EPG to XMLTV Converter',
        'source-info-url': build_url(),
        'source-info-name': 'Tubi EPG'
    })

    # Channel element
    channel = ET.SubElement(tv, 'channel', {'id': CHANNEL_ID})
    display_name = ET.SubElement(channel, 'display-name')
    display_name.text = row.get('title', CHANNEL_NAME)
    print(f"Channel display-name set to: {display_name.text}")
    
    # Logo from thumbnail (prefer custom, fallback to images.thumbnail)
    thumbnail_url = ""
    images = row.get('images', {})
    custom = images.get('custom', {})
    if isinstance(custom, dict) and 'thumbnail' in custom and isinstance(custom['thumbnail'], list) and custom['thumbnail']:
        thumbnail_url = custom['thumbnail'][0]
        print(f"Using custom thumbnail: {thumbnail_url}")
    elif isinstance(images.get('thumbnail'), list) and images['thumbnail']:
        thumbnail_url = images['thumbnail'][0]
        print(f"Using default thumbnail: {thumbnail_url}")
    else:
        print("No thumbnail URL found.")
    
    if thumbnail_url:
        icon = ET.SubElement(channel, 'icon', {'src': thumbnail_url})

    # Programme elements (compatibilidad XMLTV)
    valid_programs = 0
    for i, program in enumerate(programs):
        print(f"Processing program {i}: {program.get('title', 'N/A')}")
        start_time = parse_time(program.get('start_time'))
        end_time = parse_time(program.get('end_time'))
        if not start_time or not end_time:
            print(f"  Skipping: Invalid times (start: {program.get('start_time')}, end: {program.get('end_time')})")
            continue

        programme = ET.SubElement(tv, 'programme', {
            'start': start_time,
            'stop': end_time,
            'channel': CHANNEL_ID
        })
        valid_programs += 1

        # Title
        title = ET.SubElement(programme, 'title', {'lang': LANG})
        title.text = program.get('title', '')
        print(f"  Title: {title.text}")

        # Description
        desc = ET.SubElement(programme, 'desc', {'lang': LANG})
        desc.text = program.get('description', '')
        print(f"  Desc: {desc.text[:50]}..." if desc.text else "  Desc: Empty")

        # Date (year) - solo si no es "0"
        year = program.get('year')
        if year and year != '0':
            date_elem = ET.SubElement(programme, 'date')
            date_elem.text = year
            print(f"  Year: {year}")

        # Episode (season and episode) - formato SxxEyy si disponibles y no null/0
        season_num = program.get('season_number')
        episode_num = program.get('episode_number')
        if season_num is not None and episode_num is not None and (season_num != 0 or episode_num != 0):
            try:
                ep_num_text = f"{int(season_num):02d}{int(episode_num):02d}"
                episode_elem = ET.SubElement(programme, 'episode-num', {'system': 'xmltv_ns'})
                episode_elem.text = ep_num_text
                print(f"  Episode: S{season_num}E{episode_num}")
            except ValueError:
                print(f"  Skipping episode: Invalid season/episode numbers")

        # Ratings
        ratings = program.get('ratings', [])
        if ratings:
            rating = ratings[0]  # Primer rating
            rating_elem = ET.SubElement(programme, 'rating', {'system': rating.get('system', 'mpaa')})
            value_elem = ET.SubElement(rating_elem, 'value')
            value_elem.text = rating.get('value', '')
            print(f"  Rating: {rating.get('value', 'N/A')} ({rating.get('system', 'N/A')})")

        # Poster (como <icon> en programme para compatibilidad extendida)
        prog_images = program.get('images', {})
        poster_url = ""
        if isinstance(prog_images.get('poster'), list) and prog_images['poster']:
            poster_url = prog_images['poster'][0]
        if poster_url:
            prog_icon = ET.SubElement(programme, 'icon', {'src': poster_url})
            print(f"  Poster: {poster_url}")

    print(f"Built XMLTV with 1 channel and {valid_programs} valid programmes.")
    return tv

def save_xml(tv_root, filename):
    """Save XML to file with proper formatting."""
    rough_string = ET.tostring(tv_root, 'unicode', short_empty_elements=False)
    reparsed = ET.fromstring(rough_string)
    try:
        ET.indent(reparsed, space="  ", level=0)  # Pretty print (Python 3.9+)
    except AttributeError:
        pass  # Ignora si versión antigua
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
            sys.exit(0)
        else:
            print("No valid data to build XMLTV (e.g., empty rows). Skipping generation.")
            sys.exit(0)  # No falla Actions
    else:
        print("No data fetched. Skipping XML generation.")
        sys.exit(0)

if __name__ == "__main__":
    main()
