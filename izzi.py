import asyncio
from playwright.async_api import async_playwright

PAGE_URL = "https://www.izzi.mx/webApps/entretenimiento/guia"
FETCH_URL = "https://www.izzi.mx/webApps/entretenimiento/guia/getguia"

async def fetch_epg_with_playwright():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # Navegar a la página para cargar cookies y DOM
        await page.goto(PAGE_URL)

        # Extraer el token CSRF desde la meta tag
        csrf_token = await page.evaluate('''() => {
            const meta = document.querySelector('meta[name="_csrf"]');
            return meta ? meta.getAttribute('content') : "";
        }''')

        if not csrf_token:
            print("No se encontró el token CSRF")
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
            }}).then(res => res.json())
        ''')

        await browser.close()
        return epg_data

async def main():
    epg = await fetch_epg_with_playwright()
    if epg:
        for day in epg:
            print(f"Fecha: {day['date']}")
            for event in day['schedule']:
                print(f"  Título: {event['title']}")
                print(f"  Descripción: {event['description']}")
                print()

if __name__ == "__main__":
    asyncio.run(main())
