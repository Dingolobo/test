import requests
import json

# URL de la API
url = "https://epg-cdn.production-public.tubi.io/content/epg/programming?platform=web&device_id=55450647-2a0d-45ab-9d3b-8a8b15432f13&lookahead=1&content_id=400000156,400000122"

try:
    # Hacer la solicitud GET
    response = requests.get(url)
    
    # Verificar si la respuesta es exitosa
    if response.status_code == 200:
        # Convertir a JSON y imprimir formateado
        data = response.json()
        print(json.dumps(data, indent=2))
    else:
        print(f"Error HTTP: {response.status_code} - {response.status_text}")
except requests.exceptions.RequestException as e:
    print(f"Error en la solicitud: {e}")
