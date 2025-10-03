import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

PAGE_URL = "https://www.izzi.mx/webApps/entretenimiento/guia"
FETCH_URL = "https://www.izzi.mx/webApps/entretenimiento/guia/getguia"

MAX_RETRIES = 2
WAIT_FOR_META_TIMEOUT = 15000  # ms

async def fetch_epg_with_retries():
    for attempt in range(1, MAX_RETRIES + 2):  # intentos: 1, 2, ..., MAX_RETRIES+1
        print(f"Intento {attempt} de {MAX_RETRIES + 1}")
        epg = await fetch_epg_once()
        if epg is not None:
            return epg
        print("Reintentando...\n")
    print("No se pudo obtener la guía EPG después de varios intentos.")
    return None

async def fetch_epg_once():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            await page.goto(PAGE_URL)
            # Esperar hasta 10 segundos a que la meta tag _csrf esté en el DOM
            await page.wait_for_selector('meta[name="_csrf"]', timeout=WAIT_FOR_META_TIMEOUT)
            csrf_token = await page.evaluate('''() => {
                const meta = document.querySelector('meta[name="_csrf"]');
                return meta ? meta.getAttribute('content') : "";
            }''')
            if not csrf_token:
                print("Token CSRF no encontrado en la meta tag.")
                await browser.close()
                return None

            # Ejecutar fetch con el token CSRF y cookies
            epg_data = await page.evaluate(f'''
                () => fetch("{FETCH_URL}", {{
                    method: "POST",
                    headers: {{
                        "accept": "application/json",
                        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
                        "x-requested-with": "XMLHttpRequest",
                        "x-csrf-token": "{csrf_token}",
                        "origin": "https://www.izzi.mx",
                        "referer": "{PAGE_URL}",
                    }},
                    body: "",
                    credentials: "include"
                }}).then(res => {{
                    if (!res.ok) throw new Error("HTTP " + res.status);
                    return res.json();
                }})
            ''')
            await browser.close()
            return epg_data

        except PlaywrightTimeoutError:
            print(f"Timeout esperando la meta tag _csrf (esperado {WAIT_FOR_META_TIMEOUT} ms).")
            await browser.close()
            return None
        except Exception as e:
            print(f"Error durante fetch: {e}")
            await browser.close()
            return None

async def main():
    epg = await fetch_epg_with_retries()
    if epg:
        for day in epg:
            print(f"Fecha: {day['date']}")
            for event in day['schedule']:
                print(f"  Título: {event['title']}")
                print(f"  Descripción: {event['description']}")
                print()

if __name__ == "__main__":
    asyncio.run(main())
