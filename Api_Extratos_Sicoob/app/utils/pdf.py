from fpdf import FPDF
from datetime import datetime
from pathlib import Path

def format_brl(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

class ExtratoPDF(FPDF):

    def header(self):
        self.set_text_color(0, 0, 0)

        # Caminho da logo
        BASE_DIR = Path(__file__).resolve().parents[1].parent
        logo_path = BASE_DIR / "static" / "sicoob-logo.png"

        # Logo à esquerda
        if logo_path.is_file():
            self.image(str(logo_path), x=10, y=15, w=30, h=20)
        else:
            print('Logo não carregou!')    
        
         # Título centralizado (mais abaixo para evitar sobreposição)
        self.set_xy(0, 30)
        self.set_font("Arial", "B", 14)
        self.cell(0, 10, "Extrato Bancário Sicoob - Conta:41.967-2", border=False, ln=True, align="C")

        self.ln(5)
        self.set_font("Arial", "B", 10)
        self.cell(35, 8, "Data", 1, align="C")
        self.cell(20, 8, "Tipo", 1, align="C")
        self.cell(30, 8, "Valor", 1, align="C")
        self.cell(105, 8, "Descrição", 1, align="C")
        self.ln()

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Página {self.page_no()}", 0, 0, "C")

def gerar_pdf_extrato(json_data: dict, nome_arquivo: str = "extrato.pdf"):
    saldo_anterior = float(json_data['resultado']['saldoAnterior'])
    saldo_atual = saldo_anterior

    pdf = ExtratoPDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_font("Arial", size=9)

    transacoes = json_data["resultado"]["transacoes"]
    transacoes.sort(key=lambda x: x["data"])

    ultimo_dia = None

    for transacao in transacoes:
        data_iso = transacao["data"]
        data_apenas = data_iso[:10]
        data_formatada = datetime.fromisoformat(data_iso).strftime("%d/%m/%Y %H:%M")
        tipo = transacao["tipo"]
        valor = float(transacao["valor"])
        descricao = transacao["descricao"][:90]

        if tipo == "CREDITO":
            saldo_atual += valor
            sinal = "C"
        else:
            saldo_atual -= valor
            sinal = "D"

        valor_formatado = format_brl(valor) + f"{sinal}"

        if ultimo_dia and data_apenas != ultimo_dia:
            pdf.set_font("Arial", "B", 9)
            pdf.cell(190, 8, f"SALDO DO DIA {ultimo_dia}: {format_brl(saldo_dia)}", 1, ln=True, align="R")
            pdf.ln(2)
            pdf.set_font("Arial", size=9)

        pdf.cell(35, 8, data_formatada, 1, align="C")
        pdf.cell(20, 8, tipo, 1, align="C")

        if tipo == "DEBITO":
            pdf.set_text_color(220, 0, 0)  # vermelho
        else:
            pdf.set_text_color(0, 0, 0)    # preto

        pdf.cell(30, 8, valor_formatado, 1, align="R")
        pdf.set_text_color(0, 0, 0)  # reset

        pdf.cell(105, 8, descricao, 1, align="L")
        pdf.ln()

        saldo_dia = saldo_atual
        ultimo_dia = data_apenas

    if ultimo_dia:
        pdf.set_font("Arial", "B", 9)
        pdf.cell(190, 8, f"SALDO DO DIA {ultimo_dia}: {format_brl(saldo_dia)}", 1, ln=True, align="R")

    pdf.ln(5)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 8, f"SALDO ANTERIOR AO PERIODO: {format_brl(float(json_data['resultado']['saldoAnterior']))}", ln=True, align="R")
    pdf.cell(0, 8, f"SALDO EM CTA ULTIMO DIA DO PERIODO: {format_brl(saldo_atual)}", ln=True, align="R")

    pasta_extratos = pasta_extratos = Path(r"\\10.10.100.10\Extratos-Bancarios\ExtratosSicoob\41.967-2")
    pasta_extratos.mkdir(exist_ok=True)
    caminho_arquivo = pasta_extratos / nome_arquivo
    pdf.output(str(caminho_arquivo))
    return str(caminho_arquivo)