from fpdf import FPDF
from datetime import datetime
from pathlib import Path

def format_brl(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

class ExtratoPDF(FPDF):
    def header(self):
        self.set_text_color(0, 0, 0)

        BASE_DIR = Path(__file__).resolve().parents[1].parent
        logo_path = BASE_DIR / "static" / "logo-santander.png"

        if logo_path.is_file():
            self.image(str(logo_path), x=10, y=15, w=30, h=25)
        else:
            print('Logo do Santander não carregou!')

        self.set_xy(0, 30)
        self.set_font("Arial", "B", 14)
        self.cell(0, 10, "Extrato Santander Conta: 1300000-0", border=False, ln=True, align="C")

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


def gerar_pdf_extrato_santander(
    json_data: dict,
    saldo_final_real: float,
    nome_arquivo: str = "extrato_santander.pdf"
):
    transacoes = json_data["_content"]
    transacoes.sort(key=lambda x: datetime.strptime(x["transactionDate"], "%d/%m/%Y"))

    # Calcula saldo inicial do período
    saldo_calculado = saldo_final_real
    for transacao in reversed(transacoes):
        valor = float(transacao["amount"])
        if transacao["creditDebitType"] == "CREDITO":
            saldo_calculado -= valor
        else:
            saldo_calculado += valor
    saldo_inicial = saldo_calculado

    pdf = ExtratoPDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_font("Arial", size=9)

    saldo_atual = saldo_inicial
    ultimo_dia = None

    for transacao in transacoes:
        data_str = transacao["transactionDate"]
        data_formatada = datetime.strptime(data_str, "%d/%m/%Y").strftime("%d/%m/%Y")
        tipo = transacao["creditDebitType"]
        valor = float(transacao["amount"])
        descricao = (transacao["transactionName"] + " " + (transacao.get("historicComplement") or "")).strip()[:90]

        if ultimo_dia and data_formatada != ultimo_dia:
            pdf.set_font("Arial", "B", 9)
            pdf.cell(190, 8, f"SALDO DO DIA {ultimo_dia}: {format_brl(saldo_atual)}", 1, ln=True, align="R")
            pdf.ln(2)
            pdf.set_font("Arial", size=9)

        pdf.cell(35, 8, data_formatada, 1, align="C")
        pdf.cell(20, 8, tipo, 1, align="C")

        if tipo == "DEBITO":
            pdf.set_text_color(220, 0, 0)
            saldo_atual -= valor
        else:
            pdf.set_text_color(0, 0, 0)
            saldo_atual += valor

        valor_formatado = format_brl(valor) + (" D" if tipo == "DEBITO" else " C")
        pdf.cell(30, 8, valor_formatado, 1, align="R")
        pdf.set_text_color(0, 0, 0)

        pdf.cell(105, 8, descricao, 1, align="L")
        pdf.ln()

        ultimo_dia = data_formatada

    if ultimo_dia:
        pdf.set_font("Arial", "B", 9)
        pdf.cell(190, 8, f"SALDO DO DIA {ultimo_dia}: {format_brl(saldo_atual)}", 1, ln=True, align="R")

    pdf.ln(5)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 8, f"SALDO INICIAL DO PERÍODO: {format_brl(saldo_inicial)}", ln=True, align="R")
    pdf.cell(0, 8, f"SALDO FINAL DO PERÍODO: {format_brl(saldo_final_real)}", ln=True, align="R")

    # Agora salva apenas no caminho passado
    pdf.output(str(nome_arquivo))
    return str(nome_arquivo)
