import requests
import json

# URL del proxy (como en tu HTML)
url = 'https://cors-proxy.cooks.fyi/https://epg-cdn.production-public.tubi.io/content/epg/programming?platform=web&device_id=55450647-2a0d-45ab-9d3b-8a8b15432f13&lookahead=1&content_id=400000156,400000122'

# Headers copiados de tu captura (ajustados para requests)
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Accept-Language': 'es-419,es;q=0.9',
    'Cache-Control': 'no-cache',
    'Origin': 'https://dingolobo.github.io',  # Importante: tu sitio en Pages
    'Pragma': 'no-cache',
    'Priority': 'u=1, i',
    'Referer': 'https://dingolobo.github.io/',  # Importante: mismo que en la captura
    'Sec-Ch-Ua': '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Ch-Ua-Platform': '"Windows"',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'cross-site'
}

try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    print("Datos obtenidos:")
    print(json.dumps(data, indent=2))
    
    # Verificar si rows está vacío
    if not data.get('rows'):
        print("Advertencia: 'rows' está vacío. Posible detección de bot o falta de autenticación.")
    
    with open('tubi_data.json', 'w') as f:
        json.dump(data, f, indent=2)
except requests.exceptions.RequestException as e:
    print(f"Error en fetch: {e}")
