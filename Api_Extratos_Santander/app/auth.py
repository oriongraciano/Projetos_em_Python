import os
import atexit
import tempfile
import requests
from typing import Tuple, Optional
from cryptography.hazmat.primitives.serialization import pkcs12, Encoding, PrivateFormat, NoEncryption
from dotenv import load_dotenv

load_dotenv()

AUTH_URL = "https://trust-open.api.santander.com.br/auth/oauth/v2/token"

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
CERT_PATH_PFX = os.getenv("CERT_PFX_PATH")
CERT_PASSWORD = os.getenv("CERT_PASSWORD")

# cache de caminhos do cert para reuso no processo
_CERT_CRT_PATH: Optional[str] = None
_CERT_KEY_PATH: Optional[str] = None
_TEMP_FILES: list[str] = []

def _cleanup_temp_files():
    for p in _TEMP_FILES:
        try:
            if p and os.path.exists(p):
                os.remove(p)
        except Exception:
            pass

atexit.register(_cleanup_temp_files)

def get_cert_paths() -> Tuple[str, str]:
    """
    Extrai o PFX uma única vez por execução e retorna caminhos (crt,key).
    Mantém os arquivos até o processo encerrar (limpeza via atexit).
    """
    global _CERT_CRT_PATH, _CERT_KEY_PATH

    if _CERT_CRT_PATH and _CERT_KEY_PATH and os.path.exists(_CERT_CRT_PATH) and os.path.exists(_CERT_KEY_PATH):
        return _CERT_CRT_PATH, _CERT_KEY_PATH

    if not os.path.exists(CERT_PATH_PFX):
        raise FileNotFoundError(f"PFX não encontrado em: {CERT_PATH_PFX}")

    if not CERT_PASSWORD:
        raise RuntimeError("CERT_PASSWORD não definido no ambiente.")

    with open(CERT_PATH_PFX, "rb") as f:
        pfx_data = f.read()

    private_key, certificate, _ = pkcs12.load_key_and_certificates(
        pfx_data, CERT_PASSWORD.encode()
    )

    # cria arquivos temporários persistentes
    cert_file = tempfile.NamedTemporaryFile(delete=False, suffix=".crt")
    key_file = tempfile.NamedTemporaryFile(delete=False, suffix=".key")

    cert_file.write(certificate.public_bytes(Encoding.PEM))
    cert_file.flush(); cert_file.close()

    key_file.write(private_key.private_bytes(
        encoding=Encoding.PEM,
        format=PrivateFormat.PKCS8,
        encryption_algorithm=NoEncryption()
    ))
    key_file.flush(); key_file.close()

    _CERT_CRT_PATH = cert_file.name
    _CERT_KEY_PATH = key_file.name
    _TEMP_FILES.extend([_CERT_CRT_PATH, _CERT_KEY_PATH])

    return _CERT_CRT_PATH, _CERT_KEY_PATH


def gerar_token(scope: Optional[str] = None, timeout: int = 20) -> str:
    """
    Gera access_token via mTLS. Usa o mesmo cert nas duas pontas.
    """
    if not CLIENT_ID or not CLIENT_SECRET:
        raise RuntimeError("CLIENT_ID ou CLIENT_SECRET não definidos no ambiente.")

    crt_path, key_path = get_cert_paths()

    data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }
   
    if scope:
        data["scope"] = scope

    resp = requests.post(
        AUTH_URL,
        data=data,
        cert=(crt_path, key_path),
        timeout=timeout,  # evita travar
    )

    if resp.status_code != 200:
        raise RuntimeError(f"Falha ao obter token: {resp.status_code} - {resp.text}")

    payload = resp.json()
    token = payload.get("access_token")
    if not token:
        raise RuntimeError(f"Resposta sem access_token: {payload}")
    return token
