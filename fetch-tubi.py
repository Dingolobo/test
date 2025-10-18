from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import json
import os

# Configurar opciones para headless con permisos relajados
options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')
options.add_argument('--window-size=1920,1080')
options.add_argument('--disable-web-security')  # Permite requests cross-origin
options.add_argument('--allow-running-insecure-content')
options.add_argument('--ignore-certificate-errors')
options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')  # Simula navegador real

# Iniciar el navegador
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

try:
    # Ruta al HTML en la raíz del repo
    html_path = os.path.join(os.getcwd(), 'tubi_fetch.html')
    file_url = f'file://{html_path}'
    
    print(f"Cargando: {file_url}")
    driver.get(file_url)
    
    # Depuración: Imprimir título
    print(f"Título de la página: {driver.title}")
    time.sleep(2)
    
    # En lugar de hacer clic, ejecutar el JavaScript directamente para evitar problemas
    js_code = """
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
    return fetchData();
    """
    
    # Ejecutar el JS y esperar el resultado
    result = driver.execute_async_script(js_code)
    print("Fetch ejecutado via JS.")
    
    # Esperar a que el output se actualice
    WebDriverWait(driver, 30).until(
        lambda d: d.find_element(By.ID, 'output').text.strip() != ""
    )
    
    output_element = driver.find_element(By.ID, 'output')
    result_text = output_element.text
    print(f"Resultado crudo: '{result_text}'")
    
    # Guardar page_source para debug
    with open('debug_page_after_js.html', 'w') as f:
        f.write(driver.page_source)
    
    if not result_text or result_text.startswith('Error'):
        print(f"Error en fetch: {result_text}")
    else:
        data = json.loads(result_text)
        print("Datos obtenidos:")
        print(json.dumps(data, indent=2))
        
        with open('tubi_data.json', 'w') as f:
            json.dump(data, f, indent=2)

finally:
    driver.quit()
