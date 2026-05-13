from PIL import Image, ImageEnhance
import pytesseract
import re
import os
from pdf2image import convert_from_path

# ✅ Constantes de configuração
TESSERACT_CMD  = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
POPPLER_PATH   = r"C:\Program Files (x86)\poppler\Library\bin"
TEMP_DEBUG_DIR = r"debug_ocr"
BOLETOS_DIR    = "BoletosTemp"
OCR_LANG       = "por+eng"
OCR_CONFIG     = "--psm 6"

pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD


def preprocessar_para_ocr(imagem: Image.Image) -> Image.Image:
    """Pipeline de pré-processamento da imagem para melhorar leitura OCR."""

    imagem = imagem.convert("RGB")

    enhancer = ImageEnhance.Contrast(imagem)
    imagem = enhancer.enhance(3.0)

    largura, altura = imagem.size
    imagem = imagem.resize((largura * 3, altura * 3))

    imagem = imagem.convert("L")
    imagem = imagem.point(lambda x: 0 if x < 160 else 255, "1")

    return imagem


def extrair_dados_boleto(texto: str) -> list[dict]:
    """
    Extrai os campos de cada guia a partir do texto OCR distorcido.

    Estratégia:
      - Divide o texto em blocos por âncora 'IPTU...Parcela'
      - Aplica regex tolerantes a ruído OCR em cada bloco
      - Linha digitável: busca padrão de 4 grupos numéricos com traço

    Campos extraídos:
      - parcela        : ex "05/09"
      - vencimento     : ex "30/06/2026"
      - valor          : ex "53,18"
      - linha_digitavel: ex "81640000000-5 53182531202-2 ..."
      - paga           : True se a parcela já foi paga
    """

    guias = []

    # Divide por bloco de parcela ───────
    blocos = re.split(
        r"(?=(?:IPTU|IPT[UL]|1PTU).{0,30}?Parcela\s+[\dOoIl]{2,4}[/X\s]?[\dOoIl]{2,4})",
        texto
    )

    # Linha digitável — extrai todas do texto completo ─
    # Padrão real: "81640000000-5  53182531202-2  60630971100-4  01607804052-0"
    linhas_digitaveis = re.findall(
        r"(\d{5,12}-\d[\s,]+\d{5,12}-\d[\s,]+\d{5,12}-\d[\s,]+\d{5,12}-\d)",
        texto
    )
    idx_linha = 0

    for bloco in blocos:

        if "Parcela" not in bloco:
            continue

        dados = {}

        # Parcela
        # Real: "03/09" | OCR: "0309", "O3X9", "03 09"
        m = re.search(r"Parcela\s+([\dOoIl]{2,4})[/X\s\-]?([\dOoIl]{2,4})", bloco)
        if m:
            num = re.sub(r"[Oo]", "0", re.sub(r"[Ii]", "1", m.group(1)))
            den = re.sub(r"[Oo]", "0", re.sub(r"[Ii]", "1", m.group(2)))
            dados["parcela"] = f"{num.zfill(2)}/{den.zfill(2)}"
        else:
            dados["parcela"] = None

        # Paga 
        dados["paga"] = bool(re.search(r"Parcela\s+Paga\s+em", bloco, re.IGNORECASE))

        # Vencimento 
        # Real: "30/06/2026" | OCR: "JOR /20 26", "3132026", "SOAS 20276"
        m = re.search(
            r"Venc[ai]mento.{0,30}?(\d{1,2})\s*[/\\\s]\s*(\d{1,2})\s*[/\\\s]\s*(20\d{2})",
            bloco, re.DOTALL
        )
        if m:
            dados["vencimento"] = f"{m.group(1).zfill(2)}/{m.group(2).zfill(2)}/{m.group(3)}"
        else:
            m2 = re.search(r"(\d{2})/(\d{2})/(20\d{2})", bloco)
            dados["vencimento"] = f"{m2.group(1)}/{m2.group(2)}/{m2.group(3)}" if m2 else None

        #  Valor 
        # Real: "53,18" | OCR: "45 ,18", "535,18", "43,1H"
        m = re.search(r"\b(\d{1,4})[,.](\d{2})\b", bloco)
        dados["valor"] = f"{m.group(1)},{m.group(2)}" if m else None

        # Linha digitável 
        m = re.search(
            r"(\d{5,12}-\d[\s,]+\d{5,12}-\d[\s,]+\d{5,12}-\d[\s,]+\d{5,12}-\d)",
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

    paginas = convert_from_path(
        caminho,
        first_page=1,
        last_page=1,
        poppler_path=POPPLER_PATH,
        dpi=400
    )

    imagem_processada = preprocessar_para_ocr(paginas[0])

    texto_ocr = pytesseract.image_to_string(imagem_processada, lang=OCR_LANG, config=OCR_CONFIG)

    os.makedirs(TEMP_DEBUG_DIR, exist_ok=True)
    imagem_processada.save(os.path.join(TEMP_DEBUG_DIR, f"debug_{nome_arquivo}.png"))
    with open(os.path.join(TEMP_DEBUG_DIR, f"debug_{nome_arquivo}.txt"), "w", encoding="utf-8") as f:
        f.write(texto_ocr)

    return extrair_dados_boleto(texto_ocr)


def main():
    """Ponto de entrada — processa todos os boletos da pasta."""

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