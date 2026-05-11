import asyncio
import aiohttp
import base64
import re
from PIL import Image
from io import BytesIO
from pathlib import Path
import os
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import pytesseract

# Cabeçalho:
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
            viewstategenerator = pagina.find("input", {"name": "__VIEWSTATEGENERATOR"})["value"]
            eventvalidation = pagina.find("input", {"name": "__EVENTVALIDATION"})["value"]

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
                "ctl00$cphCabMenu$CaptchaControl$tbCaptchaControl": "",
                "ctl00$cphCabMenu$CaptchaControl$ccCodigo": "",
            }

            # POST CAMPO INSCRIÇÃO:
            async with session.post(url, data=payload_postback_insc) as post2_response:

                resultado2 = await post2_response.text()

                pagina2 = BeautifulSoup(resultado2, "html.parser")


                # Inicio baixa o Capcha na raiz:
                captcha_img = pagina2.find(
                    "img", src=lambda x: x and "CaptchaImage.aspx" in x
                )

                if captcha_img:
                    captcha_src = captcha_img.get("src")
                    captcha_url = urljoin(url, captcha_src)
                    print(captcha_src)
                else:
                    print("Captcha não encontrado")
                
                async with session.get(captcha_url) as captcha_response2:

                    captcha_bytes = await captcha_response2.read()

                    with open("Captcha.jpg", "wb") as f:
                        f.write(captcha_bytes)

                print("\nCaptcha salvo como Captcha.jpg")
                # Final baixa o Capcha.


                # Input do Captcha no terminal:
                captcha_digitado = (
                    input("\nDigite o captcha da imagem Captcha.jpg: ").strip().upper()
                )

                # Extração dos Tokens POST:
                viewstate2 = pagina2.find("input", {"name": "__VIEWSTATE"})["value"]
                eventvalidation2 = pagina2.find("input", {"name": "__EVENTVALIDATION"})["value"]
                viewstategenerator2 = pagina2.find("input", {"name": "__VIEWSTATEGENERATOR"})["value"]

                # Paiload final:
                payload_final = {
                    "__LASTFOCUS": "",
                    "__EVENTTARGET": "",
                    "__EVENTARGUMENT": "",
                    "__VIEWSTATE": viewstate2,
                    "__VIEWSTATEGENERATOR": viewstategenerator2,
                    "__EVENTVALIDATION": eventvalidation2,
                    "ctl00$CAB$ddlNavegacaoRapida": "0",
                    "ctl00$cphCabMenu$CtrlContribuinte$tbInscricao": "10365299",
                    "ctl00$cphCabMenu$CaptchaControl$tbCaptchaControl": "",
                    "ctl00$cphCabMenu$CaptchaControl$ccCodigo": captcha_digitado,
                    "ctl00$cphCabMenu$btConsultar": "Consultar",
                }


            # POST FORMULARIO:
            async with session.post(url, data=payload_final) as post_response:

                resultado = await post_response.text()

                print(f"Status code: {post_response.status}")

                with open("resultado_final.html", "w", encoding="utf-8") as f:
                    f.write(resultado)

                print("\nHTML salvo resultado_final.html")

                # PEGANDO INFORMAÇÕES PROPRIETARIO:
                pagina_final = BeautifulSoup(resultado,"html.parser")

                nome_proprietario = pagina_final.find(
                    "span", {"id": "ctl00_cphCabMenu_lbNome"},
                    )    
                inscricao = pagina_final.find(
                    "span", {"id": "ctl00_cphCabMenu_lbInscricao"},
                    )
                numero_guia = pagina_final.find(
                    "span", {"id": "ctl00_cphCabMenu_lbGuia"},
                    )
                valor = pagina_final.find(
                    "span", {"id": "ctl00_cphCabMenu_lbValorCobranca"},
                    )
                data_vencimento = pagina_final.find(
                    "span", {"id": "ctl00_cphCabMenu_lbVencimento"},
                    )
                parcelas = pagina_final.find(
                    "span", {"id": "ctl00_cphCabMenu_lbParcelas"}
                )

                print("\n===== DADOS IPTU =====\n")

                print(f"Nome: {nome_proprietario.text.strip()}")

                print(f"Inscrição: {inscricao.text.strip()}")

                print(f"Guia: {numero_guia.text.strip()}")

                print(f"Valor: {valor.text.strip()}")

                print(f"Vencimento: {data_vencimento.text.strip()}")

                print(f"Parcelas: {parcelas.text.strip()}")


                # Extração dos Tokens Pagina Boleto:
                viewstate_boleto = pagina_final.find("input", {"name": "__VIEWSTATE"})["value"]
                viewstategenerator_boleto = pagina_final.find("input", {"name": "__VIEWSTATEGENERATOR"})["value"]
                eventvalidation_boleto = pagina_final.find("input", {"name": "__EVENTVALIDATION"})["value"]

                #Payload Pagina Boleto:
                payload_boleto = {
                    "__LASTFOCUS": "",
                    "__EVENTTARGET": "",
                    "__EVENTARGUMENT": "",
                    "__VIEWSTATE": viewstate_boleto,
                    "__VIEWSTATEGENERATOR": viewstategenerator_boleto,
                    "__EVENTVALIDATION": eventvalidation_boleto,
                    "ctl00$CAB$ddlNavegacaoRapida": "0",
                    "ctl00$cphCabMenu$ddlExercicio": "2026",
                    "ctl00$cphCabMenu$btParcelada": "Parcelas"
                }

            # Post Pagina Boleto:
            async with session.post(url, data=payload_boleto) as response_boleto:

                resultado_boleto = await response_boleto.text()
                
                print(f"Status code: {response_boleto.status}")

                pagina_boletos = BeautifulSoup(
                    resultado_boleto, "html.parser"
                )

                with open("resultadoPg_boleto.html", "w", encoding="utf-8") as f:
                    f.write(resultado_boleto)

                print("\nHTML salvo resultadoPg_boleto.html")


                #Baixa as Guias boleto e salva na pasta BoletosTemp:
                imagens_guias = pagina_boletos.find_all(
                    "img", 
                    id=re.compile(r".*imgGuia$") 
                )

                print(f"\nTotal de guias encontradas: {len(imagens_guias)}")

                for cont, img in enumerate(imagens_guias, start=1):

                    src = img.get("src", "")

                    if "base64," in src:
                        header, base64_data = src.split("base64,", 1)

                        imagem_bytes = base64.b64decode(base64_data)

                        imagem = Image.open(BytesIO(imagem_bytes))

                        base_dir = Path(__file__).resolve().parent
                        pasta_local = base_dir / "BoletosTemp"
                        os.makedirs(pasta_local, exist_ok=True)
                        nome_arquivo = f"Boleto_{cont}.png"
                        caminho_arquivos = pasta_local / nome_arquivo
                        imagem.save(caminho_arquivos, "PNG")

                        print(f"Guia salva: {nome_arquivo}")

                    else:
                        print("Imagem {cont} Invalida! Ou não esta em base64!")    
                

asyncio.run(buscar())
