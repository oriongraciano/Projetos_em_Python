import re

texto = "O valor da fatura é R$1299 reais. Codigo: 125455. Data Vencimento: 12/05/2026"

valor = re.findall(r"R\$(\d+)\s(.....)", texto)
codigo = re.findall(r"Codigo:\s(\d+)", texto)
data = re.findall(r"\d{2}/\d{2}/\d{4}", texto)

print(
    f"Esses são os dados relevante da fatura: codigo:{codigo}, valor:{valor}, data venc:{data}"
)
