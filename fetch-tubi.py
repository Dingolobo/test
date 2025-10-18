from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import json

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

# Iniciar el navegador
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

try:
    # Navegar directamente a tu HTML en GitHub Pages
    url = 'https://dingolobo.github.io/tubi_fetch.html'  # Ajusta el nombre del repo si es diferente
    print(f"Navegando a: {url}")
    driver.get(url)
    
    # Verificar carga
    print(f"Título de la página: {driver.title}")
    
    # Hacer clic en el botón
    button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, 'fetchBtn'))
    )
    button.click()
    print("Clic en botón realizado.")
    
    # Esperar unos segundos (ajusta si es necesario)
    time.sleep(25)
    
    # Capturar el resultado del <pre id="output">
    output_element = driver.find_element(By.ID, 'output')
    result_text = output_element.text
    print(f"Resultado capturado: '{result_text}'")
    
    if not result_text or result_text.startswith('Error'):
        print(f"Error o vacío: {result_text}")
    else:
        data = json.loads(result_text)
        print("Datos obtenidos:")
        print(json.dumps(data, indent=2))
        
        with open('tubi_data.json', 'w') as f:
            json.dump(data, f, indent=2)

finally:
    driver.quit()
