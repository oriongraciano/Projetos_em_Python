from PIL import Image, ImageEnhance
import cv2
import numpy as np
import pytesseract
import fitz
import re
import io
import os

TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
TEMP_DEBUG_DIR = r"debug_ocr"
BOLETOS_DIR = "BoletosTemp"

OCR_LANG = "por+eng"
OCR_CONFIG = "--psm 11"

ESCALA = 3

pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD


def preprocessar_para_ocr(imagem: Image.Image) -> Image.Image:
    """
    Pipeline OCR:
    usado SOMENTE para:
      - parcela
      - vencimento
      - valor
      - status paga
    """

    imagem = imagem.convert("RGB")

    enhancer = ImageEnhance.Contrast(imagem)

    imagem = enhancer.enhance(4.0)

    largura, altura = imagem.size

    imagem = imagem.resize((largura * ESCALA, altura * ESCALA))

    imagem = imagem.convert("L")

    imagem = imagem.point(lambda x: 0 if x < 160 else 255, "1")

    return imagem


def preprocessar_barcode(imagem: Image.Image) -> Image.Image:
    """
    Pré-processamento LEVE.
    Barcode NÃO pode usar threshold agressivo.
    """

    imagem = imagem.convert("RGB")

    enhancer = ImageEnhance.Contrast(imagem)

    imagem = enhancer.enhance(4.0)

    largura, altura = imagem.size

    imagem = imagem.resize((largura * 2, altura * 2))

    return imagem


def detectar_inicio_guias(imagem: Image.Image) -> list[int]:
    """
    Detecta automaticamente a coordenada Y
    de início de cada guia.
    """

    W, H = imagem.size

    col_esq = imagem.crop((0, 0, W // 2, H))

    proc = preprocessar_para_ocr(col_esq)

    data = pytesseract.image_to_data(
        proc, lang=OCR_LANG, output_type=pytesseract.Output.DICT
    )

    inicios_y = []

    for i, word in enumerate(data["text"]):

        if "Parcela" not in word or "Paga" in word:
            continue

        contexto = " ".join(data["text"][max(0, i - 3) : i + 4])

        if not re.search(r"Parcela\s*\d{2}", contexto):
            continue

        y_original = data["top"][i] // ESCALA

        if not inicios_y or (y_original - inicios_y[-1]) > 50:
            inicios_y.append(y_original)

    return inicios_y


def extrair_codigo_barras(imagem: Image.Image) -> str | None:

    try:

        imagem_cv = cv2.cvtColor(np.array(imagem), cv2.COLOR_RGB2BGR)

        detector = cv2.barcode.BarcodeDetector()

        resultado = detector.detectAndDecode(imagem_cv)

        # =====================================================
        # OpenCV pode retornar:
        # 3 ou 4 valores dependendo da versão
        # =====================================================

        if len(resultado) == 3:

            ok, decoded_info, points = resultado

        elif len(resultado) == 4:

            ok, decoded_info, decoded_type, points = resultado

        else:

            print(f"Formato inesperado retorno barcode: {resultado}")

            return None

        # Barcode encontrado

        if ok and decoded_info:

            if isinstance(decoded_info, (list, tuple)):

                codigo = decoded_info[0]

            else:

                codigo = decoded_info

            codigo = re.sub(r"\D", "", codigo)

            if codigo:

                return codigo

    except Exception as e:

        print(f"Erro barcode OpenCV: {e}")

    return None


def formatar_linha_digitavel(codigo: str) -> str | None:
    """
    Formata linha digitável.
    """

    if not codigo:
        return None

    codigo = re.sub(r"\D", "", codigo)

    if len(codigo) < 48:
        return codigo

    return (
        f"{codigo[0:11]}-{codigo[11]} "
        f"{codigo[12:23]}-{codigo[23]} "
        f"{codigo[24:35]}-{codigo[35]} "
        f"{codigo[36:47]}-{codigo[47]}"
    )


def extrair_dados_boleto(texto_esq: str, linha_digitavel: str) -> dict | None:
    """
    Extrai:
      - parcela
      - vencimento
      - valor
      - status
      - linha digitável
    """

    if "Parcela" not in texto_esq:
        return None

    dados = {}

    # PARCELA

    m = re.search(r"Parcela\s+([Gg\d]{2})[/]?(\d{2})\b", texto_esq)

    if m:

        num = re.sub(r"[Gg]", "0", m.group(1))

        dados["parcela"] = f"{num}/{m.group(2)}"

    else:

        dados["parcela"] = None

    # PAGA

    dados["paga"] = bool(re.search(r"Parcela\s+Paga\s+em", texto_esq, re.IGNORECASE))

    # VENCIMENTO

    m = re.search(
        r"Venc[ia]mento.{0,40}?(\d{2})\D{0,2}(\d{2})\D{0,2}(20\d{2})",
        texto_esq,
        re.DOTALL,
    )

    if m:

        dados["vencimento"] = f"{m.group(1)}/" f"{m.group(2)}/" f"{m.group(3)}"

    else:

        m2 = re.search(r"\b(\d{2})/(\d{2})/(20\d{2})\b", texto_esq)

        dados["vencimento"] = (
            f"{m2.group(1)}/" f"{m2.group(2)}/" f"{m2.group(3)}" if m2 else None
        )

    # VALOR

    m = re.search(r"Valor\s*\(R\$\).{0,30}?(\d{1,4}),(\d{2})\b", texto_esq, re.DOTALL)

    if not m:

        m = re.search(r"\b(\d{1,4}),(\d{2})\b", texto_esq)

    dados["valor"] = f"{m.group(1)},{m.group(2)}" if m else None

    # LINHA DIGITÁVEL

    dados["linha_digitavel"] = linha_digitavel

    if not dados["vencimento"] and not dados["valor"]:
        return None

    return dados


def processar_boleto(nome_arquivo: str) -> list[dict]:
    """
    Processamento principal:
      - OCR regional
      - pyzbar barcode
    """

    caminho = os.path.join(BOLETOS_DIR, nome_arquivo)

    # FITZ

    doc = fitz.open(caminho)

    imagens = doc[0].get_images(full=True)

    if not imagens:

        print(f"  [AVISO] Nenhuma imagem embutida em {nome_arquivo}")

        return []

    xref = imagens[0][0]

    imagem = Image.open(io.BytesIO(doc.extract_image(xref)["image"]))

    W, H = imagem.size

    col_x = int(W * 0.35)

    # DETECTA GUIAS

    inicios_y = detectar_inicio_guias(imagem)

    if not inicios_y:

        print(f"  [AVISO] Nenhuma guia detectada em {nome_arquivo}")

        return []

    os.makedirs(TEMP_DEBUG_DIR, exist_ok=True)

    todas_guias = []

    # LOOP GUIAS

    for i, y0 in enumerate(inicios_y):

        y_inicio = max(0, y0 - 30)

        y_fim = inicios_y[i + 1] - 30 if i + 1 < len(inicios_y) else H

        # RECORTE 1
        # OCR TEXTO

        recorte_esq = imagem.crop((0, y_inicio, col_x, y_fim))

        proc_esq = preprocessar_para_ocr(recorte_esq)

        texto_esq = pytesseract.image_to_string(
            proc_esq, lang=OCR_LANG, config=OCR_CONFIG
        )

        # RECORTE 2
        # BARCODE / LINHA DIGITÁVEL

        recorte_barcode = imagem.crop(
            (
                int(W * 0.35),  # esquerda
                y_inicio + 145,  # topo
                W,  # direita
                y_inicio + 260,
            )
        )

        proc_barcode = preprocessar_barcode(recorte_barcode)

        linha_digitavel = extrair_codigo_barras(proc_barcode)

        linha_digitavel = formatar_linha_digitavel(linha_digitavel)

        # DEBUG

        proc_esq.save(
            os.path.join(TEMP_DEBUG_DIR, f"debug_{nome_arquivo}_guia{i+1}_esq.png")
        )

        proc_barcode.save(
            os.path.join(TEMP_DEBUG_DIR, f"debug_{nome_arquivo}_guia{i+1}_barcode.png")
        )

        with open(
            os.path.join(TEMP_DEBUG_DIR, f"debug_{nome_arquivo}_guia{i+1}_esq.txt"),
            "w",
            encoding="utf-8",
        ) as f:

            f.write(texto_esq)

        # PARSER

        dados = extrair_dados_boleto(texto_esq, linha_digitavel)

        if dados:
            todas_guias.append(dados)

    return todas_guias


def main():

    arquivos = sorted(f for f in os.listdir(BOLETOS_DIR) if f.lower().endswith(".pdf"))

    if not arquivos:

        print("Nenhum PDF encontrado em BoletosTemp/")

        return

    for arquivo in arquivos:

        print(f"\n{'='*52}")

        print(f"  Processando: {arquivo}")

        print(f"{'='*52}")

        guias = processar_boleto(arquivo)

        if not guias:

            print("  Nenhuma guia extraída.")

            continue

        for i, guia in enumerate(guias, start=1):

            status = "PAGA" if guia["paga"] else "ABERTA"

            print(f"\n  Guia {i} [{status}]")

            print(f"    Parcela        : {guia['parcela']}")

            print(f"    Vencimento     : {guia['vencimento']}")

            print(f"    Valor (R$)     : {guia['valor']}")

            print(f"    Linha Digitável: {guia['linha_digitavel']}")


if __name__ == "__main__":

    main()
