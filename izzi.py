import asyncio
from playwright.async_api import async_playwright

PAGE_URL = "https://www.izzi.mx/webApps/entretenimiento/guia"
FETCH_URL = "https://www.izzi.mx/webApps/entretenimiento/guia/getguia"

async def fetch_epg_with_playwright():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # Navegar a la página para que se establezcan cookies y tokens
        await page.goto(PAGE_URL)

        # Ejecutar fetch dentro del contexto del navegador
        epg_data = await page.evaluate(f'''
            () => fetch("{FETCH_URL}", {{
                method: "POST",
                headers: {{
                    "accept": "application/json",
                    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "x-requested-with": "XMLHttpRequest",
                    "x-csrf-token": window.__IZZI_CSRF_TOKEN || document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || "",
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
