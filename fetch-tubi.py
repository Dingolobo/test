from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import json
import os

# Configurar opciones para headless
options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')
options.add_argument('--window-size=1920,1080')
options.add_argument('--disable-web-security')
options.add_argument('--allow-running-insecure-content')
options.add_argument('--ignore-certificate-errors')

# Iniciar el navegador con timeout mayor para scripts
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.set_script_timeout(60)  # Aumentar a 60 segundos

try:
    # Paso 1: Navegar a la página de live TV de Tubi para establecer sesión y cookies
    print("Navegando a Tubi Live para establecer sesión...")
    driver.get('https://tubitv.com/es-mx/live')
    time.sleep(5)
    
    # Aceptar cookies si aparece
    try:
        accept_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept') or contains(text(), 'Aceptar') or contains(text(), 'Aceptar todo')]"))
        )
        accept_button.click()
        print("Cookies aceptadas.")
        time.sleep(2)
    except:
        print("No se encontró botón de cookies o ya aceptadas.")
    
    # Paso 2: Cargar tu HTML desde GitHub Pages
    print("Cargando HTML desde GitHub Pages...")
    driver.get('https://dingolobo.github.io/tubi_fetch.html')  # Ajusta si el repo no es 'test'
    time.sleep(2)
    
    # Verificar carga
    print(f"Título de la página: {driver.title}")
    
    # Ejecutar el fetch via JS con callback
    js_code = """
    var callback = arguments[arguments.length - 1];
    fetchData().then(function(data) {
        callback(data);
    }).catch(function(error) {
        callback('Error: ' + error.message);
    });
    
    async function fetchData() {
        try {
            const response = await fetch('https://cors-proxy.cooks.fyi/https://epg-cdn.production-public.tubi.io/content/epg/programming?platform=web&device_id=55450647-2a0d-45ab-9d3b-8a8b15432f13&lookahead=1&content_id=400000156,400000122');
            if (!response.ok) {
                throw new Error(`Error HTTP: ${response.status}`);
            }
            const data = await response.json();
            document.getElementById('output').textContent = JSON.stringify(data, null, 2);
            return data;
        } catch (error) {
            document.getElementById('output').textContent = `Error: ${error.message}`;
            throw error;
        }
    }
    """
    
    result = driver.execute_async_script(js_code)
    print("Fetch ejecutado.")
    
    # Esperar resultado
    WebDriverWait(driver, 30).until(
        lambda d: d.find_element(By.ID, 'output').text.strip() != ""
    )
    
    output_element = driver.find_element(By.ID, 'output')
    result_text = output_element.text
    print(f"Resultado crudo: '{result_text}'")
    
    if not result_text or result_text.startswith('Error'):
        print(f"Error: {result_text}")
    else:
        data = json.loads(result_text)
        print("Datos obtenidos:")
        print(json.dumps(data, indent=2))
        
        with open('tubi_data.json', 'w') as f:
            json.dump(data, f, indent=2)

finally:
    driver.quit()
