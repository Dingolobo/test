from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import json
import time

# Configurar Chrome en modo headless
options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')
options.add_argument('--window-size=1920,1080')

# Iniciar el driver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

try:
    # Paso 1: Visitar el sitio de Tubi para iniciar sesión y obtener cookies/context
    driver.get('https://tubi.tv/')
    time.sleep(5)  # Espera a que cargue (ajusta si es necesario)

    # Opcional: Navega a una página específica de Tubi para más contexto (ej. una página de contenido)
    # driver.get('https://tubi.tv/live')  # Prueba si ayuda; ajusta la URL
    # time.sleep(3)

    # Paso 2: Navegar a la URL de la API directamente con el navegador
    url = 'https://epg-cdn.production-public.tubi.io/content/epg/programming?platform=web&device_id=55450647-2a0d-45ab-9d3b-8a8b15432f13&lookahead=1&content_id=400000156,400000122'
    driver.get(url)

    # Espera a que cargue la respuesta (el JSON)
    time.sleep(3)

    # Paso 3: Extraer el JSON de la página (debería estar en el body o como texto plano)
    page_source = driver.page_source
    # Asume que el JSON está en el body; si no, busca en <pre> o scripts
    if '<pre>' in page_source:
        # Extrae de <pre> si se muestra formateado
        start = page_source.find('<pre>') + 5
        end = page_source.find('</pre>')
        json_text = page_source[start:end]
    else:
        # Si es JSON plano, usa el body
        json_text = page_source.strip()

    # Parsear y imprimir
    data = json.loads(json_text)
    print(json.dumps(data, indent=2))

finally:
    driver.quit()
