import asyncio
import requests
from playwright.async_api import async_playwright

URL = "https://www.izzi.mx/webApps/entretenimiento/guia/getguia"
PAGE_URL = "https://www.izzi.mx/webApps/entretenimiento/guia"

async def get_csrf_and_cookies():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto(PAGE_URL)

        # Extraer el valor del token x-csrf-token desde las cookies o localStorage
        # Aquí un ejemplo para extraerlo de las cookies:
        cookies = await context.cookies()
        csrf_token = None
        for cookie in cookies:
            if cookie['name'] == 'x-csrf-token':
                csrf_token = cookie['value']
                break

        # Si no está en cookies, intentar extraerlo del DOM o localStorage
        if not csrf_token:
            # Ejemplo: si está en localStorage
            csrf_token = await page.evaluate("localStorage.getItem('x-csrf-token')")

        # Extraer cookies para requests
        cookie_header = "; ".join([f"{c['name']}={c['value']}" for c in cookies])

        await browser.close()
        return csrf_token, cookie_header

def fetch_epg(csrf_token, cookie_header):
    headers = {
        "accept": "application/json",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "origin": "https://www.izzi.mx",
        "referer": PAGE_URL,
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
        "x-csrf-token": csrf_token,
        "x-requested-with": "XMLHttpRequest",
        "cookie": cookie_header,
        "cache-control": "no-cache",
    }
    data = ""  # Ajusta si es necesario

    response = requests.post(URL, headers=headers, data=data)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error {response.status_code}: {response.text}")
        return None

async def main():
    csrf_token, cookie_header = await get_csrf_and_cookies()
    if not csrf_token:
        print("No se pudo obtener el token CSRF")
        return
    epg = fetch_epg(csrf_token, cookie_header)
    if epg:
        for day in epg:
            print(f"Fecha: {day['date']}")
            for event in day['schedule']:
                print(f"  Título: {event['title']}")
                print(f"  Descripción: {event['description']}")
                print()

if __name__ == "__main__":
    asyncio.run(main())
