from sqlalchemy import Column, Integer, String, Text, Numeric, Date, DateTime
from sqlalchemy.sql import func
from app.database import Base

class OrdemServico(Base):
    __tablename__ = "ordens_servico"

    id = Column(Integer, primary_key=True, index=True)
    numero_os = Column(String, unique=True, nullable=False)

    cliente = Column(String, nullable=False)
    telefone = Column(String, nullable=False)

    equipamento = Column(String, nullable=False)

    problema = Column(Text, nullable=False)
    diagnostico = Column(Text, nullable=True)

    tecnico = Column(String, nullable=False)

    data_abertura = Column(Date, nullable=False)

    status = Column(String, nullable=False)

    valor = Column(Numeric(10, 2), nullable=False)

    pdf_path = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())