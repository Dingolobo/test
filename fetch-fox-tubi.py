import json
import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.parse import quote  # Para codificar params en URL
import sys
import time  # Para waits en Selenium

# Intenta importar Selenium/undetected-chromedriver; fallback a cloudscraper o requests
try:
    import undetected_chromedriver as uc
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    SELENIUM_AVAILABLE = True
    print("Selenium + undetected-chromedriver loaded: Full browser simulation for Akamai evasion.")
except ImportError:
    SELENIUM_AVAILABLE = False
    print("WARNING: Selenium not installed. Install with: pip install selenium undetected-chromedriver")
    try:
        import cloudscraper
        SCRAPER_AVAILABLE = True
        print("CloudScraper fallback loaded (may not evade Akamai).")
    except ImportError:
        import requests
        SCRAPER_AVAILABLE = False
        print("Plain requests fallback (likely to fail on Akamai). Install cloudscraper or selenium.")

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
    query_params = "&".join([f"{k}={quote(v)}" for k, v in PARAMS.items()])
    return f"{BASE_URL}?{query_params}"

def fetch_epg_data():
    """Fetch data using Selenium (Akamai evasion), fallback to cloudscraper/requests."""
    url = build_url()
    print(f"Fetching from URL: {url}")
    print(f"Using Selenium: {SELENIUM_AVAILABLE}, CloudScraper: {getattr(sys.modules, 'cloudscraper', False) is not None if 'cloudscraper' in globals() else False}")

    if SELENIUM_AVAILABLE:
        print("Using Selenium + undetected-chromedriver for Akamai evasion...")
        try:
            # Config Chrome options para headless y evasión
            options = Options()
            options.add_argument('--headless')  # Headless para Actions
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

            # Crea driver undetected
            driver = uc.Chrome(options=options, version_main=None)  # Auto-detecta Chrome version
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            print("Selenium: Navigating to URL...")
            driver.get(url)
            time.sleep(5)  # Wait para JS/challenges de Akamai

            # Obtén response (Selenium no tiene status directo, pero chequea page_source)
            page_source = driver.page_source
            print(f"Selenium Response Length: {len(page_source)} characters")
            print(f"Selenium Title: {driver.title}")  # Si es error, title podría ser "Error"

            if "Error" in driver.title or len(page_source) < 1000:
                print("Selenium: Detected possible Akamai block in page_source.")
                print(f"Page Source Snippet: {page_source[:500]}...")
                driver.quit()
                return None

            # Intenta extraer JSON de page_source (Akamai devuelve JSON directo si pasa)
            if page_source.strip().startswith('{'):
                data = json.loads(page_source)
                print("Selenium: JSON extracted from page_source.")
            else:
                print("Selenium: No JSON in page_source (possible redirect/block).")
                driver.quit()
                return None

            driver.quit()

            # Logs como antes
            print("SUCCESS: JSON parsed via Selenium.")
            print(f"JSON Top-Level Keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            rows = data.get('rows', [])
            print(f"Rows in JSON: {len(rows)}")
            if rows:
                first_row = rows[0]
                programs = first_row.get('programs', [])
                print(f"Programs in First Row: {len(programs)}")
                if programs:
                    first_program = programs[0]
                    print(f"Sample Title: {first_program.get('title', 'N/A')}")
            else:
                print(f"Full JSON (debug): {json.dumps(data, indent=2)}")

            return data

        except Exception as e:
            print(f"Selenium ERROR: {e}")
            print("  - Check Chrome installation or version mismatch.")
            return None

    # Fallback a cloudscraper si disponible
    elif 'cloudscraper' in globals() and SCRAPER_AVAILABLE:
        print("Fallback to CloudScraper...")
        # [Código de cloudscraper de la versión anterior, abreviado para espacio]
        try:
            scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False}, delay=10)
            # ... (resto igual que antes)
            # (Incluye el código completo de fetch con cloudscraper de mi respuesta anterior)
            # Para brevidad, asumo que lo copias de la versión previa
            pass  # Reemplaza con el bloque cloudscraper
        except Exception as e:
            print(f"CloudScraper ERROR: {e}")
            return None
    else:
        # Fallback requests (fallará)
        print("Fallback to requests (likely fail)...")
        # [Código requests de versiones anteriores]
        pass  # Reemplaza con requests.get

    return None  # Si todos fallan

# [Resto del script idéntico: parse_time, build_xmltv, save_xml, main - copia de la versión anterior]
# (Para ahorrar espacio, usa el build_xmltv y main de la respuesta con cloudscraper; son iguales)
