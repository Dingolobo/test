import requests
import json

# URL de la API
url = "https://epg-cdn.production-public.tubi.io/content/epg/programming?platform=web&device_id=55450647-2a0d-45ab-9d3b-8a8b15432f13&lookahead=1&content_id=400000156,400000122"

# Headers para simular un navegador (ajusta si es necesario)
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://tubi.tv/',  # O la URL de origen si sabes cuál es
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'cross-site',
}

try:
    # Hacer la solicitud GET con headers
    response = requests.get(url, headers=headers)
    
    # Verificar si la respuesta es exitosa
    if response.status_code == 200:
        # Convertir a JSON y imprimir formateado
        data = response.json()
        print(json.dumps(data, indent=2))
    else:
        print(f"Error HTTP: {response.status_code} - {response.statusText}")
except requests.exceptions.RequestException as e:
    print(f"Error en la solicitud: {e}")
