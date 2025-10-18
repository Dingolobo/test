import requests
import json

# URL de la API
url = 'https://epg-cdn.production-public.tubi.io/content/epg/programming?platform=web&device_id=55450647-2a0d-45ab-9d3b-8a8b15432f13&lookahead=1&content_id=400000156,400000122'

# Headers copiados del cURL
headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'es-419,es;q=0.9',
    'cache-control': 'no-cache',
    'pragma': 'no-cache',
    'priority': 'u=0, i',
    'sec-ch-ua': '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'none',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36'
}

# Cookies copiadas del cURL (parseadas a dict)
cookies = {
    'ak_bmsc': 'EE8822EB823554A8474878F0BCB08A1D~000000000000000000000000000000~YAAQjmEoF4CIRvOZAQAAGBaU9x0Wk/JAEGlubJCzsJtJDdVR+9EaOb2X9r7ZMvJ1kbR/VjI90SbS0x37oJJux+bgDj/OriDKMFP79xIp1LsXnz0LaLxMLb/2+bcfI84TlnDKwjMDRix9O9MkAGG0tC1/icWUuEgmeH/6i6XsblK1dazTBVgT1FEVstk4M6+an4Geb6uJ3OIonQzmunZIJL3i1BlEG26a/yg9hOuIW0tUTvhJsstqjfcD6cio+dKnEY6VUH7/gzU3eEYr6wqDrZUvaLUbMZRbL5vcCFp9Zg1YjodslM/VGZRMmsARmccYZI4e2Wi2Ha09eDuUKN7lRIqKx+GaQCdhQ6SRNyWL01Dqwixii5+IPzZPVhavBl2cNyec1x0BWgHAIiOY1Qk99lNcxI+f1yh1tw4=',
    'bm_sv': 'C9E9C3E89746757C3F7496D073BFD7DF~YAAQl6b3vVsgIueZAQAAdGWX9x09TfHnMLUi01TXqL+RZ1sIha+Ac5Lehf5GUWbDqcDwQnJE/s7EmLz3tEDLLsKsu+X1B+iSdQ7EEGy8m/XPkWKkzu7f8iJzIoZB27znQ9YTfvaW6qOTgDdTLC4dT1TWGfyTl72I/eB4PRrViUWCU0hd5fjdRWxjNhuHWlzByz0WQ9lWHOmiSQGqU3GZHFM2Bl9K+EHv4F3sdkBE3k/D8l+06dSvQxKnAE2q1lLhIDL+jOawJUxOTg/WemtU~1'
}

try:
    # Solicitud GET con headers y cookies
    response = requests.get(url, headers=headers, cookies=cookies)
    
    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2))
    else:
        print(f"Error HTTP: {response.status_code} - {response.text}")
except requests.exceptions.RequestException as e:
    print(f"Error en la solicitud: {e}")
