from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import json

# Configurar opciones para headless (útil en servidores como GitHub Actions)
options = webdriver.ChromeOptions()
options.add_argument('--headless')  # Sin interfaz gráfica
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')

# Iniciar el navegador
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

try:
    # Cargar el HTML local (ajusta la ruta si es necesario)
    driver.get('file://' + 'tubi_fetch.html')  # Reemplaza con la ruta absoluta

    # Hacer clic en el botón
    button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, 'fetchBtn'))
    )
    button.click()

    # Esperar a que se cargue el resultado en <pre id="output">
    output_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, 'output'))
    )
    
    # Extraer el texto (JSON)
    result_text = output_element.text
    if result_text.startswith('Error'):
        print(f"Error en fetch: {result_text}")
    else:
        # Parsear y procesar el JSON
        data = json.loads(result_text)
        print("Datos obtenidos:")
        print(json.dumps(data, indent=2))
        
        # Aquí puedes guardar a un archivo o procesar más
        with open('tubi_data.json', 'w') as f:
            json.dump(data, f, indent=2)

finally:
    driver.quit()
