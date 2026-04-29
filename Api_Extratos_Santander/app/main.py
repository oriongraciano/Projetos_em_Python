from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import FileResponse
from app.santander import consultar_extrato, consultar_saldo
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import os
from pathlib import Path
from app.utils.pdf import gerar_pdf_extrato_santander
import shutil
import asyncio

app = FastAPI(title="API de Extrato Santander")

# Cria instância global do scheduler
scheduler = BackgroundScheduler()

#Função consultar Saldo
@app.get("/{bank_id}/balances/{balance_id}")
async def gerar_saldo(bank_id="90400888000000", balance_id="2032.000000000000"):
    return await consultar_saldo(bank_id, balance_id)


# Função do agendador, rodar diariamente e salvar no Extrato
def gerar_extrato_diario():
    asyncio.run(_gerar_extrato_async())

async def _gerar_extrato_async():   
    try:
        hoje = datetime.now()
        ano = hoje.year
        mes = hoje.month
        dia_final = hoje.day

        initialDate = f"{ano}-{mes:02d}-01"
        finalDate = f"{ano}-{mes:02d}-{dia_final:02d}"

        bank_id = "9040088800000"
        statement_id = "2032.000000000000"
        _offset = 1
        _limit = 50

        # 1 Consulta o extrato
        resultado_json = await consultar_extrato(bank_id, statement_id, initialDate, finalDate, _limit)
        if "erro" in resultado_json:
            print(f"[ERRO] {resultado_json['erro']}")
            return

        # 2 Consulta o saldo real do Santander
        saldo_json = await consultar_saldo(bank_id, statement_id)
        saldo_inicial_real = float(saldo_json["availableAmount"])

        # 3 Gera PDF localmente
        nome_arquivo = f"extrato-santander_{mes:02d}_{ano}.pdf"
        base_dir = Path(__file__).resolve().parent.parent  # raiz do projeto (ex: C:\santander_api-13007506-1)
        pasta_local = base_dir / "ExtratosTemp"
        os.makedirs(pasta_local, exist_ok=True)

        caminho_local = pasta_local / nome_arquivo

        gerar_pdf_extrato_santander(
            resultado_json,
            nome_arquivo=caminho_local,
            saldo_final_real=saldo_inicial_real
        )

        # 4 Copia para a pasta de rede
        pasta_rede = r"\\0.0.0.0\Extratos-Bancarios\ExtratosSantander\13000000-0"
        os.makedirs(pasta_rede, exist_ok=True)
        caminho_rede = os.path.join(pasta_rede, nome_arquivo)

        shutil.copy2(caminho_local, caminho_rede)

        print(f"[OK] Extrato Santander gerado local ({caminho_local}) e copiado para rede ({caminho_rede})")

    except Exception as e:
        print(f"[FALHA AO GERAR EXTRATO AUTOMATICO - Santander] {str(e)}")


# Starta o scheduler apenas quando a API subir
@app.on_event("startup")
def start_scheduler():
    if not scheduler.running:
        scheduler.add_job(gerar_extrato_diario, "cron", hour=7, minute=20)
        scheduler.start()
        print("[INFO] Agendador diário Santander iniciado com sucesso!")


# Endpoint gerar Json Padrão
@app.get("/{bank_id}/statements/{statement_id}")
async def extrato(bank_id: str, statement_id: str, initialDate: str, finalDate: str, _limit: int = 50):
    return await consultar_extrato(bank_id, statement_id, initialDate, finalDate, _limit)


# Endpoint Gera PDF e salva na pasta rede
@app.get("/{bank_id}/statements/{statement_id}/pdf")
async def extrato_pdf(bank_id: str, statement_id: str, initialDate: str, finalDate: str, _limit: int = 50):
    try:
        extrato_json = await consultar_extrato(bank_id, statement_id, initialDate, finalDate, _limit)
        saldo_json = await consultar_saldo(bank_id, statement_id)
        saldo_inicial_real = float(saldo_json["availableAmount"])

        nome_arquivo = f"extrato-santander_{finalDate}.pdf"
        pasta_local = r"C:\ExtratosTemp"
        os.makedirs(pasta_local, exist_ok=True)
        caminho_local = os.path.join(pasta_local, nome_arquivo)

        gerar_pdf_extrato_santander(extrato_json, nome_arquivo=caminho_local, saldo_final_real=saldo_inicial_real)

        pasta_rede = r"\\\0.0.0.0\Extratos-Bancarios\ExtratosSantander\13000000-0"
        os.makedirs(pasta_rede, exist_ok=True)
        shutil.copy2(caminho_local, os.path.join(pasta_rede, nome_arquivo))

        return FileResponse(path=caminho_local, filename=nome_arquivo, media_type="application/pdf")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    