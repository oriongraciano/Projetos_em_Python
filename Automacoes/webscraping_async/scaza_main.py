import asyncio
import aiohttp
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/137.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Connection": "keep-alive",
}


async def buscar():

    url = "https://mangaratiba.nfe.com.br/iptu/guia.aspx"

    async with aiohttp.ClientSession(headers=HEADERS) as session:

        async with session.get(url) as response:

            html = await response.text()

            pagina = BeautifulSoup(html, "html.parser")

            print(f"Titulo da Pagina: {pagina.title.text.strip()}")

            img_captcha = pagina.find(
                "img", src=lambda x: x and "CaptchaImage.aspx" in x
            )

            if img_captcha:
                captcha_src = img_captcha.get("src")
                print("\nCaptcha Encontrado:")
                print(captcha_src)
            else:
                print("Imagem do Captcha não encontrado")

            viewstate = pagina.find("input", {"name": "__VIEWSTATE"})
            eventvalidation = pagina.find("input", {"name": "__EVENTVALIDATION"})
            viewstategenerator = pagina.find("input", {"name": "__VIEWSTATEGENERATOR"})

            print("\nVIEWSTATE:")
            print(viewstate["value"][:100])

            print("\nEVENTVALIDATION:")
            print(eventvalidation["value"][:100])

            print("\nVIEWSTATEGENERATOR:")
            print(viewstategenerator["value"])

            inputs = pagina.find_all("input")

            for input in inputs:
                print(
                    "\nNAME:",
                    input.get("name"),
                    "\nID:",
                    input.get("id"),
                    "\nTYPE:",
                    input.get("type"),
                    "\nVALUE",
                    input.get("value"),
                )


asyncio.run(buscar())
