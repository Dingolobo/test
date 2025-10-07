import asyncio
import time
import xml.etree.ElementTree as ET
import xml.dom.minidom
from playwright.async_api import async_playwright

URL_TEMPLATE = ("https://tvlistings.gracenote.com/api/grid?"
                "lineupId=MEX-1008175-DEFAULT&timespan=6&headendId=1008175&country=MEX&timezone=&device=-"
                "&postalCode=&isOverride=true&pref=16,128&userId=-&aid=dishmex&languagecode=es-mx&time={timestamp}")

async def fetch_multiple(num_fetches=5, interval_seconds=21000):
    """Realiza múltiples fetches de EPG con timestamps incrementales."""
    base_ts = int(time.time())
    all_data = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        ))
        page = await context.new_page()

        # Ir a la página inicial para establecer cookies/sesión
        await page.goto("https://tvlistings.gracenote.com/grid-affiliates.html?aid=dishmex")
        await asyncio.sleep(2)  # Esperar un poco para cargar la página

        for i in range(num_fetches):
            current_ts = base_ts + i * interval_seconds
            url = URL_TEMPLATE.format(timestamp=current_ts)

            response_data = None

            async def handle_response(response):
                nonlocal response_data
                if url in response.url and response.status == 200:
                    try:
                        response_data = await response.json()
                    except Exception as e:
                        print(f"Error parseando JSON en fetch {i+1}: {e}")

            # Configurar listener para esta respuesta específica
            response_listener = page.on("response", handle_response)

            # Realizar el fetch via evaluate
            await page.evaluate(f"""
                fetch("{url}", {{
                    headers: {{
                        "Accept": "application/json, text/javascript, */*; q=0.01",
                        "X-Requested-With": "XMLHttpRequest"
                    }},
                    credentials: "include"
                }});
            """)

            # Esperar la respuesta (similar al original)
            await asyncio.sleep(5)

            # Remover el listener después de un tiempo para evitar acumulación
            page.remove_listener("response", response_listener)

            if response_data is not None:
                all_data.append(response_data)
                print(f"Fetch {i+1} completado para timestamp {current_ts}.")
            else:
                print(f"Advertencia: No se obtuvo respuesta para fetch {i+1}. Continuando...")

            # Pequeña pausa entre fetches para evitar rate limiting
            if i < num_fetches - 1:
                await asyncio.sleep(2)

        await browser.close()

    if not all_data:
        raise Exception("No se pudo obtener ningún dato EPG")

    return all_data

def merge_epg_data(all_data):
    """Fusiona múltiples conjuntos de datos EPG, eliminando duplicados."""
    channels = {}  # channelId -> {'callSign': str, 'events': list}

    for data in all_data:
        for channel in data.get('channels', []):
            cid = channel.get('channelId', '')
            if not cid:
                continue

            if cid not in channels:
                channels[cid] = {
                    'callSign': channel.get('callSign', 'SinNombre'),
                    'events': []
                }

            # Deduplicar eventos por startTime en este canal
            existing_starts = {e['startTime'] for e in channels[cid]['events']}
            for event in channel.get('events', []):
                start_time = event.get('startTime', '')
                if start_time and start_time not in existing_starts:
                    channels[cid]['events'].append(event)
                    existing_starts.add(start_time)

    # Ordenar eventos por startTime para cada canal (opcional, pero mejora legibilidad)
    for chdata in channels.values():
        chdata['events'].sort(key=lambda e: e.get('startTime', ''))

    return channels

def channels_to_xmltv(channels):
    """Convierte los canales fusionados a formato XMLTV."""
    tv = ET.Element('tv')

    # Crear elementos <channel>
    for cid, chdata in channels.items():
        ch = ET.SubElement(tv, 'channel', id=cid)
        display_name = ET.SubElement(ch, 'display-name')
        display_name.text = chdata['callSign']

    # Crear elementos <programme>
    for cid, chdata in channels.items():
        for event in chdata['events']:
            start_str = event.get('startTime', '').replace('-', '').replace(':', '').replace('T', '').replace('Z', ' +0000')
            stop_str = event.get('endTime', '').replace('-', '').replace(':', '').replace('T', '').replace('Z', ' +0000')

            prog = ET.SubElement(tv, 'programme', {
                'start': start_str,
                'stop': stop_str,
                'channel': cid
            })

            program_info = event.get('program', {})
            title = ET.SubElement(prog, 'title')
            title.text = program_info.get('title', 'Sin título')

            desc = ET.SubElement(prog, 'desc')
            desc.text = program_info.get('shortDesc', '')

    return ET.tostring(tv, encoding='utf-8', xml_declaration=True).decode('utf-8')

def pretty_xml(xml_str):
    """Formatea el XML con sangrías para que sea legible."""
    dom = xml.dom.minidom.parseString(xml_str)
    return dom.toprettyxml(indent="  ")

def save_xmltv(xml_str, filename="dish.xml"):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(xml_str)

def main():
    # Realizar fetches múltiples (5 fetches cubren ~6h + 4*5:50h ≈ 28.33 horas)
    # interval_seconds = 5*3600 + 50*60 = 5 horas 50 min en segundos
    all_epg_data = asyncio.run(fetch_multiple(num_fetches=5, interval_seconds=5*3600 + 50*60))
    
    # Fusionar datos
    merged_channels = merge_epg_data(all_epg_data)
    
    # Generar XML
    xmltv_str = channels_to_xmltv(merged_channels)
    xmltv_pretty = pretty_xml(xmltv_str)
    save_xmltv(xmltv_pretty)
    
    total_channels = len(merged_channels)
    total_programmes = sum(len(ch['events']) for ch in merged_channels.values())
    print(f"Archivo dish.xml generado correctamente.")
    print(f"Canales únicos: {total_channels}")
    print(f"Programas totales (sin duplicados): {total_programmes}")

if __name__ == "__main__":
    main()
