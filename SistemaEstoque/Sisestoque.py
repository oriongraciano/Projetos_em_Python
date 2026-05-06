from time import sleep
import datetime


print("---Sistema de estoque---")
print("===" * 10)

produtos = []

while True:
    print("--MENU--")
    print("opção 1 - Cadastrar novo produto")
    print("opção 2 - Listar produtos cadastrados")
    print("opção 3 - Editar produtos cadastrados")
    print("opção 4 - Deletar produtos cadastrados")
    print("opção 5 - Sair")
    
    opcao = int(input("Escolha uma opção: "))
    
    if opcao == "5":
        sleep(1.5)
        print("Saindo...")
        sleep(1.5)
        break
    
    elif opcao == "1": 
        nome = input("informe nome do produto: ")
        preco = input("Informe o preço do produto: ")
        quantidade = input("Informe a quantidade do produto")
        
        produto = {
            "nome": "",
            "preco": 0.0,
            "quantidade": 0
        }
        
        produtos.append(produto)
        sleep(1.5)
        print("Produto cadastrado com sucesso!")