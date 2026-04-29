from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from cryptography.hazmat.primitives.serialization.pkcs12 import load_key_and_certificates
from cryptography.hazmat.backends import default_backend

# Caminho para o arquivo PFX
caminho_pfx = "C:/Users/Documents/Projetos/ExtratordeChavePublica/certs/Certificado_A1_2025.pfx"
senha_pfx = b"Certificado@2025"  # b = bytes

# Lê o conteúdo do arquivo PFX
with open(caminho_pfx, "rb") as arquivo:
    pfx_data = arquivo.read()

# Carrega a chave privada, certificado e CA (se houver)
chave_privada, certificado, cadeia = load_key_and_certificates(pfx_data, senha_pfx, backend=default_backend())

# Extrai a chave pública do certificado
chave_publica = certificado.public_key()

# Serializa a chave pública no formato PEM
chave_publica_pem = chave_publica.public_bytes(
    encoding=Encoding.PEM,
    format=PublicFormat.SubjectPublicKeyInfo
)

# Salva a chave pública em um arquivo
with open("Chave_publicaCertifica.pem", "wb") as f:
    f.write(chave_publica_pem)

print("Chave pública extraída com sucesso para 'chave_publica.pem'")
