from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
from app.sicoob import consultar_extrato
from app.utils.pdf import gerar_pdf_extrato
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import os

app = FastAPI(title="API de Extrato Sicoob")


#Função para rodar diariamente e salvar o extrato
def gerar_extrato_diario():
    try:
        from app.sicoob import consultar_extrato
        from app.utils.pdf import gerar_pdf_extrato

        hoje = datetime.now()
        mes = hoje.month
        ano = hoje.year
        dia_inicial = 1
        dia_final = hoje.day
        numero_conta = 000000
        agrupar_cnab = True

        resultado_json = consultar_extrato(mes, ano, dia_inicial, dia_final, agrupar_cnab, numero_conta)
        if "erro" in resultado_json:
            print(f"[ERRO] {resultado_json['erro']}")
            return
        
        nome_arquivo = f"extrato-sicoob_{mes:02d}_{ano}.pdf"
        pasta_extratos = r"\\0.0.00.0\Extratos-Bancarios\ExtratosSicoob\00.000-0"
        os.makedirs(pasta_extratos, exist_ok=True)
        caminho_arquivo = os.path.join(pasta_extratos, nome_arquivo)

        gerar_pdf_extrato(resultado_json, nome_arquivo=caminho_arquivo)
        print(f"[OK] Extrato gerado: {caminho_arquivo}")

    except Exception as e:
        print(f"[FALHA AO GERAR EXTRATO AUTOMATICO] {str(e)}")

#Iniciar agendador
scheduler = BackgroundScheduler()
scheduler.add_job(gerar_extrato_diario, "cron", hour=7, minute=15)
scheduler.start()        
print("[INFO] Agendador diário iniciado sucesso!")


# endpoint JSON padrão
@app.get("/extrato/{mes}/{ano}")
def extrato(
    mes: int,
    ano: int,
    diaInicial: int = Query(...),
    diaFinal: int = Query(...),
    agruparCNAB: bool = Query(True),
    numeroContaCorrente: int = Query(...)
):
    return consultar_extrato(mes, ano, diaInicial, diaFinal, agruparCNAB, numeroContaCorrente)


# endpoint para PDF
@app.get("/extrato/pdf/{mes}/{ano}")
def extrato_em_pdf(
    mes: int,
    ano: int,
    diaInicial: int = Query(...),
    diaFinal: int = Query(...),
    agruparCNAB: bool = Query(True),
    numeroContaCorrente: int = Query(...)
):
    resultado_json = consultar_extrato(mes, ano, diaInicial, diaFinal, agruparCNAB, numeroContaCorrente)
    nome_arquivo = f"extrato-sicoob_0{mes}_{ano}.pdf"

    # caminho ABSOLUTO ou relativo para salvar pasta na rede
    import os
    pasta_extratos = r"\\00.00.000.00\Extratos-Bancarios\ExtratosSicoob\00.000-0"
    os.makedirs(pasta_extratos, exist_ok=True)  # garante que a pasta existe, so funciona se user tiver permisão

    caminho_arquivo = os.path.join(pasta_extratos, nome_arquivo)

    # gerar e salvar no caminho
    gerar_pdf_extrato(resultado_json, nome_arquivo=caminho_arquivo)
    
    # e retornar para download no navegador
    return FileResponse(caminho_arquivo, media_type="application/pdf", filename=nome_arquivo)

