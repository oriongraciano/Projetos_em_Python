import requests
import os
from app.auth import gerar_token

BASE_URL = "https://api.sicoob.com.br/conta-corrente/v4"

def consultar_extrato(mes: int, ano: int, dia_inicial: int, dia_final: int, agrupar_cnab: bool, numero_conta: int):
    token = gerar_token()
    if not token:
        return {"erro": "Não foi possível gerar o token."}

    endpoint = f"{BASE_URL}/extrato/{mes:02d}/{ano}"
    params = {
        "diaInicial": dia_inicial,
        "diaFinal": dia_final,
        "agruparCNAB": str(agrupar_cnab).lower(),
        "numeroContaCorrente": numero_conta
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "client_id": os.getenv("CLIENT_ID")
    }

    response = requests.get(endpoint, headers=headers, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        return {
            "erro": f"Erro ao consultar extrato: {response.status_code}",
            "detalhes": response.text
        }
