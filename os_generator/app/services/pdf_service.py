from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import os


def gerar_pdf(ordem_servico):
    pasta_pdf = "app/static/pdfs"

    if not os.path.exists(pasta_pdf):
        os.makedirs(pasta_pdf)

    pdf_path = f"{pasta_pdf}/{ordem_servico.numero_os}.pdf"

    c = canvas.Canvas(pdf_path, pagesize=A4)
    largura, altura = A4

    y = altura - 50

    # Cabeçalho
    c.setFont("Helvetica-Bold", 18)
    c.drawString(140, y, "OG SOLUÇÕES EM TECNOLOGIA")

    y -= 30
    c.setFont("Helvetica-Bold", 14)
    c.drawString(180, y, f"ORDEM DE SERVIÇO")

    y -= 40
    c.line(50, y, 550, y)

    y -= 30
    c.setFont("Helvetica", 12)

    c.drawString(50, y, f"Número OS: {ordem_servico.numero_os}")
    y -= 25

    c.drawString(50, y, f"Cliente: {ordem_servico.cliente}")
    y -= 25

    c.drawString(50, y, f"Telefone: {ordem_servico.telefone}")
    y -= 25

    c.drawString(50, y, f"Equipamento: {ordem_servico.equipamento}")
    y -= 25

    c.drawString(50, y, f"Técnico: {ordem_servico.tecnico}")
    y -= 25

    c.drawString(50, y, f"Data: {ordem_servico.data_abertura}")
    y -= 25

    c.drawString(50, y, f"Status: {ordem_servico.status}")
    y -= 25

    c.drawString(50, y, f"Valor: R$ {ordem_servico.valor}")
    y -= 40

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Problema:")
    y -= 25

    c.setFont("Helvetica", 12)
    c.drawString(70, y, str(ordem_servico.problema))
    y -= 50

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Diagnóstico:")
    y -= 25

    c.setFont("Helvetica", 12)
    c.drawString(70, y, str(ordem_servico.diagnostico))
    y -= 100

    # Assinaturas
    c.line(80, y, 230, y)
    c.line(330, y, 480, y)

    y -= 20
    c.drawString(115, y, "Técnico")
    c.drawString(375, y, "Cliente")

    c.save()

    return pdf_path