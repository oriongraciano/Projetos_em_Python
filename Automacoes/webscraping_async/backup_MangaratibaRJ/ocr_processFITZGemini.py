import os
import io
import re
import fitz  # PyMuPDF
import pytesseract
from PIL import Image, ImageEnhance, ImageOps
from pyzbar.pyzbar import decode
import numpy as np

# Configurações
TESSERACT_CMD  = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
BOLETOS_DIR    = "BoletosTemp"
TEMP_DEBUG_DIR = "debug_ocr"
pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

class ProcessadorBoletoMangaratiba:
    def __init__(self):
        self.ocr_config = "--psm 6" # PSM 6 é melhor para blocos uniformes de dados
        self.escala = 3
        os.makedirs(TEMP_DEBUG_DIR, exist_ok=True)

    def preprocessar(self, imagem: Image.Image, modo="texto") -> Image.Image:
        """Pipeline de imagem otimizado por tipo de dado."""
        img = imagem.convert("L")
        
        if modo == "barcode":
            # Para código de barras, menos é mais. Apenas um leve ajuste de contraste.
            enhancer = ImageEnhance.Contrast(img)
            return enhancer.enhance(2.0)
        
        # Para texto, binarização ajuda no Tesseract
        img = ImageOps.autocontrast(img)
        largura, altura = img.size
        img = img.resize((largura * self.escala, altura * self.escala), Image.Resampling.LANCZOS)
        return img.point(lambda x: 0 if x < 180 else 255, "1")

    def extrair_barcode(self, imagem_guia: Image.Image) -> str | None:
        """Tenta ler o código de barras I25."""
        # O ZBar trabalha bem com a imagem original ou levemente ajustada
        decoded = decode(imagem_guia)
        for obj in decoded:
            if obj.type == 'I25' or len(obj.data) >= 44:
                return obj.data.decode('utf-8')
        return None

    def limpar_texto(self, texto: str) -> str:
        return " ".join(texto.split())

    def parse_dados(self, texto: str, linha_barcode: str = None) -> dict:
        """Regex aprimoradas para os campos específicos da prefeitura."""
        dados = {
            "inscricao": None,
            "cobranca": None,
            "parcela": None,
            "vencimento": None,
            "valor": None,
            "linha_digitavel": linha_barcode,
            "paga": bool(re.search(r"Parcela\s+Paga", texto, re.I))
        }

        # Inscrição (Ex: 103652.99) [cite: 4, 92]
        m_insc = re.search(r"Inscri[çc][ãa]o\s*(\d{5,8}[\.\s]\d{2})", texto)
        if m_insc: dados["inscricao"] = m_insc.group(1).replace(" ", ".")

        # N° Cobrança (Ex: 01607804) [cite: 3, 17]
        m_cob = re.search(r"(?:Cobran[çc]a|Gula)\s*(\d{7,10})", texto)
        if m_cob: dados["cobranca"] = m_cob.group(1)

        # Parcela (Ex: 06/09) [cite: 1, 14]
        m_parc = re.search(r"Parcela\s*(\d{2}/\d{2})", texto)
        if m_parc: dados["parcela"] = m_parc.group(1)

        # Vencimento (Ex: 31/07/2026) [cite: 7, 19]
        m_venc = re.search(r"(\d{2}/\d{2}/20\d{2})", texto)
        if m_venc: dados["vencimento"] = m_venc.group(1)

        # Valor (Ex: 53,18) [cite: 8, 21]
        m_val = re.search(r"(?:Valor|Total).*?(\d{1,4},\d{2})", texto, re.S)
        if m_val: dados["valor"] = m_val.group(1)

        return dados

    def detectar_guias(self, imagem: Image.Image) -> list[int]:
        """Localiza os Y iniciais de cada guia."""
        W, H = imagem.size
        # Foca na lateral esquerda superior para achar "Prefeitura" ou "Parcela"
        crop_check = imagem.crop((0, 0, W//2, H))
        data = pytesseract.image_to_data(self.preprocessar(crop_check), output_type=pytesseract.Output.DICT)
        
        indices = []
        for i, text in enumerate(data['text']):
            if "Parcela" in text and not "Paga" in data['text'][i:i+2]:
                y = data['top'][i] // self.escala
                if not indices or (y - indices[-1]) > 200:
                    indices.append(y)
        return indices

    def processar_arquivo(self, path: str):
        doc = fitz.open(path)
        img_data = doc[0].get_images(full=True)
        if not img_data: return []

        pix = doc.extract_image(img_data[0][0])
        imagem = Image.open(io.BytesIO(pix["image"]))
        W, H = imagem.size
        
        pontos_y = self.detectar_guias(imagem)
        resultados = []

        for i, y0 in enumerate(pontos_y):
            y_start = max(0, y0 - 150) # Buffer para pegar Inscrição no topo
            y_end = pontos_y[i+1] - 20 if i+1 < len(pontos_y) else H
            
            guia_img = imagem.crop((0, y_start, W, y_end))
            
            # 1. Tentar Código de Barras (Decodificação Direta)
            barcode = self.extrair_barcode(guia_img)
            
            # 2. OCR para o restante dos dados
            guia_proc = self.preprocessar(guia_img)
            texto_ocr = pytesseract.image_to_string(guia_proc, lang="por", config=self.ocr_config)
            
            # Debug saving
            guia_proc.save(os.path.join(TEMP_DEBUG_DIR, f"debug_{os.path.basename(path)}_g{i}.png"))

            dados = self.parse_dados(texto_ocr, barcode)
            resultados.append(dados)
            
        doc.close()
        return resultados

def main():
    proc = ProcessadorBoletoMangaratiba()
    arquivos = [f for f in os.listdir(BOLETOS_DIR) if f.lower().endswith(".pdf")]

    for arq in arquivos:
        print(f"\n--- Analisando: {arq} ---")
        caminho = os.path.join(BOLETOS_DIR, arq)
        guias = proc.processar_arquivo(caminho)
        
        for idx, g in enumerate(guias):
            status = " [PAGA]" if g['paga'] else " [ABERTA]"
            print(f"Guia {idx+1}{status}: {g['parcela']} | Venc: {g['vencimento']} | Valor: R$ {g['valor']}")
            print(f"   Inscrição: {g['inscricao']} | Cobrança: {g['cobranca']}")
            print(f"   Linha: {g['linha_digitavel'] if g['linha_digitavel'] else 'NÃO DETECTADA'}")

if __name__ == "__main__":
    main()