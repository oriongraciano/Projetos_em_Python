from time import sleep
from datetime import date
from collections import Counter

produtos = []


def titulo(msg):
    print("===" * 10)
    print(f"--- {msg} ---")
    print("===" * 10)


titulo("-- CONTROLE DE VENDAS --")


def menu():
    print("\n        -- MENU -- ")
    print("Opção 1 - Registrar produto vendido")
    print("Opção 2 - Listar produtos vendidos")
    print("Opção 3 - Listar produtos mais vendido")
    print("Opção 4 - Editar produtos vendidos")
    print("Opção 5 - Deletar produtos vendidos")
    print("Opção 00 - Sair")

nome_vendedor = input("\nInforme o nome do vendedor(a): ")

while True:
    menu()
    sleep(1.0)

    opcao_escolhida = input(f"Olá, {nome_vendedor} qual opção deseja escolher? ")

    if opcao_escolhida == "00":
        sleep(1.5)
        print("Saindo...")
        sleep(1.5)
        print("Sistema encerrado.")
        break


    elif opcao_escolhida == "1":
        nome = str(input("informe o nome do produto: ")).strip().upper()
        preco = float(input("Informe o preço do produto: "))
        quantidade = int(input("Informe a quantidade do produto: "))
        data_venda = date.today()

        produto = {
            "nome": nome, 
            "preco": preco, 
            "quantidade": quantidade
        }

        produtos.append(produto)
        print(f"Parabéns {nome_vendedor}, por mais uma venda concluida com sucesso!")


    elif opcao_escolhida == "2":
        print("-- Produtos Vendidos --")

        if not produtos:
            print("Nenhum produto Vendido")

        for cont, produto in enumerate(produtos):
            valor_venda = produto["preco"] * produto["quantidade"]
            valor_vendido = valor_venda
            print(f"{cont} - {produto} - Data Venda: {data_venda}")
            print(f"O valor total vendido pelo vendedor {nome_vendedor} foi {valor_vendido:.2f}")


    elif opcao_escolhida == "3":
        if not produtos:
            print("Nenhum produto Vendido")

        nomes_produtos = []

        for produto in produtos:
            nomes_produtos.append(produto["nome"])

        contador = Counter(nomes_produtos)

        print(contador)

        contador = Counter(produto["nome"] for produto in produtos)
        print("\n--- Ranking de Vendas ---")

        for posicao,(nome, quantidade) in enumerate(contador.most_common(), start=1):
            print(f"{posicao}º - {nome}: {quantidade} vendas")


    elif opcao_escolhida == "4":
        if not produtos:
            print("Nenhum produto Vendido")

        print("== Produtos vendidos registrados ==")
        for cont, produto in enumerate(produtos):
            print(f"{cont} - {produto} - Data Venda:{data_venda}")

        try:

            indice = int(input("Qual produto vendido deseja editar? "))

            if 0 < indice < len(produtos):
                produto = produtos[indice]

                novo_nome = input(f"Digite o novo nome do ({produto['nome']}): ")
                novo_preco = input(f"Digite o novo preço do ({produto['preco']}): ")
                nova_qtd = input(f"Digite a nova quantidade do ({produto['quantidade']}): ")

                if novo_nome:
                    produto["nome"] = novo_nome
                if novo_preco:
                    produto["preco"] = novo_preco
                if nova_qtd:
                    produto["quantidade"] = nova_qtd
                else:
                    print("Indice invalido!")
        except ValueError:
            print("Digite um número valido de acordo com id selecionado.")


    elif opcao_escolhida == "5":

        print("== Produtos vendidos registrados ==")
        for cont, produto in enumerate(produtos):
            print(f"{cont} - {produto} - Data Venda:{data_venda}")

        try:

            indice = int(input("Qual produto vendido deseja excluir? "))

            if 0 < indice < len(produtos):
                produto = produtos[indice]
                removido = produtos.pop(indice)
                print("Produto vendido deletado com sucesso!")

            else:
                print("Indice Invalido!")
        except ValueError:
            print("Digite um id valido.")
