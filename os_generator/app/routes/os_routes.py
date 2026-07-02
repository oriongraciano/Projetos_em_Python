from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.schemas.ordem_servico_schema import OrdemServicoCreate
from app.services.os_service import criar_ordem_servico
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from app.services.os_service import (
    criar_ordem_servico,
    listar_ordens_servico, 
    buscar_os_por_id,
    buscar_os_por_numero,
    deletar_ordem_servico
)

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/ordem-servico")
def criar_os(
    ordem_servico: OrdemServicoCreate,
    db: Session = Depends(get_db)
):
    return criar_ordem_servico(db, ordem_servico)            


@router.get("/ordens-servico")
def listar_os(db: Session = Depends(get_db)):
    return listar_ordens_servico(db)


@router.get("/ordem-servico/numero/{numero_os}")
def buscar_por_numero(numero_os: str, db: Session = Depends(get_db)):
    ordem = buscar_os_por_numero(db, numero_os)

    if not ordem:
        raise HTTPException(
            status_code=404,
            detail="Ordem de serviço não encontrada"
        )

    return ordem


@router.get("/ordem-servico/{os_id}")
def buscar_por_id(os_id: int, db: Session = Depends(get_db)):
    ordem = buscar_os_por_id(db, os_id)

    if not ordem:
        raise HTTPException(
            status_code=404,
            detail="Ordem de serviço não encontrada"
        )
    
    return ordem


@router.get("/ordem-servico/{os_id}/pdf")
def baixar_pdf(os_id: int, db: Session = Depends(get_db)):
    ordem = buscar_os_por_id(db,os_id)

    if not ordem:
        raise HTTPException(
            status_code=404,
            detail="Ordem de serviço não encontrada"
        )
    
    if not ordem.pdf_path:
        raise HTTPException(status_code=404, detail="PDF ainda não foi gerado")
    
    return FileResponse(
        path=ordem.pdf_path,
        media_type='application/pdf',
        filename=f"{ordem.numero_os}-OG.pdf",
    )

@router.delete("/ordem-servico/{os_id}")
def deletar_os(os_id: int, db: Session = Depends(get_db)):
    ordem = deletar_ordem_servico(db, os_id)

    if not ordem:
        raise HTTPException(
            status_code=404,
            detail="OS não encontrada"
        )

    return {"message": "OS deletada com sucesso"}