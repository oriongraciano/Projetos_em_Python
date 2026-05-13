from PIL import Image, ImageEnhance
import pytesseract
import fitz
import re
import io
import os

TESSERACT_CMD  = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
TEMP_DEBUG_DIR = r"debug_ocr"
BOLETOS_DIR    = "BoletosTemp"
OCR_LANG       = "por+eng"
OCR_CONFIG     = "--psm 6"

ESCALA = 3

pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD


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
        if "Parcela" not in word or "Paga" in word:
            continue

        contexto = " ".join(data["text"][max(0, i - 3):i + 4])
        if not re.search(r"Parcela\s*\d{2}", contexto):
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
    m = re.search(r"Parcela\s+([Gg\d]{2})[/]?(\d{2})\b", texto_esq)
    if m:
        num = re.sub(r"[Gg]", "0", m.group(1))
        dados["parcela"] = f"{num}/{m.group(2)}"
    else:
        dados["parcela"] = None

    # Paga
    dados["paga"] = bool(re.search(r"Parcela\s+Paga\s+em", texto_esq, re.IGNORECASE))

    # Vencimento 
    # Real: "30/06/2026" | OCR residual: "3046/2026", "30N6/2026"
    m = re.search(
        r"Venc[ia]mento.{0,40}?(\d{2})\D{0,2}(\d{2})\D{0,2}(20\d{2})",
        texto_esq, re.DOTALL
    )
    if m:
        dados["vencimento"] = f"{m.group(1)}/{m.group(2)}/{m.group(3)}"
    else:
        m2 = re.search(r"\b(\d{2})/(\d{2})/(20\d{2})\b", texto_esq)
        dados["vencimento"] = f"{m2.group(1)}/{m2.group(2)}/{m2.group(3)}" if m2 else None

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
        texto_full
    )
    dados["linha_digitavel"] = re.sub(r"\s+", " ", m.group(1)).strip() if m else None

    if not dados["vencimento"] and not dados["valor"]:
        return None

    return dados


def processar_boleto(nome_arquivo: str) -> list[dict]:
    """
    Extrai imagem do PDF via fitz, detecta Y de cada guia e aplica
    dois recortes por guia:
      - coluna esquerda : parcela, vencimento, valor, status
      - largura total   : linha digitável
    """

    caminho = os.path.join(BOLETOS_DIR, nome_arquivo)

    # fitz: extrai imagem embutida original do PDF
    doc = fitz.open(caminho)
    imagens = doc[0].get_images(full=True)

    if not imagens:
        print(f"  [AVISO] Nenhuma imagem embutida em {nome_arquivo}")
        return []

    xref   = imagens[0][0]
    imagem = Image.open(io.BytesIO(doc.extract_image(xref)["image"]))

    W, H  = imagem.size
    col_x = int(W * 0.35) 
    imagem.save(os.path.join(TEMP_DEBUG_DIR, f"debug_{nome_arquivo}_guiaImagem.png"))


    # Detecta Y de início de cada guia automaticamente
    inicios_y = detectar_inicio_guias(imagem)

    if not inicios_y:
        print(f"  [AVISO] Nenhuma guia detectada em {nome_arquivo}")
        return []

    os.makedirs(TEMP_DEBUG_DIR, exist_ok=True)
    todas_guias = []

    for i, y0 in enumerate(inicios_y):

        y_inicio = max(0, y0 - 30)
        y_fim    = inicios_y[i + 1] - 30 if i + 1 < len(inicios_y) else H

        # ── Recorte 1: coluna esquerda — parcela, vencimento, valor 
        recorte_esq  = imagem.crop((0, y_inicio, col_x, y_fim))
        proc_esq     = preprocessar_para_ocr(recorte_esq)
        texto_esq    = pytesseract.image_to_string(proc_esq, lang=OCR_LANG, config=OCR_CONFIG)

        # ── Recorte 2: largura total — linha digitável 
        recorte_full = imagem.crop((int(W * 0.35), y_inicio + 145, W, y_fim ))
        proc_full    = preprocessar_para_ocr(recorte_full)
        texto_full   = pytesseract.image_to_string(proc_full, lang=OCR_LANG, config=OCR_CONFIG)

        # Debug — salva ambos os recortes e textos
        proc_esq.save(os.path.join(TEMP_DEBUG_DIR, f"debug_{nome_arquivo}_guia{i+1}_esq.png"))
        proc_full.save(os.path.join(TEMP_DEBUG_DIR, f"debug_{nome_arquivo}_guia{i+1}_full.png"))

        with open(os.path.join(TEMP_DEBUG_DIR, f"debug_{nome_arquivo}_guia{i+1}_esq.txt"), "w", encoding="utf-8") as f:
            f.write(texto_esq)
        with open(os.path.join(TEMP_DEBUG_DIR, f"debug_{nome_arquivo}_guia{i+1}_full.txt"), "w", encoding="utf-8") as f:
            f.write(texto_full)

        dados = extrair_dados_boleto(texto_esq, texto_full)
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