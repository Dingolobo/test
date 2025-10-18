from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import json
import os

# Configurar opciones para headless (útil en GitHub Actions)
options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')
options.add_argument('--window-size=1920,1080')  # Asegura tamaño de ventana

# Iniciar el navegador
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

try:
    # Ruta al HTML en la raíz del repo (modificación aquí)
    html_path = os.path.join(os.getcwd(), 'tubi_fetch.html')
    file_url = f'file://{html_path}'
    
    print(f"Cargando: {file_url}")
    driver.get(file_url)
    
    # Depuración: Imprimir título y verificar carga
    print(f"Título de la página: {driver.title}")
    time.sleep(2)  # Espera breve para carga completa
    
    # Verificar si el botón existe
    try:
        button = driver.find_element(By.ID, 'fetchBtn')
        print("Botón encontrado.")
    except:
        print("Botón NO encontrado. Guardando page_source para debug...")
        with open('debug_page.html', 'w') as f:
            f.write(driver.page_source)
        raise Exception("El botón 'fetchBtn' no se encontró en el DOM.")
    
    # Esperar y hacer clic
    button = WebDriverWait(driver, 20).until(  # Aumentado a 20s
        EC.element_to_be_clickable((By.ID, 'fetchBtn'))
    )
    button.click()
    print("Clic en botón realizado.")
    
    # Esperar resultado
    output_element = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.ID, 'output'))
    )
    
    result_text = output_element.text
    print(f"Resultado crudo: {result_text}")
    
    if result_text.startswith('Error'):
        print(f"Error en fetch: {result_text}")
    else:
        data = json.loads(result_text)
        print("Datos obtenidos:")
        print(json.dumps(data, indent=2))
        
        with open('tubi_data.json', 'w') as f:
            json.dump(data, f, indent=2)

finally:
    driver.quit()
