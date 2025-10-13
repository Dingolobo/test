import asyncio
import re
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import sys
import os
import logging
import time
from playwright.async_api import async_playwright, TimeoutError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

INVALID_UUIDS = [
    "5cc95856-8487-406e-bb67-83f97d24ab5f",
    "2c841b16-71f5-4e68-886a-63678ae79fb0"
]
CHANNEL_URL_PREFIX = "https://edge.prod.ovp.ses.com:9443/xtv-ws-client/api/epgcache/list/"

CHANNEL_IDS = [306, 645, 701, 702, 703, 704, 705, 726, 727, 728, 734, 736, 741, 761, 762, 763, 764, 766, 769, 770, 771, 772, 801, 802, 803, 805, 806, 807, 808, 809, 814, 821, 822, 963, 964, 965, 1062, 1141, 1361, 1445, 1447,  1451]
OUTPUT_FILE = "mvshub.xml"

HEADERS_EPG = {
    'accept': 'application/xml, text/xml, */*',
    'accept-language': 'es-419,es;q=0.9',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'none',
    'cache-control': 'no-cache',
    'pragma': 'no-cache'
}

async def extract_valid_uuid():
    potential_uuids = []
    uuid_regex = re.compile(r"/list/([0-9a-fA-F\-]{36})/")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        async def handle_response(response):
            nonlocal potential_uuids
            url = response.url
            if url.startswith(CHANNEL_URL_PREFIX):
                match = uuid_regex.search(url)
                if match:
                    uuid = match.group(1)
                    if uuid in INVALID_UUIDS:
                        logger.info(f"UUID inválido detectado en URL: {uuid}, descartando...")
                    elif uuid not in potential_uuids:
                        potential_uuids.append(uuid)
                        logger.info(f"UUID potencial detectado en URL: {uuid}, recolectando para prueba...")

        page.on("response", handle_response)

        logger.info("Navegando a la página para extraer UUIDs potenciales...")
        await page.goto("https://www.mvshub.com.mx/#spa/epg")

        try:
            await page.wait_for_selector("div.page", timeout=10000)
            logger.info("Elemento clave cargado, página lista.")
        except TimeoutError:
            logger.warning("No se encontró el elemento clave, continuar igual.")

        # Scroll para forzar carga
        for y in range(0, 1000, 100):
            await page.evaluate(f"window.scrollTo(0, {y})")
            await asyncio.sleep(0.5)
        await page.evaluate("window.scrollTo(0, 0)")

        # Esperar 20 segundos para capturar más respuestas
        await page.wait_for_timeout(20000)

        await browser.close()

    logger.info(f"UUIDs potenciales recolectados: {len(potential_uuids)}")

    if not potential_uuids:
        logger.warning("No se recolectaron UUIDs potenciales.")
        return None

    # Computar fechas para la prueba (igual que en main)
    offset = int(os.environ.get('TIMEZONE_OFFSET', '0'))
    now = datetime.utcnow() + timedelta(hours=offset)
    date_from = int(now.timestamp() * 1000)
    date_to = int((now + timedelta(days=2)).timestamp() * 1000)

    # Probar cada UUID potencial con un fetch de prueba para canal 222
    session = requests.Session()
    session.headers.update(HEADERS_EPG)

    for uuid in potential_uuids:
        logger.info(f"Probando UUID potencial: {uuid} con fetch de canal 222...")
        test_contents = fetch_channel_contents(222, date_from, date_to, session, uuid)
        if test_contents and len(test_contents) > 0:
            logger.info(f"UUID válido confirmado: {uuid} (obtuvo {len(test_contents)} programas en prueba)")
            return uuid
        else:
            logger.warning(f"UUID {uuid} no válido (prueba fallida), probando siguiente...")

    logger.warning("Ningún UUID potencial resultó válido en las pruebas.")
    return None

async def run_with_retries(max_retries=8, retry_delay=3):
    for attempt in range(1, max_retries + 1):
        logger.info(f"Intento {attempt} para extraer UUID válido...")
        uuid = await extract_valid_uuid()
        if uuid:
            return uuid
        logger.warning(f"No se obtuvo UUID válido en intento {attempt}. Reintentando en {retry_delay}s...")
        await asyncio.sleep(retry_delay)
    return None

# --- Funciones fetch_channel_contents y build_xmltv iguales que antes ---
# (sin cambios, solo se usa en main y en la prueba de extract_valid_uuid)

def fetch_channel_contents(channel_id, date_from, date_to, session, uuid):
    url_base = f"https://edge.prod.ovp.ses.com:9443/xtv-ws-client/api/epgcache/list/{uuid}/" + "{}/220?page=0&size=100&dateFrom={}&dateTo={}"
    url = url_base.format(channel_id, date_from, date_to)
    logger.info(f"Fetching channel {channel_id} with UUID {uuid}: {url}")
    
    try:
        response = session.get(url, headers=HEADERS_EPG, timeout=15, verify=False)
        logger.info(f"Status for {channel_id}: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"Error for {channel_id}: {response.status_code} - {response.text[:300]}")
            return []
        
        if len(response.text.strip()) < 100:
            logger.warning(f"Empty response for {channel_id}: {response.text[:200]}")
            return []
        
        raw_file = f"raw_response_{channel_id}.xml"
        with open(raw_file, 'w', encoding='utf-8') as f:
            f.write(response.text)
        logger.info(f"Raw XML saved to {raw_file} (len: {len(response.text)} chars)")
        
        root = ET.fromstring(response.content)
        ns = "{http://ws.minervanetworks.com/}"
        contents = root.findall(f".//{ns}content")
        if not contents:
            all_children = [child.tag for child in root]
            logger.warning(f"No <content> found for {channel_id}. Root children: {all_children[:10]}. Snippet: {ET.tostring(root, encoding='unicode')[:300]}")
        else:
            logger.info(f"Found {len(contents)} programmes for channel {channel_id}")
        return contents
        
    except ET.ParseError as pe:
        logger.error(f"XML Parse error for {channel_id}: {pe} - Response: {response.text[:300]}")
        return []
    except Exception as e:
        logger.error(f"Exception for {channel_id}: {e}")
        return []

def build_xmltv(channels_data):
    if not channels_data:
        logger.warning("No data to build XMLTV - skipping")
        return False
    
    tv = ET.Element("tv", attrib={
        "generator-info-name": "MVS Hub Multi-Channel Dynamic 24h",
        "generator-info-url": "https://www.mvshub.com.mx/"
    })
    
    ns = "{http://ws.minervanetworks.com/}"
    channels = {}
    
    for channel_id, contents in channels_data:
        if not contents:
            continue
        
        first_content = contents[0]
        tv_channel = first_content.find(f".//{ns}TV_CHANNEL")
        call_sign = str(channel_id)
        number = ""
        logo_src = ""
        if tv_channel is not None:
            call_sign_elem = tv_channel.find(f"{ns}callSign")
            call_sign = call_sign_elem.text if call_sign_elem is not None else str(channel_id)
            number_elem = tv_channel.find(f"{ns}number")
            number = number_elem.text if number_elem is not None else ""
            # Logo del CANAL: Solo del <TV_CHANNEL><images>
            channel_images = tv_channel.findall(f".//{ns}images/{ns}image")
            if channel_images:
                channel_image = channel_images[0]  # Primera imagen del canal (logo)
                url_elem = channel_image.find(f"{ns}url")
                if url_elem is not None and url_elem.text:
                    logo_src = url_elem.text.strip()
                    logger.debug(f"Logo del canal {channel_id}: {logo_src}")
        else:
            logger.warning(f"No TV_CHANNEL in first content for {channel_id} - using defaults")
        
        if channel_id not in channels:
            channel = ET.SubElement(tv, "channel", id=str(channel_id))
            ET.SubElement(channel, "display-name").text = call_sign
            if number:
                ET.SubElement(channel, "display-name").text = number
            if logo_src:
                ET.SubElement(channel, "icon", src=logo_src)
            channels[channel_id] = True
            logger.info(f"Added channel {channel_id}: {call_sign} (number: {number}, logo: {logo_src})")
        
        for content in contents:
            start_elem = content.find(f"{ns}startDateTime")
            end_elem = content.find(f"{ns}endDateTime")
            if start_elem is None or end_elem is None:
                logger.warning(f"Missing start/end for programme in {channel_id} - skipping")
                continue
            try:
                start_ms = int(start_elem.text)
                end_ms = int(end_elem.text)
            except (ValueError, TypeError):
                logger.warning(f"Invalid start/end timestamp in {channel_id} - skipping programme")
                continue
            
            programme = ET.SubElement(tv, "programme", attrib={
                "start": datetime.utcfromtimestamp(start_ms / 1000).strftime("%Y%m%d%H%M%S") + " +0000",
                "stop": datetime.utcfromtimestamp(end_ms / 1000).strftime("%Y%m%d%H%M%S") + " +0000",
                "channel": str(channel_id)
            })
            
            title_elem = content.find(f"{ns}title")
            if title_elem is not None and title_elem.text:
                ET.SubElement(programme, "title", lang="es").text = title_elem.text
            else:
                ET.SubElement(programme, "title", lang="es").text = "Sin título"
            
            desc_elem = content.find(f"{ns}description")
            if desc_elem is not None and desc_elem.text:
                ET.SubElement(programme, "desc", lang="es").text = desc_elem.text
            
            genres = content.findall(f".//{ns}genres/{ns}genre/{ns}name")
            for genre in genres:
                if genre is not None and genre.text:
                    ET.SubElement(programme, "category", lang="es").text = genre.text

            # Episode Title como sub-title (compatible con XMLTV)
            episode_title_elem = content.find(f"{ns}episodeTitle")
            if episode_title_elem is not None and episode_title_elem.text:
                sub_title = ET.SubElement(programme, "sub-title", lang="es")
                sub_title.text = episode_title_elem.text

            # Season Number y Episode Number como episode-num (formato estándar XMLTV: S{season}E{episode})
            season_num_elem = content.find(f"{ns}seasonNumber")
            episode_num_elem = content.find(f"{ns}episodeNumber")
            if season_num_elem is not None and episode_num_elem is not None:
                season_text = season_num_elem.text
                episode_text = episode_num_elem.text
                if season_text and episode_text:
                    try:
                        episode_num_str = f"S{season_text}E{episode_text}"
                        ep_num = ET.SubElement(programme, "episode-num", system="xmltv_ns")
                        ep_num.text = episode_num_str
                    except (ValueError, TypeError):
                        pass  # Omitir si no se puede formatear

            # Rating de parentalLevel
            parental_level = content.find(f"{ns}parentalLevel")
            if parental_level is not None:
                rating_elem = parental_level.find(f"{ns}rating")
                if rating_elem is not None and rating_elem.text:
                    rating_container = ET.SubElement(programme, "rating")
                    value = ET.SubElement(rating_container, "value")
                    value.text = rating_elem.text

            # Org Air Date como date (fecha de estreno original)
            org_air_date_elem = content.find(f"{ns}orgAirDate")
            if org_air_date_elem is not None and org_air_date_elem.text:
                org_date_text = org_air_date_elem.text.strip()
                if org_date_text:
                    # Formatear como YYYYMMDD si es posible, o usar como está (e.g., "2020-07-01" -> "20200701")
                    try:
                        date_obj = datetime.strptime(org_date_text, "%Y-%m-%d")
                        formatted_date = date_obj.strftime("%Y%m%d")
                    except ValueError:
                        formatted_date = org_date_text  # Usar como está si no parsea
                    date_elem = ET.SubElement(programme, "date")
                    date_elem.text = formatted_date

            # Poster del programa: Primera <image><url> en <images> DEL CONTENT (no del TV_CHANNEL)
            # Buscar específicamente en las <images> del <content> actual (programme)
            content_images = content.findall(f"{ns}images/{ns}image")  # Sin .// para buscar directo en content
            if not content_images:
                # Fallback: Buscar descendientes si no está directo
                content_images = content.findall(f".//{ns}images/{ns}image")
            if content_images:
                first_image = content_images[0]  # Primera imagen del content (debería ser BROWSE o similar, poster)
                url_elem = first_image.find(f"{ns}url")
                if url_elem is not None and url_elem.text:
                    poster_src = url_elem.text.strip()
                    if poster_src and "logo" not in poster_src.lower():  # Evitar logos accidentales
                        icon = ET.SubElement(programme, "icon", src=poster_src)
                        logger.debug(f"Poster del programa en canal {channel_id}: {poster_src}")
                    else:
                        logger.debug(f"Imagen ignorada (posible logo): {poster_src}")
            else:
                logger.debug(f"No se encontró <images> en content para canal {channel_id}")
    
    rough_string = ET.tostring(tv, encoding='unicode', method='xml')
    reparsed = ET.fromstring(rough_string)
    ET.indent(reparsed, space="  ", level=0)
    tree = ET.ElementTree(reparsed)
    tree.write(OUTPUT_FILE, encoding="utf-8", xml_declaration=True)
    
    num_channels = len(channels)
    total_programmes = sum(len(contents) for _, contents in channels_data if contents)
    programmes_with_posters = sum(1 for _, contents in channels_data if contents for content in contents if content.findall(f".//{ns}images/{ns}image"))
    logger.info(f"XMLTV generado: {OUTPUT_FILE} ({num_channels} canales, {total_programmes} programas)")
    logger.info(f"Programas con posters: {programmes_with_posters}")
    return True

def main(uuid):
    global CHANNEL_IDS

    offset = int(os.environ.get('TIMEZONE_OFFSET', '0'))
    now = datetime.utcnow() + timedelta(hours=offset)
    date_from = int(now.timestamp() * 1000)
    date_to = int((now + timedelta(days=2)).timestamp() * 1000)

    if len(sys.argv) > 1:
        CHANNEL_IDS = [int(id.strip()) for id in sys.argv[1].split(',')]
    if 'CHANNEL_IDS' in os.environ:
        CHANNEL_IDS = [int(id.strip()) for id in os.environ['CHANNEL_IDS'].split(',')]

    if not CHANNEL_IDS:
        logger.error("No se proporcionaron canales.")
        return False

    logger.info(f"Canales: {CHANNEL_IDS}")
    logger.info(f"Usando UUID dinámico validado: {uuid}")

    session = requests.Session()
    session.headers.update(HEADERS_EPG)

    logger.info("=== TEST FETCH PARA CANAL 222 (debug final) ===")
    test_contents = fetch_channel_contents(222, date_from, date_to, session, uuid)
    if not test_contents:
        logger.error("Test fetch para 222 falló (0 programas) - Revisa logs.")
        return False
    else:
        logger.info(f"Test exitoso: {len(test_contents)} programas para 222 - Continuando con todos los canales.")

    channels_data = []
    logger.info("=== DESCARGANDO TODOS LOS CANALES ===")
    for channel_id in CHANNEL_IDS:
        logger.info(f"--- Descargando canal {channel_id} ---")
        contents = fetch_channel_contents(channel_id, date_from, date_to, session, uuid)
        channels_data.append((channel_id, contents))
        time.sleep(1)

    logger.info("=== GENERANDO XMLTV ===")
    success = build_xmltv(channels_data)
    if success:
        logger.info("¡Éxito! XMLTV generado correctamente.")
    else:
        logger.warning("Error al generar XMLTV o datos vacíos.")

    return success

if __name__ == "__main__":
    uuid = asyncio.run(run_with_retries())
    if uuid:
        main(uuid)
    else:
        logger.error("No se pudo extraer UUID válido tras varios intentos, abortando.")
