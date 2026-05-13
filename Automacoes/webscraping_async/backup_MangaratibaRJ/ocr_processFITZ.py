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
OCR_CONFIG     = "--psm 11"

pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD


def preprocessar_para_ocr(imagem: Image.Image) -> Image.Image:
    """Pipeline de pré-processamento da imagem embutida para OCR."""

    imagem = imagem.convert("RGB")

    enhancer = ImageEnhance.Contrast(imagem)
    imagem = enhancer.enhance(4.0)

    largura, altura = imagem.size
    imagem = imagem.resize((largura * 3, altura * 3))

    imagem = imagem.convert("L")
    imagem = imagem.point(lambda x: 0 if x < 160 else 255, "1")

    return imagem


def extrair_dados_boleto(texto: str) -> list[dict]:
    """
    Extrai os campos de cada guia a partir do texto OCR.
    Campos extraídos por guia:
      - parcela        : "06/09"
      - vencimento     : "31/07/2026"
      - valor          : "53,18"
      - linha_digitavel: "81610000000-8 53182531202-2 ..."
      - paga           : True se parcela já foi paga
    """

    guias = []

    # Divide por bloco de parcela
    blocos = re.split(
        r"(?=(?:IPTU|IPT[UL]).{0,30}?Parcela\s+\d{2}[/]?\d{2})",
        texto
    )

    # Linha digitável — extrai todas do texto completo 
    # Padrão: "81610000000-8 53182531202-2 607319711000 01607804062-9"
    linhas_digitaveis = re.findall(
        r"(\d{8,12}-?\d[\s]+\d{8,12}-?\d[\s]+\d{8,12}-?\d[\s]+\d{8,12}-?\d)",
        texto
    )
    idx_linha = 0

    for bloco in blocos:

        if "Parcela" not in bloco:
            continue

        dados = {}

        # Parcela 
        # Real: "06/09" | OCR residual: "06109", "G8/09", "0809"
        m = re.search(r"Parcela\s+([Gg\d]{2})[/]?(\d{2})\b", bloco)
        if m:
            num = re.sub(r"[Gg]", "0", m.group(1))
            dados["parcela"] = f"{num}/{m.group(2)}"
        else:
            dados["parcela"] = None

        # Paga 
        dados["paga"] = bool(re.search(r"Parcela\s+Paga\s+em", bloco, re.IGNORECASE))

        # Vencimento 
        # Real: "31/07/2026" | OCR: "3147/2026", "3107/2026", "30/09/2026"
        # Estratégia: próximo ao label Vencimento, aceita dígitos extras no meio
        m = re.search(
            r"Venc[ia]mento.{0,40}?(\d{2})\D{0,2}(\d{2})\D{0,2}(20\d{2})",
            bloco, re.DOTALL
        )
        if m:
            dados["vencimento"] = f"{m.group(1)}/{m.group(2)}/{m.group(3)}"
        else:
            # fallback: dd/mm/yyyy puro no bloco
            m2 = re.search(r"\b(\d{2})/(\d{2})/(20\d{2})\b", bloco)
            dados["vencimento"] = f"{m2.group(1)}/{m2.group(2)}/{m2.group(3)}" if m2 else None

        # Valor
        # Real: "53,18" | OCR: "53,25", "435,15" — bem legível com fitz
        # Pega o primeiro valor com vírgula após "Valor (R$)"
        m = re.search(r"Valor\s*\(R\$\).{0,30}?(\d{1,4}),(\d{2})\b", bloco, re.DOTALL)
        if not m:
            m = re.search(r"\b(\d{1,4}),(\d{2})\b", bloco)
        dados["valor"] = f"{m.group(1)},{m.group(2)}" if m else None

        # Linha digitável
        # Busca no bloco primeiro; fallback no índice global
        m = re.search(
            r"(\d{8,12}-?\d[\s]+\d{8,12}-?\d[\s]+\d{8,12}-?\d[\s]+\d{8,12}-?\d)",
            bloco
        )
        if m:
            dados["linha_digitavel"] = re.sub(r"\s+", " ", m.group(1)).strip()
        elif idx_linha < len(linhas_digitaveis) and not dados["paga"]:
            dados["linha_digitavel"] = re.sub(r"\s+", " ", linhas_digitaveis[idx_linha]).strip()
            idx_linha += 1
        else:
            dados["linha_digitavel"] = None

        if dados["vencimento"] or dados["valor"]:
            guias.append(dados)

    return guias


def processar_boleto(nome_arquivo: str) -> list[dict]:
   
    caminho = os.path.join(BOLETOS_DIR, nome_arquivo)

    # fitz: extrai imagem embutida original do PDF:
    doc = fitz.open(caminho)
    imagens = doc[0].get_images(full=True)

    if not imagens:
        print(f"  [AVISO] Nenhuma imagem embutida em {nome_arquivo}")
        return []

    xref = imagens[0][0]
    base_image = doc.extract_image(xref)
    imagem = Image.open(io.BytesIO(base_image["image"]))

    imagem_processada = preprocessar_para_ocr(imagem)

    texto_ocr = pytesseract.image_to_string(imagem_processada, lang=OCR_LANG, config=OCR_CONFIG)

    # Debug — salva imagem e texto para inspeção
    os.makedirs(TEMP_DEBUG_DIR, exist_ok=True)
    imagem_processada.save(os.path.join(TEMP_DEBUG_DIR, f"debug_{nome_arquivo}.png"))
    with open(os.path.join(TEMP_DEBUG_DIR, f"debug_{nome_arquivo}.txt"), "w", encoding="utf-8") as f:
        f.write(texto_ocr)

    return extrair_dados_boleto(texto_ocr)


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