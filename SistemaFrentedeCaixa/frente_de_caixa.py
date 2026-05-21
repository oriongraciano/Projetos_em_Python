from time import sleep

total = 0
mais_de_Mil = 0
produto_mais_barato = ""
preco_mais_barato = 0
contador = 0

produtos = []


def linha():
    print("===" * 10)


while True:
    linha()
    print("  FRENTE DE CAIXA  ")
    linha()

    nome_produto = str(input("Informe nome do produto: "))
    preco = float(input("Informe o preço do produto: R$ "))

    produto = {"nome": nome_produto, "preco": preco}

    produtos.append(produto)

    contador += 1
    total += preco

    if preco > 1000:
        mais_de_Mil += 1

    if contador == 1 or preco < preco_mais_barato:
        preco_mais_barato = preco
        produto_mais_barato = nome_produto

    continuar = " "
    while continuar not in "SN":
        continuar = str(input("Deseja continuar? [SN]")).strip().upper()[0]

    if continuar == "N":
        break

sleep(1.5)
print(f"O valor total gasto na compra foi de {total:.2f} reais")
print(f"Temos {mais_de_Mil} produtos que custam mais de R$ 1.000 reais")
print(f"O Produto mais barato foi {preco_mais_barato:.2f} que custa R${produto_mais_barato} reais ")
sleep(1.5)


print("\nPRODUTOS CADASTRADOS:")
for cont, produto in enumerate(produtos):
    print(
        f"Esses são os produtos comprados: {cont} - {produto['nome']} - R$ {produto['preco']:.2f} reais"
    )