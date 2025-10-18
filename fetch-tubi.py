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

max_attempts = 3
attempt = 0
data = None

try:
    # Navegar directamente a tu HTML en GitHub Pages
    url = 'https://dingolobo.github.io/tubi_fetch.html'  # Ajusta el nombre del repo si es diferente
    print(f"Navegando a: {url}")
    driver.get(url)
    
    # Verificar carga
    print(f"Título de la página: {driver.title}")
    
    while attempt < max_attempts:
        attempt += 1
        print(f"Intento {attempt} de {max_attempts}")
        
        # Hacer clic en el botón
        button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'fetchBtn'))
        )
        button.click()
        print("Clic en botón realizado.")
        
        # Esperar 5 segundos
        time.sleep(25)
        
        # Capturar el resultado del <pre id="output">
        output_element = driver.find_element(By.ID, 'output')
        result_text = output_element.text
        print(f"Resultado capturado: '{result_text}'")
        
        if not result_text or result_text.startswith('Error'):
            print(f"Error o vacío en intento {attempt}: {result_text}")
            if attempt < max_attempts:
                print("Reintentando en 5 segundos...")
                time.sleep(3)
            continue
        
        # Intentar parsear JSON
        try:
            data = json.loads(result_text)
            if data.get('rows'):  # Si rows no está vacío, éxito
                print("Datos obtenidos con rows no vacío:")
                print(json.dumps(data, indent=2))
                break
            else:
                print(f"Rows vacío en intento {attempt}. Reintentando...")
                if attempt < max_attempts:
                    time.sleep(5)
        except json.JSONDecodeError:
            print(f"JSON inválido en intento {attempt}: {result_text}")
            if attempt < max_attempts:
                print("Reintentando en 5 segundos...")
                time.sleep(3)
    
    # Si terminó el loop sin éxito
    if not data or not data.get('rows'):
        print("Después de 3 intentos, rows sigue vacío o hubo error.")
    else:
        with open('tubi_data.json', 'w') as f:
            json.dump(data, f, indent=2)

finally:
    driver.quit()
