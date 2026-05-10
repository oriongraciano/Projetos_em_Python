import asyncio
import aiohttp
from urllib.parse import urljoin
from bs4 import BeautifulSoup

# Cabeçalho
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
    "Referer": "https://mangaratiba.nfe.com.br/iptu/guia.aspx",
    "Origin": "https://mangaratiba.nfe.com.br",
    "Cache-Control": "max-age=0",
}


async def buscar():

    url = "https://mangaratiba.nfe.com.br/iptu/guia.aspx"

    async with aiohttp.ClientSession(headers=HEADERS) as session:

        # GET Pagina inicial:
        async with session.get(url) as response:

            html = await response.text()

            pagina = BeautifulSoup(html, "html.parser")

            print(f"Titulo da Pagina: {pagina.title.text.strip()}")

            # Extração dos Tokens GET:
            viewstate = pagina.find("input", {"name": "__VIEWSTATE"})["value"]
            eventvalidation = pagina.find("input", {"name": "__EVENTVALIDATION"})[
                "value"
            ]
            viewstategenerator = pagina.find("input", {"name": "__VIEWSTATEGENERATOR"})[
                "value"
            ]

            # Paiload PostBack:
            payload_postback_insc = {
                "__LASTFOCUS": "",
                "__EVENTTARGET": "ctl00$cphCabMenu$CtrlContribuinte$tbInscricao",
                "__EVENTARGUMENT": "",
                "__VIEWSTATE": viewstate,
                "__VIEWSTATEGENERATOR": viewstategenerator,
                "__EVENTVALIDATION": eventvalidation,
                "ctl00$CAB$ddlNavegacaoRapida": "0",
                "ctl00$cphCabMenu$CtrlContribuinte$tbInscricao": "10365299",
            }

            # POST CAMPO INSCRIÇÃO:
            async with session.post(url, data=payload_postback_insc) as post2_response:

                resultado2 = await post2_response.text()

                with open("resultado_postback.html", "w", encoding="utf-8") as f:
                    f.write(resultado2)

                pagina2 = BeautifulSoup(resultado2, "html.parser")

                captcha_img2 = pagina2.find(
                    "img", src=lambda x: x and "CaptchaImage.aspx" in x
                )

                if captcha_img2:
                    captcha_src2 = captcha_img2.get("src")
                    captcha_url2 = urljoin(url, captcha_src2)
                    print(captcha_src2)
                else:
                    print("Captcha não encontrado")

                # Baixa o Capcha na raiz:
                async with session.get(captcha_url2) as captcha_response2:

                    captcha_bytes2 = await captcha_response2.read()

                    with open("captcha2.jpg", "wb") as f:
                        f.write(captcha_bytes2)

                print("\nNovo captcha salvo como captcha2.jpg")

                # Input do Captcha no terminal:
                captcha_digitado = (
                    input("\nDigite o captcha da imagem captcha2.jpg: ").strip().upper()
                )

                # Extração dos Tokens POST
                viewstate2 = pagina2.find("input", {"name": "__VIEWSTATE"})["value"]
                eventvalidation2 = pagina2.find("input", {"name": "__EVENTVALIDATION"})[
                    "value"
                ]
                viewstategenerator2 = pagina2.find(
                    "input", {"name": "__VIEWSTATEGENERATOR"}
                )["value"]
                captcha_codigo2 = pagina2.find(
                    "input", {"name": "ctl00$cphCabMenu$CaptchaControl$ccCodigo"}
                )["value"]

                # Paiload final
                payload_final = {
                    "__LASTFOCUS": "",
                    "__EVENTTARGET": "",
                    "__EVENTARGUMENT": "",
                    "__VIEWSTATE": viewstate2,
                    "__VIEWSTATEGENERATOR": viewstategenerator2,
                    "__EVENTVALIDATION": eventvalidation2,
                    "ctl00$CAB$ddlNavegacaoRapida": "0",
                    "ctl00$cphCabMenu$CtrlContribuinte$tbInscricao": "10365299",
                    "ctl00$cphCabMenu$CaptchaControl$tbCaptchaControl": captcha_digitado,
                    "ctl00$cphCabMenu$CaptchaControl$ccCodigo": captcha_codigo2,
                    "ctl00$cphCabMenu$CaptchaControl$hfCaptcha": "",
                    "ctl00$cphCabMenu$btConsultar": "Consultar",
                }

            # POST FORMULARIO:
            async with session.post(url, data=payload_final) as post_response:

                resultado = await post_response.text()

                print(f"Status code: {post_response.status}")

                print(post_response.url)

                print(post_response.history)
                
                if "não confere" in resultado.lower():
                    print("\nCaptcha inválido")

                elif "ADRIANA DA SILVA GOMES" in resultado:
                    print("\nCONSULTA REALIZADA COM SUCESSO")

                else:
                    print("\nResposta recebida mas resultado não identificado")

                with open("resultado_final.html", "w", encoding="utf-8") as f:
                    f.write(resultado)

                print("\nHTML salvo em resultado_final.html")


asyncio.run(buscar())
