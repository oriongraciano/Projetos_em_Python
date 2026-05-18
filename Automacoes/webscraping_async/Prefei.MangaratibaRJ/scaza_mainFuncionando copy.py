from shared_code.driver_response import DataResponse
from shared_code.upload_boleto import subir_boleto_azure
from aiohttp import compression_utils
import asyncio
import aiohttp
import base64
import logging
import re
from io import BytesIO
from pathlib import Path
from urllib.parse import urljoin
import os
import io
from bs4 import BeautifulSoup
from shared_code.solver_captcha.base_solver import BaseCaptchaSolver
from shared_code.driver_response import *
from shared_code import formatter
from PIL import Image, ImageEnhance
import pytesseract
import fitz


TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
TEMP_DEBUG_DIR = r"debug_ocr"
OCR_LANG = "por+eng"
OCR_CONFIG = "--psm 6"

ESCALA = 3

pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

URL = "https://mangaratiba.nfe.com.br/iptu/guia.aspx"

TIMEOUT = aiohttp.ClientTimeout(total=60)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/137.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,image/avif,image/webp,/;q=0.8"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Connection": "keep-alive",
    "Referer": "https://mangaratiba.nfe.com.br/iptu/guia.aspx",
    "Origin": "https://mangaratiba.nfe.com.br",
    "Cache-Control": "max-age=0",
}


INSCRICAO = "10365299"


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


def salvar_html(nome_arquivo, conteudo):

    with open(nome_arquivo, "w", encoding="utf-8") as f:
        f.write(conteudo)

    logger.info(f"HTML salvo: {nome_arquivo}")


def extrair_tokens(pagina):

    return {
        "__VIEWSTATE": pagina.find("input", {"name": "__VIEWSTATE"})["value"],
        "__VIEWSTATEGENERATOR": pagina.find("input", {"name": "__VIEWSTATEGENERATOR"})[
            "value"
        ],
        "__EVENTVALIDATION": pagina.find("input", {"name": "__EVENTVALIDATION"})[
            "value"
        ],
    }


def extrair_texto(soup, tag_id):

    elemento = soup.find("span", {"id": tag_id})

    if not elemento:
        return None

    return elemento.text.strip()


async def request_with_retry(session, method, url, retries=3, delay=2, **kwargs):

    for tentativa in range(1, retries + 1):

        try:

            async with session.request(method, url, **kwargs) as response:

                response.raise_for_status()

                logger.info(f"{method} {url} | Status: {response.status}")

                return await response.text()

        except Exception as e:

            logger.warning(f"Tentativa {tentativa} falhou: {e}")

            if tentativa == retries:

                logger.error("Número máximo de tentativas atingido")

                raise

            await asyncio.sleep(delay)


async def resolver_captcha(session, pagina):

    captcha_img = pagina.find("img", src=lambda x: x and "CaptchaImage.aspx" in x)

    if not captcha_img:

        logger.error("Captcha não encontrado")

        return None

    captcha_src = captcha_img.get("src")

    captcha_url = urljoin(URL, captcha_src)

    logger.info(f"Captcha URL: {captcha_url}")

    async with session.get(captcha_url) as response:

        captcha_bytes = await response.read()

    return captcha_bytes


async def get_catpcha(session, url, solver_captcha: BaseCaptchaSolver):
    async with session.get(url) as captcha:
        logging.info("resolvendo captcha")
        captcha = solver_captcha.break_captcha(await captcha.read())
    logging.info(f"captcha resolvido: {captcha}")

    return captcha


def salvar_boletos(pagina_boletos):

    imagens_guias = pagina_boletos.find_all("img", id=re.compile(r".*imgGuia$"))

    logger.info(f"Total de guias encontradas: {len(imagens_guias)}")

    boletos_pdf = []

    for cont, img in enumerate(imagens_guias, start=1):

        src = img.get("src", "")

        if "base64," not in src:

            logger.warning(f"Guia {cont} inválida")

            continue

        try:

            _, base64_data = src.split("base64,", 1)

            imagem_bytes = base64.b64decode(base64_data)

            imagem = Image.open(BytesIO(imagem_bytes))

            imagem = imagem.convert("RGB")

            pdf_buffer = BytesIO()

            imagem.save(pdf_buffer, format="PDF")

            pdf_buffer.seek(0)

            pdf_bytes = pdf_buffer.getvalue()

            logger.info(f"Tamanho PDF guia {cont}: {len(pdf_bytes)} bytes")

            boletos_pdf.append({"nome": f"boleto_{cont}.pdf", "bytes": pdf_bytes})

            logger.info(f"Guia carregada memória: boleto_{cont}.pdf")

        except Exception as e:

            logger.error(f"Erro ao salvar guia {cont}: {e}")

    return boletos_pdf


async def load_data(session, conta, scaza_logger):

    parsed_data = ParsedDataList()

    formater = formatter.only_digits(INSCRICAO)

    logger.info("Acessando página inicial")

    html = await request_with_retry(session, "GET", URL)

    pagina = BeautifulSoup(html, "html.parser")

    logger.info(f"Título da página: {pagina.title.text.strip()}")

    tokens = extrair_tokens(pagina)

    logger.info(f"Enviando inscrição: {INSCRICAO}")

    payload_postback_insc = {
        "__LASTFOCUS": "",
        "__EVENTTARGET": "ctl00$cphCabMenu$CtrlContribuinte$tbInscricao",
        "__EVENTARGUMENT": "",
        "__VIEWSTATE": tokens["__VIEWSTATE"],
        "__VIEWSTATEGENERATOR": tokens["__VIEWSTATEGENERATOR"],
        "__EVENTVALIDATION": tokens["__EVENTVALIDATION"],
        "ctl00$CAB$ddlNavegacaoRapida": "0",
        "ctl00$cphCabMenu$CtrlContribuinte$tbInscricao": INSCRICAO,
        "ctl00$cphCabMenu$CaptchaControl$tbCaptchaControl": "",
        "ctl00$cphCabMenu$CaptchaControl$ccCodigo": "",
    }

    resultado2 = await request_with_retry(
        session, "POST", URL, data=payload_postback_insc
    )

    pagina2 = BeautifulSoup(resultado2, "html.parser")

    captcha = await resolver_captcha(session, pagina2)

    if not captcha:

        logger.error("Falha ao resolver captcha")

        return

    tokens2 = extrair_tokens(pagina2)

    logger.info("Consultando débitos")

    payload_final = {
        "__LASTFOCUS": "",
        "__EVENTTARGET": "",
        "__EVENTARGUMENT": "",
        "__VIEWSTATE": tokens2["__VIEWSTATE"],
        "__VIEWSTATEGENERATOR": tokens2["__VIEWSTATEGENERATOR"],
        "__EVENTVALIDATION": tokens2["__EVENTVALIDATION"],
        "ctl00$CAB$ddlNavegacaoRapida": "0",
        "ctl00$cphCabMenu$CtrlContribuinte$tbInscricao": INSCRICAO,
        "ctl00$cphCabMenu$CaptchaControl$tbCaptchaControl": "",
        "ctl00$cphCabMenu$CaptchaControl$ccCodigo": captcha,
        "ctl00$cphCabMenu$btConsultar": "Consultar",
    }

    resultado = await request_with_retry(session, "POST", URL, data=payload_final)

    salvar_html("resultado_final.html", resultado)

    pagina_final = BeautifulSoup(resultado, "html.parser")

    logger.info("Dados IPTU encontrados")

    dados = {
        "Nome": extrair_texto(pagina_final, "ctl00_cphCabMenu_lbNome"),
        "Inscrição": extrair_texto(pagina_final, "ctl00_cphCabMenu_lbInscricao"),
        "Guia": extrair_texto(pagina_final, "ctl00_cphCabMenu_lbGuia"),
        "Valor": extrair_texto(pagina_final, "ctl00_cphCabMenu_lbValorCobranca"),
        "Vencimento": extrair_texto(pagina_final, "ctl00_cphCabMenu_lbVencimento"),
        "Parcelas": extrair_texto(pagina_final, "ctl00_cphCabMenu_lbParcelas"),
    }

    logger.info("===== DADOS IPTU =====")

    for chave, valor in dados.items():

        logger.info(f"{chave}: {valor}")

    tokens_boleto = extrair_tokens(pagina_final)

    logger.info("Solicitando boletos parcelados")

    payload_boleto = {
        "__LASTFOCUS": "",
        "__EVENTTARGET": "",
        "__EVENTARGUMENT": "",
        "__VIEWSTATE": tokens_boleto["__VIEWSTATE"],
        "__VIEWSTATEGENERATOR": tokens_boleto["__VIEWSTATEGENERATOR"],
        "__EVENTVALIDATION": tokens_boleto["__EVENTVALIDATION"],
        "ctl00$CAB$ddlNavegacaoRapida": "0",
        "ctl00$cphCabMenu$ddlExercicio": "2026",
        "ctl00$cphCabMenu$btParcelada": "Parcelas",
    }

    resultado_boleto = await request_with_retry(
        session, "POST", URL, data=payload_boleto
    )

    salvar_html("resultadoPg_boleto.html", resultado_boleto)

    pagina_boletos = BeautifulSoup(resultado_boleto, "html.parser")

    boletos = salvar_boletos(pagina_boletos)

    logger.info("Processo finalizado com sucesso")

    logger.info("Iniciando o Processamento OCR dos boletos")

    resultado_ocr = processar_todos_boletos(boletos)

    for guia in resultado_ocr:

        try:

            if guia["paga"]:
                logger.info(f"Parcela {guia['parcela']} ignorada (PAGA)")
                continue

            valor = guia.get("valor")

            if not valor:

                logger.warning(f"Parcela {guia['parcela']} ignorada: valor vazio")

                continue

            valor_float = float(valor.replace(".", "").replace(",", ".").strip())

            dados_parcela = {
                "codigo": guia["parcela"],
                "vencimento": guia["vencimento"],
                "valor": valor_float,
                "informacoes_adicionais": f"Parcela: {guia['parcela']}",
            }

            if guia.get("linha_digitavel"):
                dados_parcela["barcode"] = formatter.only_digits(
                    guia.get("linha_digitavel")
                )

            pdf_bytes = guia.get("boleto_pdf_bytes")

            if pdf_bytes:
                link_boleto, data_boleto = await subir_boleto_azure(
                    conta["id"], "iptumangaratibarj", pdf_bytes
                )
                dados_parcela["link_boleto"] = link_boleto
                dados_parcela["data_boleto"] = data_boleto

            parsed_data.add(**dados_parcela)

        except Exception as e:

            logger.error(f"Erro ao adicionar parcela: {e}")

    logger.info(f"Total débitos encontrados: {len(parsed_data.get_list())}")
    print("=" * 38)

    return DataResponse(
        debts=parsed_data.get_list(), receipt=DataReceipt(boletos, DataType.PDF)
    )


def preprocessar_para_ocr(imagem: Image.Image) -> Image.Image:
    """Pipeline de pré-processamento da imagem embutida para OCR."""

    imagem = imagem.convert("RGB")

    enhancer = ImageEnhance.Contrast(imagem)
    imagem = enhancer.enhance(1.0)

    largura, altura = imagem.size
    imagem = imagem.resize((largura * ESCALA, altura * ESCALA))

    imagem = imagem.convert("L")
    imagem = imagem.point(lambda x: 0 if x < 160 else 255, "1")

    return imagem


def detectar_inicio_guias(imagem: Image.Image) -> list[int]:
    """
    Detecta automaticamente a coordenada Y de início de cada guia
    localizando 'Parcela XX/XX' via image_to_data na coluna esquerda.

    Retorna lista de Y em pixels da imagem original.
    """

    W, H = imagem.size
    col_esq = imagem.crop((0, 0, W // 2, H))
    proc = preprocessar_para_ocr(col_esq)

    data = pytesseract.image_to_data(
        proc, lang=OCR_LANG, output_type=pytesseract.Output.DICT
    )

    inicios_y = []

    for i, word in enumerate(data["text"]):

        texto_word = word.strip().lower()

        if "parcela" not in texto_word:
            continue

        contexto = " ".join(data["text"][max(0, i - 5) : i + 8])

        contexto = contexto.replace("\n", " ")

        # aceita OCR residual
        if not re.search(r"parcela.{0,10}[\dgG]{2}", contexto, re.IGNORECASE):
            continue

        y_original = data["top"][i] // ESCALA

        if not inicios_y or (y_original - inicios_y[-1]) > 50:
            inicios_y.append(y_original)

    return inicios_y


def extrair_dados_boleto(texto_esq: str, texto_full: str) -> dict | None:
    """
    Extrai os campos de UMA guia a partir de dois textos OCR:
      - texto_esq  : coluna esquerda — parcela, vencimento, valor, status paga
      - texto_full : largura total   — linha digitável
    Campos extraídos:
      - parcela        : "05/09"
      - vencimento     : "30/06/2026"
      - valor          : "53,18"
      - linha_digitavel: "81640000000-5 ..."
      - paga           : True se parcela já foi paga
    """

    if "Parcela" not in texto_esq:
        return None

    dados = {}

    # Parcela
    # Com recorte por guia: lê "05/09" limpo
    # Residual OCR: "0509", "G5/09"
    total_parcelas_fixo = "09"
    m = re.search(r"Parcela\s+(\d{2})[/](\d{2})", texto_esq)
    if m:
        num_parcela = m.group(1)
        dados["parcela"] = f"{num_parcela}/{total_parcelas_fixo}"
    else:
        dados["parcela"] = None

    # Paga
    dados["paga"] = bool(re.search(r"Parcela\s+Paga\s+em", texto_esq, re.IGNORECASE))

    # Vencimento
    # Real: "30/06/2026" | OCR residual: "3046/2026", "30N6/2026"
    m = re.search(
        r"Venc[ia]mento.{0,40}?(\d{2})\D{0,2}(\d{2})\D{0,2}(20\d{2})",
        texto_esq,
        re.DOTALL,
    )
    if m:
        dados["vencimento"] = f"{m.group(1)}/{m.group(2)}/{m.group(3)}"
    else:
        m2 = re.search(r"\b(\d{2})/(\d{2})/(20\d{2})\b", texto_esq)
        dados["vencimento"] = (
            f"{m2.group(1)}/{m2.group(2)}/{m2.group(3)}" if m2 else None
        )

    #  Valor
    # Prioriza após label "Valor (R$)"
    m = re.search(r"Valor\s*\(R\$\).{0,30}?(\d{1,4}),(\d{2})\b", texto_esq, re.DOTALL)
    if not m:
        m = re.search(r"\b(\d{1,4}),(\d{2})\b", texto_esq)
    dados["valor"] = f"{m.group(1)},{m.group(2)}" if m else None

    #  Linha digitável — busca no recorte de largura total
    # Padrão: 4 grupos numéricos com traço separados por espaço
    # ex: "81640000000-5  53182531202-2  60630971100-4  01607804052-0"
    m = re.search(
        r"(\d{8,12}-?\d[\s,]+\d{8,12}-?\d[\s,]+\d{8,12}-?\d[\s,]+\d{8,12}-?\d)",
        texto_full,
    )
    dados["linha_digitavel"] = re.sub(r"\s+", " ", m.group(1)).strip() if m else None

    if not dados["vencimento"] and not dados["valor"]:
        return None

    return dados


def processar_boleto(pdf_bytes, nome_arquivo="boleto"):
    """
    Extrai imagem do PDF via fitz, detecta Y de cada guia e aplica
    dois recortes por guia:
      - coluna esquerda : parcela, vencimento, valor, status
      - largura total   : linha digitável
    """

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    imagens = doc[0].get_images(full=True)

    if not imagens:
        logger.warning("Nenhuma imagem encontrada")
        return []

    xref = imagens[0][0]
    imagem = Image.open(io.BytesIO(doc.extract_image(xref)["image"])).convert("RGB")

    W, H = imagem.size
    col_x = int(W * 0.35)

    # Detecta Y de início de cada guia automaticamente
    inicios_y = detectar_inicio_guias(imagem)

    if not inicios_y:
        print(f"  [AVISO] Nenhuma guia detectada em {nome_arquivo}")
        return []

    os.makedirs(TEMP_DEBUG_DIR, exist_ok=True)
    todas_guias = []

    for i, y0 in enumerate(inicios_y):

        y_inicio = max(0, y0 - 30)
        y_fim = inicios_y[i + 1] - 30 if i + 1 < len(inicios_y) else H

        # ── Recorte 1: coluna esquerda — parcela, vencimento, valor
        recorte_esq = imagem.crop((0, y_inicio, col_x, y_fim))
        proc_esq = preprocessar_para_ocr(recorte_esq)
        texto_esq = pytesseract.image_to_string(
            proc_esq, lang=OCR_LANG, config=OCR_CONFIG
        )

        # # ── Recorte 2: largura total — linha digitável
        # recorte_full = imagem.crop(
        #     (int(W * 0.30), y_inicio + 145, W, min(y_inicio + 340, y_fim))

        # ── Recorte 2: largura total — linha digitável
        # Calculamos as coordenadas com travas de segurança (clamping)
        y_linha_inicio = y_inicio + 145
        y_linha_fim = min(y_inicio + 340, y_fim)

        # Blindagem: Se o cálculo estourar ou a guia for muito curta,
        # garantimos que o 'lower' (fim) seja sempre maior que o 'upper' (início)
        if y_linha_inicio >= y_linha_fim:
            # Em guias muito pequenas, pegamos uma fatia fixa de 100px a partir do topo detectado
            y_linha_inicio = max(0, y_linha_fim - 100)

        recorte_full = imagem.crop(
            (int(W * 0.30), int(y_linha_inicio), int(W), int(y_linha_fim))
        )

        proc_full = preprocessar_para_ocr(recorte_full)
        texto_full = pytesseract.image_to_string(
            proc_full, lang=OCR_LANG, config=OCR_CONFIG
        )

        # # Debug — salva ambos os recortes e textos
        # proc_esq.save(
        #     os.path.join(TEMP_DEBUG_DIR, f"debug_{nome_arquivo}_guia{i+1}_esq.png")
        # )
        # proc_full.save(
        #     os.path.join(TEMP_DEBUG_DIR, f"debug_{nome_arquivo}_guia{i+1}_full.png")
        # )

        # with open(
        #     os.path.join(TEMP_DEBUG_DIR, f"debug_{nome_arquivo}_guia{i+1}_esq.txt"),
        #     "w",
        #     encoding="utf-8",
        # ) as f:
        #     f.write(texto_esq)
        # with open(
        #     os.path.join(TEMP_DEBUG_DIR, f"debug_{nome_arquivo}_guia{i+1}_full.txt"),
        #     "w",
        #     encoding="utf-8",
        # ) as f:
        #     f.write(texto_full)

        dados = extrair_dados_boleto(texto_esq, texto_full)
        if dados:
            todas_guias.append(dados)

    return todas_guias


def processar_todos_boletos(lista_boletos):

    resultado = []

    for boleto in lista_boletos:

        nome = boleto["nome"]

        pdf_bytes = boleto["bytes"]

        logger.info(f"\n{'='*38}")
        logger.info(f"  Processando: {nome}")
        logger.info(f"{'='*38}")

        guias = processar_boleto(pdf_bytes, nome)

        for guia in guias:
            guia["boleto_pdf_bytes"] = pdf_bytes

        if not guias:
            logger.info(f"Nenhuma guia extraida")
            continue

        resultado.extend(guias)

        for i, guia in enumerate(guias, start=1):
            status = "PAGA" if guia["paga"] else "ABERTA"
            logger.info(f"\n  Guia {i} [{status}]")
            logger.info(f"    Parcela        : {guia['parcela']}")
            logger.info(f"    Vencimento     : {guia['vencimento']}")
            logger.info(f"    Valor (R$)     : {guia['valor']}")
            logger.info(f"    Linha Digitável: {guia['linha_digitavel']}")

    return resultado
