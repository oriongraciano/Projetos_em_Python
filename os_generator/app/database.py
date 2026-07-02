from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os

# Carrega variáveis de ambiente
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Cria engine do SqlAlchemy
engine = create_engine(DATABASE_URL)

# Cria sessão
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para models
Base = declarative_base()
