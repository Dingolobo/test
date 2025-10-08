import json
import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.parse import quote
import sys

# Config (mismo que antes)
BASE_URL = "https://epg-cdn.production-public.tubi.io/content/epg/programming"
PARAMS = {
    "platform": "web",
    "device_id": "",
    "lookahead": "1",
    "content_id": "400000122"
}
CHANNEL_ID = "400000122"
INPUT_JSON = "tubi_data.json"  # Archivo de curl
OUTPUT_XML = "tubi_fox.xml"
CHANNEL_NAME = "FOX en Tubi"
LANG = "es"

def build_url():
    query_params = "&".join([f"{k}={quote(v)}" for k, v in PARAMS.items()])
    return f"{BASE_URL}?{query_params}"

def parse_time(iso_time):
    if not iso_time:
        return ""
    try:
        dt = datetime.fromisoformat(iso_time.replace('Z', '+00:00'))
        return dt.strftime("%Y%m%d%H%M%S +0000")
    except ValueError:
        return ""

def build_xml_from_json():
    try:
        with open(INPUT_JSON, 'r') as f:
            data = json.load(f)
        print(f"JSON loaded: {len(data.get('rows', []))} rows")
    except FileNotFoundError:
        print(f"ERROR: {INPUT_JSON} not found. Curl failed?")
        return None
    except json.JSONDecodeError:
        print("ERROR: Invalid JSON in file.")
        return None

    if not data or 'rows' not in data or not data['rows']:
        print("ERROR: No rows in JSON.")
        return None

    row = data['rows'][0]
    programs = row.get('programs', [])
    print(f"Building XML for channel '{row.get('title', CHANNEL_NAME)}' with {len(programs)} programs.")

    if not programs:
        print("ERROR: No programs.")
        return None

    # XML root
    tv = ET.Element('tv', attrib={
        'generator-info-name': 'Tubi EPG Simple Converter',
        'source-info-url': build_url(),
        'source-info-name': 'Tubi EPG'
    })

    # Channel
    channel = ET.SubElement(tv, 'channel', attrib={'id': CHANNEL_ID})
    ET.SubElement(channel, 'display-name').text = row.get('title', CHANNEL_NAME)

    # Thumbnail icon (simple)
    images = row.get('images', {})
    thumbnail = images.get('thumbnail')
    if isinstance(thumbnail, list) and thumbnail:
        ET.SubElement(channel, 'icon', attrib={'src': thumbnail[0]})

    # Programmes
    for program in programs:
        start = parse_time(program.get('start_time'))
        end = parse_time(program.get('end_time'))
        if not start or not end:
            continue

        programme = ET.SubElement(tv, 'programme', attrib={
            'start': start,
            'stop': end,
            'channel': CHANNEL_ID
        })

        ET.SubElement(programme, 'title', attrib={'lang': LANG}).text = program.get('title', '')
        ET.SubElement(programme, 'desc', attrib={'lang': LANG}).text = program.get('description', '')

        year = program.get('year')
        if year and year != '0':
            ET.SubElement(programme, 'date').text = year

        season = program.get('season_number')
        episode = program.get('episode_number')
        if season is not None and episode is not None and season != 0 and episode != 0:
            ep_text = f"{int(season):02d}{int(episode):02d}"
            ET.SubElement(programme, 'episode-num', attrib={'system': 'xmltv_ns'}).text = ep_text

        ratings = program.get('ratings', [])
        if ratings:
            rating = ratings[0]
            rating_elem = ET.SubElement(programme, 'rating', attrib={'system': rating.get('system', 'mpaa')})
            ET.SubElement(rating_elem, 'value').text = rating.get('value', '')

        # Poster
        prog_images = program.get('images', {})
        poster = prog_images.get('poster')
        if isinstance(poster, list) and poster:
            ET.SubElement(programme, 'icon', attrib={'src': poster[0]})

    # Save XML
    rough = ET.tostring(tv, 'unicode')
    root = ET.fromstring(rough)
    try:
        ET.indent(root, space="  ")
    except:
        pass
    tree = ET.ElementTree(root)
    tree.write(OUTPUT_XML, encoding='utf-8', xml_declaration=True)
    print(f"XML saved to {OUTPUT_XML}")
    return tv

if __name__ == "__main__":
    if build_xml_from_json():
        print("SUCCESS: XML generated.")
        sys.exit(0)
    else:
        print("Failed to generate XML.")
        sys.exit(1)
