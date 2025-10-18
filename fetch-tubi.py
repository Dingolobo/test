import requests
import json

# URL con el proxy CORS de tu HTML
url = 'https://cors-proxy.cooks.fyi/https://epg-cdn.production-public.tubi.io/content/epg/programming?platform=web&device_id=55450647-2a0d-45ab-9d3b-8a8b15432f13&lookahead=1&content_id=400000156,400000122'

# Agregar headers para simular un navegador (puede ayudar con restricciones)
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    print("Datos obtenidos:")
    print(json.dumps(data, indent=2))
    
    with open('tubi_data.json', 'w') as f:
        json.dump(data, f, indent=2)
except requests.exceptions.RequestException as e:
    print(f"Error en fetch: {e}")
