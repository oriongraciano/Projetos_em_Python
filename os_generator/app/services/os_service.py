from sqlalchemy.orm import Session
from app.models.ordem_servico import OrdemServico
from app.services.pdf_service import gerar_pdf
import os

def gerar_numero_os(db: Session):
    ultima_os = db.query(OrdemServico).order_by(OrdemServico.id.desc()).first()

    if not ultima_os:
        return "OS-000001"

    ultimo_numero = int(ultima_os.numero_os.split("-")[1])
    novo_numero = ultimo_numero + 1

    return f"OS-{novo_numero:06d}"


def criar_ordem_servico(db: Session, dados) -> OrdemServico:
    numero_os = gerar_numero_os(db)

    nova_os = OrdemServico(
        numero_os=numero_os,
        cliente=dados.cliente,
        telefone=dados.telefone,
        equipamento=dados.equipamento,
        problema=dados.problema,
        diagnostico=dados.diagnostico,
        tecnico=dados.tecnico,
        data_abertura=dados.data_abertura,
        status=dados.status,
        valor=dados.valor
    )

    db.add(nova_os)
    db.commit()
    db.refresh(nova_os)

    # Gera PDF após OS existir no banco
    pdf_path = gerar_pdf(nova_os)

    nova_os.pdf_path = pdf_path

    db.commit()
    db.refresh(nova_os)

    return nova_os


def listar_ordens_servico(db: Session):
    return db.query(OrdemServico).all()


def buscar_os_por_id(db: Session, os_id: int):
    return db.query(OrdemServico).filter(
        OrdemServico.id == os_id
    ).first()


def buscar_os_por_numero(db: Session, numero_os: str):
    return db.query(OrdemServico).filter(
        OrdemServico.numero_os == numero_os
    ).first()


def deletar_ordem_servico(db: Session, os_id: int):
    ordem = buscar_os_por_id(db, os_id)

    if not ordem:
        return None
    
    if ordem.pdf_path and os.path.exists(ordem.pdf_path):
        os.remove(ordem.pdf_path)

    db.delete(ordem)
    db.commit()

    return ordem