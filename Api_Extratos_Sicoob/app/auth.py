import os
import requests
import tempfile
from cryptography.hazmat.primitives.serialization import pkcs12, Encoding, PrivateFormat, NoEncryption
from dotenv import load_dotenv

load_dotenv()

AUTH_URL = "https://auth.sicoob.com.br/auth/realms/cooperado/protocol/openid-connect/token"
CLIENT_ID = os.getenv("CLIENT_ID")
SCOPE = "cco_extrato cco_consulta openid"
CERT_PATH = "C:/sicoob_api-00.000-0/certs/CERTIFICADO.pfx"
CERT_PASSWORD = os.getenv("CERT_PASSWORD")

def gerar_token():
    with open(CERT_PATH, 'rb') as f:
        pfx_data = f.read()

    private_key, certificate, _ = pkcs12.load_key_and_certificates(
        pfx_data,
        CERT_PASSWORD.encode()
    )

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pem") as cert_file:
        cert_file.write(certificate.public_bytes(Encoding.PEM))
        cert_file_path = cert_file.name

    with tempfile.NamedTemporaryFile(delete=False, suffix=".key") as key_file:
        key_file.write(private_key.private_bytes(
            encoding=Encoding.PEM,
            format=PrivateFormat.PKCS8,
            encryption_algorithm=NoEncryption()
        ))
        key_file_path = key_file.name

    response = requests.post(
        AUTH_URL,
        data={
            "grant_type": "client_credentials",
            "client_id": CLIENT_ID,
            "scope": SCOPE
        },
        cert=(cert_file_path, key_file_path),
        verify=True
    )

    os.remove(cert_file_path)
    os.remove(key_file_path)

    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print("Erro ao obter token:", response.status_code, response.text)
        return None
