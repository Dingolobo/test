import requests

# URL para hacer fetch de la guía EPG
url = "https://www.izzi.mx/webApps/entretenimiento/guia/getguia"

# Headers necesarios para la petición POST
headers = {
    "accept": "application/json",
    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    "origin": "https://www.izzi.mx",
    "referer": "https://www.izzi.mx/webApps/entretenimiento/guia",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
    "x-csrf-token": "226ac7fd-51e8-42e2-a187-bfcf504de2c1",
    "x-requested-with": "XMLHttpRequest",
    "cache-control": "no-cache",
}

# Datos del cuerpo de la petición (puede estar vacío o con parámetros si se requieren)
data = ""  # Según la info, content-length es 20, puede ser un string vacío o algún parámetro simple

def fetch_epg():
    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        epg_data = response.json()
        return epg_data
    else:
        print(f"Error: Status code {response.status_code}")
        return None

if __name__ == "__main__":
    epg = fetch_epg()
    if epg:
        # Ejemplo: imprimir títulos y descripciones de la guía
        for day in epg:
            print(f"Fecha: {day['date']}")
            for event in day['schedule']:
                print(f"  Título: {event['title']}")
                print(f"  Descripción: {event['description']}")
                print(f"  Duración: {event['duration']} minutos")
                print()
