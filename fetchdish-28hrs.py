import asyncio
import time
import xml.etree.ElementTree as ET
import xml.dom.minidom
from playwright.async_api import async_playwright
import json
import re  # Para manipular la URL del thumbnail

URL_TEMPLATE = ("https://tvlistings.gracenote.com/api/grid?"
                "lineupId=MEX-1008175-DEFAULT&timespan=6&headendId=1008175&country=MEX&timezone=&device=-"
                "&postalCode=&isOverride=true&pref=16,128&userId=-&aid=dishmex&languagecode=es-mx&time={timestamp}")

async def fetch_multiple(num_fetches=5, interval_seconds=21000):
    """Realiza múltiples fetches de EPG con timestamps incrementales."""
    base_ts = int(time.time())
    all_data = []
    pending_responses = {}  # url -> response object or None

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

        # Listener único para todas las respuestas (síncrono)
        def handle_response(response):
            response_url = response.url
            if any(url in response_url for url in pending_responses) and response.status == 200:
                # Encontrar la URL que coincide y almacenar el objeto response
                for pending_url in list(pending_responses.keys()):
                    if pending_url in response_url:
                        pending_responses[pending_url] = response
                        print(f"Respuesta capturada para {pending_url}")
                        break

        page.on("response", handle_response)

        for i in range(num_fetches):
            current_ts = base_ts + i * interval_seconds
            url = URL_TEMPLATE.format(timestamp=current_ts)
            pending_responses[url] = None  # Marcar como pendiente

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

            # Verificar si se capturó el response object
            if pending_responses[url] is not None:
                try:
                    # Ahora parsear el JSON en contexto async
                    response_obj = pending_responses[url]
                    response_text = await response_obj.text()
                    data = json.loads(response_text)
                    all_data.append(data)
                    print(f"Fetch {i+1} completado para timestamp {current_ts}.")
                except Exception as e:
                    print(f"Error parseando JSON para fetch {i+1}: {e}")
                    # Opcional: intentar con response.json() si text() falla
                    try:
                        data = await response_obj.json()
                        all_data.append(data)
                        print(f"Fetch {i+1} completado usando json() alternativo.")
                    except Exception as e2:
                        print(f"Error alternativo parseando JSON: {e2}")
                finally:
                    del pending_responses[url]  # Remover de pendientes
            else:
                print(f"Advertencia: No se obtuvo respuesta para fetch {i+1} ({url}). Continuando...")

            # Pequeña pausa entre fetches para evitar rate limiting
            if i < num_fetches - 1:
                await asyncio.sleep(2)

        await browser.close()

    # Verificar si hay pendientes al final
    if pending_responses:
        print(f"Advertencia: {len(pending_responses)} respuestas pendientes no capturadas.")

    if not all_data:
        raise Exception("No se pudo obtener ningún dato EPG")

    return all_data

def merge_epg_data(all_data):
    """Fusiona múltiples conjuntos de datos EPG, eliminando duplicados."""
    channels = {}  # channelId -> {'callSign': str, 'thumbnail': str, 'events': list}

    for data in all_data:
        for channel in data.get('channels', []):
            cid = channel.get('channelId', '')
            if not cid:
                continue

            if cid not in channels:
                thumbnail = channel.get('thumbnail', '')
                # Procesar la URL del thumbnail: agregar https: si es necesario y cambiar w=55 a w=256
                if thumbnail:
                    if thumbnail.startswith('//'):
                        thumbnail = 'https:' + thumbnail
                    # Reemplazar w=55 por w=256 usando regex para manejar posibles variaciones
                    thumbnail = re.sub(r'w=\d+', 'w=256', thumbnail)
                channels[cid] = {
                    'callSign': channel.get('callSign', 'SinNombre'),
                    'thumbnail': thumbnail,
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
        
        # Agregar icono si hay thumbnail
        thumbnail = chdata.get('thumbnail', '')
        if thumbnail:
            icon = ET.SubElement(ch, 'icon', src=thumbnail)

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
            title = ET.SubElement(prog, 'title', lang='es')
            title.text = program_info.get('title', 'Sin título')

            desc = ET.SubElement(prog, 'desc', lang='es')
            desc.text = program_info.get('shortDesc', '')

            # Poster del programa (thumbnail del event)
            event_thumbnail = event.get('thumbnail', '')#.replace()
            #event_thumbnail = event.get('thumbnail', '').replace('v8', 'h9').replace('v9', 'h9').replace('v10','h9') + '.jpg?w=600'
            if event_thumbnail:
                poster_url = f"https://zap2it.tmsimg.com/assets/{event_thumbnail}.jpg?w=600"
                icon = ET.SubElement(prog, 'icon', src=poster_url)

            # Rating
            rating = event.get('rating')
            if rating is not None and rating != '':
                rating_elem = ET.SubElement(prog, 'rating')
                value = ET.SubElement(rating_elem, 'value')
                value.text = str(rating)

            # Season y Episode (usando episode-num en formato XMLTV)
            season = program_info.get('season')
            episode = program_info.get('episode')
            if season is not None and episode is not None and season != '' and episode != '':
                try:
                    # Formato: S{season}E{episode} (estándar común para XMLTV)
                    episode_num = f"S{season}E{episode}"
                    ep_num_elem = ET.SubElement(prog, 'episode-num', system='xmltv_ns')
                    ep_num_elem.text = episode_num
                except (ValueError, TypeError):
                    pass  # Omitir si no se puede formatear

            # Episode Title (como sub-title)
            episode_title = program_info.get('episodeTitle')
            if episode_title and episode_title != '':
                sub_title = ET.SubElement(prog, 'sub-title', lang='es')
                sub_title.text = episode_title

            # Release Year (como date)
            release_year = program_info.get('releaseYear')
            if release_year is not None and release_year != '':
                date_elem = ET.SubElement(prog, 'date')
                date_elem.text = str(release_year)

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
    all_epg_data = asyncio.run(fetch_multiple(num_fetches=4, interval_seconds=5*3600 + 50*60))
    
    # Fusionar datos
    merged_channels = merge_epg_data(all_epg_data)
    
    # Generar XML
    xmltv_str = channels_to_xmltv(merged_channels)
    xmltv_pretty = pretty_xml(xmltv_str)
    save_xmltv(xmltv_pretty)
    
    total_channels = len(merged_channels)
    total_programmes = sum(len(ch['events']) for ch in merged_channels.values())
    channels_with_logos = sum(1 for ch in merged_channels.values() if ch.get('thumbnail'))
    programmes_with_posters = sum(1 for ch in merged_channels.values() for event in ch['events'] if event.get('thumbnail'))
    print(f"Archivo dish.xml generado correctamente.")
    print(f"Canales únicos: {total_channels}")
    print(f"Programas totales (sin duplicados): {total_programmes}")
    print(f"Canales con logos: {channels_with_logos}")
    print(f"Programas con posters: {programmes_with_posters}")

if __name__ == "__main__":
    main()
