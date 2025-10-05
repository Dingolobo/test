import asyncio
import time
import xml.etree.ElementTree as ET
import xml.dom.minidom
from playwright.async_api import async_playwright

URL_TEMPLATE = ("https://tvlistings.gracenote.com/api/grid?"
                "lineupId=MEX-1008175-DEFAULT&timespan=6&headendId=1008175&country=MEX&timezone=&device=-"
                "&postalCode=&isOverride=true&pref=16,128&userId=-&aid=dishmex&languagecode=es-mx&time={timestamp}")

def json_to_xmltv(data):
    tv = ET.Element('tv')

    for channel in data.get('channels', []):
        ch = ET.SubElement(tv, 'channel', id=channel.get('channelId', ''))
        display_name = ET.SubElement(ch, 'display-name')
        display_name.text = channel.get('callSign', 'SinNombre')
        
        # Agregar el logo del canal como icono si está disponible
        thumbnail = channel.get('thumbnail', '')
        if thumbnail:
            icon = ET.SubElement(ch, 'icon', src=thumbnail)

        for event in channel.get('events', []):
            prog = ET.SubElement(tv, 'programme', {
                'start': event.get('startTime', '').replace('-', '').replace(':', '').replace('T', '').replace('Z', ' +0000'),
                'stop': event.get('endTime', '').replace('-', '').replace(':', '').replace('T', '').replace('Z', ' +0000'),
                'channel': channel.get('channelId', '')
            })
            title = ET.SubElement(prog, 'title')
            title.text = event.get('program', {}).get('title', 'Sin título')

            desc = ET.SubElement(prog, 'desc')
            desc.text = event.get('program', {}).get('shortDesc', '')

    return ET.tostring(tv, encoding='utf-8', xml_declaration=True).decode('utf-8')

def pretty_xml(xml_str):
    """Formatea el XML con sangrías para que sea legible."""
    dom = xml.dom.minidom.parseString(xml_str)
    return dom.toprettyxml(indent="  ")

async def fetch_epg():
    timestamp = int(time.time())
    url = URL_TEMPLATE.format(timestamp=timestamp)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        ))
        page = await context.new_page()

        response_data = None

        async def handle_response(response):
            nonlocal response_data
            if url in response.url and response.status == 200:
                try:
                    response_data = await response.json()
                except Exception as e:
                    print(f"Error parseando JSON: {e}")

        page.on("response", handle_response)

        await page.goto("https://tvlistings.gracenote.com/grid-affiliates.html?aid=dishmex")

        await page.evaluate(f"""
            fetch("{url}", {{
                headers: {{
                    "Accept": "application/json, text/javascript, */*; q=0.01",
                    "X-Requested-With": "XMLHttpRequest"
                }},
                credentials: "include"
            }});
        """)

        await asyncio.sleep(5)

        await browser.close()

        if response_data is None:
            raise Exception("No se pudo obtener datos EPG")

        return response_data

def save_xmltv(xml_str, filename="dish.xml"):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(xml_str)

def main():
    epg_data = asyncio.run(fetch_epg())
    xmltv_str = json_to_xmltv(epg_data)
    xmltv_pretty = pretty_xml(xmltv_str)
    save_xmltv(xmltv_pretty)
    print("Archivo dish.xml generado correctamente.")

if __name__ == "__main__":
    main()
