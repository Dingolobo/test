from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager  # Para manejar el driver automáticamente
import requests
import json
import time

# Configurar Chrome en modo headless (sin interfaz gráfica)
options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')
options.add_argument('--window-size=1920,1080')

# Iniciar el driver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

try:
    # Paso 1: Visitar el sitio de Tubi para iniciar sesión y obtener cookies frescas
    driver.get('https://tubi.tv/')
    time.sleep(5)  # Espera a que cargue y se generen cookies (ajusta si es necesario)

    # Paso 2: Hacer la solicitud a la API usando las cookies del navegador
    url = 'https://epg-cdn.production-public.tubi.io/content/epg/programming?platform=web&device_id=55450647-2a0d-45ab-9d3b-8a8b15432f13&lookahead=1&content_id=400000156,400000122'
    
    # Obtener cookies del navegador y convertirlas a dict para requests
    selenium_cookies = driver.get_cookies()
    cookies = {cookie['name']: cookie['value'] for cookie in selenium_cookies}
    
    # Headers básicos (puedes agregar más si es necesario)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
        'Accept': 'application/json',
    }
    
    # Solicitud con cookies frescas
    response = requests.get(url, headers=headers, cookies=cookies)
    
    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2))
    else:
        print(f"Error HTTP: {response.status_code} - {response.text}")

finally:
    driver.quit()  # Cerrar el navegador
