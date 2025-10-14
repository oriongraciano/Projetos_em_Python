import os
import httpx
from app.auth import gerar_token, get_cert_paths

BASE_URL = "https://trust-open.api.santander.com.br/bank_account_information/v1/banks"
CLIENT_ID = os.getenv("CLIENT_ID")

async def consultar_saldo(bank_id: str, balance_id: str):
    token = gerar_token(scope="balances")
    crt_path, key_path = get_cert_paths()

    endpoint = f"{BASE_URL}/{bank_id}/balances/{balance_id}"

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "X-Application-Key": CLIENT_ID,
    }

    async with httpx.AsyncClient(cert=(crt_path, key_path), timeout=30) as client:
        resp = await client.get(endpoint, headers=headers)

    if resp.status_code == 200:
        return resp.json()
    return {"erro": f"Erro ao consultar saldo: {resp.status_code}", "detalhe": resp.text}


async def consultar_extrato(bank_id: str, statement_id: str, initialDate: str, finalDate: str, limit: int = 50):
    try:
        token = gerar_token(scope=None)
        crt_path, key_path = get_cert_paths()

        todos_registros = []
        offset = 1

        async with httpx.AsyncClient(cert=(crt_path, key_path), timeout=30) as client:
            while True:
                endpoint = f"{BASE_URL}/{bank_id}/statements/{statement_id}"
                params = {
                    "initialDate": initialDate,
                    "finalDate": finalDate,
                    "_offset": offset,
                    "_limit": limit,
                }

                headers = {
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/json",
                    "X-Application-Key": CLIENT_ID,
                }

                resp = await client.get(endpoint, headers=headers, params=params)

                if resp.status_code != 200:
                    return {
                        "erro": f"Erro ao consultar Extrato: {resp.status_code}",
                        "detalhe": resp.text,
                        "url": str(resp.url),
                    }

                data = resp.json()
                conteudo = data.get("_content", [])
                todos_registros.extend(conteudo)

                if len(conteudo) < limit:
                    break
                offset += 1

        return {"_content": todos_registros}

    except Exception as e:
        return {"erro": "Exceção na consulta de extrato", "detalhe": str(e)}
