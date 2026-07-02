from pydantic import BaseModel
from datetime import date
from decimal import Decimal


class OrdemServicoCreate(BaseModel):
    cliente: str
    telefone: str
    equipamento: str
    problema: str
    diagnostico: str | None = None
    tecnico: str
    data_abertura: date
    status: str
    valor: Decimal