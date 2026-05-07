from time import sleep
import datetime

print("--- Sistema de estoque ---")
print("===" * 10)

produtos = []


while True:
    print("-- MENU --")
    print("opção 1 - Cadastrar novo produto")
    print("opção 2 - Listar produtos cadastrados")
    print("opção 3 - Editar produtos cadastrados")
    print("opção 4 - Deletar produtos cadastrados")
    print("opção 5 - Sair")

    opcao = input("Escolha uma opção: ").strip()

    # Cadastrar clientes:
    if opcao == "5":
        sleep(1.5)
        print("Saindo...")
        sleep(1.5)
        break

    elif opcao == "1":
        nome = str(input("informe nome do produto: ")).strip()
        preco = float(input("Informe o preço do produto: "))
        quantidade = float(input("Informe a quantidade do produto: "))

        produto = {"nome": nome, "preco": preco, "quantidade": quantidade}

        produtos.append(produto)
        print("Produto cadastrado com sucesso!")

    # Lista produtos cadastrados:
    elif opcao == "2":
        print("Produtos cadastrados na Base:")
        
        valor_estoque = 0
        
        for cont, produto in enumerate(produtos):
            valorTotal = produto["preco"] * produto["quantidade"]
            valor_estoque += valorTotal
            
            print(f"{cont} - {produto}")
            print(f"Valor total do estoque atual: {valorTotal:.2f}")
            
        print(f"\nValor total do estoque: R$ {valor_estoque:.2f}")    
            

    # Editar produtos cadastrados
    elif opcao == "3":
        if not produtos:
            print("Não há produtos cadastrados!")
            continue

        print("Produtos cadastrados na Base:")
        for cont, produto in enumerate(produtos):
            print(f"{cont} - {produto}")

        try:
            indice = (input("Qual produto deseja editar? "))

            if 0 <= indice < len(produtos):
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
                print("Cliente atualizado com sucesso!")
            else:
                print("Indice Invalido!")

        except ValueError:
            print("Digite um número valido de acordo com indice selecionado.")

    # Deletar produto cadastrado:
    elif opcao == "4":
        if not produtos:
            print("Nenhum produto cadastrado. ")
            continue

        print("Produtos cadastrados na Base:")
        for cont, produto in enumerate(produtos):
            print(f"{cont} - {produto}")

        try:
            indice = (input("Qual produto deseja deletar? "))

            if 0 <= indice < len(produtos):
                removido = produtos.pop(indice)
                print(f"Cliente removido: {removido}")
            else:
                print("Indice Invalido!")

        except ValueError:
            print("Digite um número valido.")
