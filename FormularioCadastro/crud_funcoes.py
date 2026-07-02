from time import sleep


def main():

    clientes = []

    titulo()

    while True:

        opcao = menu()

        if opcao == "1":
            cadastrar_cliente(clientes)

        elif opcao == "2":
            listar_clientes(clientes)

        elif opcao == "4":
            editar_cliente(clientes)

        elif opcao == "4":
            deletar_cliente(clientes)

        elif opcao == "5":
            print("Saindo...")
            sleep(1.5)
            break    

        else:    
            print("Opção invalida, tente novamente!")


def titulo():
    print("===== CADASTRO DE CLIENTES =====")
    print("Para cadastrar prencha os campos abaixo!")


def menu():
    print("\n==== MENU ====")
    print("1 - Cadastrar cliente")
    print("2 - Listar clientes")
    print("3 - Atualizar cliente")
    print("4 - Deletar cliente")
    print("5 - Sair")
    
    return input("Escolha uma opção: ")

    
def cadastrar_cliente(clientes):    
        nome = str(input("Nome: "))
        idade = int(input("idade: "))
        email = str(input("E-mail: "))
        
        cliente = {
            "nome": nome,
            "idade": idade,
            "email": email
        }
        
        clientes.append(cliente)
        print("Cliente cadastrado com sucesso!")
    
    
def listar_clientes(clientes):    
    if not clientes:
        print("Nenhum cliente cadastrado.")
        return

    print("=== Clientes cadastrados na base ===")

    for cont, cliente in enumerate(clientes):
        print(f"{cont} - {cliente}")


def editar_cliente(clientes):  
    if not clientes:
        print("Nenhum cliente cadastrado.")
        return
    
    listar_clientes()
    
    try:
        indice = int(input("Qual cliente deseja editar? "))         
        
        if 0 <= indice < len(clientes):
            cliente = clientes[indice]
            
            novo_nome = str(input(f"Novo nome ({cliente['nome']}): "))
            nova_idade = input(f"Nova idade ({cliente['idade']}): ")
            novo_email = str(input(f"Novo email ({cliente['email']}): "))
            
            if novo_nome:
                cliente["nome"] = novo_nome
            if nova_idade:
                cliente["idade"] = int(nova_idade)
            if novo_email:
                cliente["email"] = novo_email
            
            print("Cliente atualizado com sucesso!")
        else:
            print("Índice inválido.")
            
    except ValueError:
        print("Digite um número válido.")                            
            

def deletar_cliente(clientes):                   
    if not clientes: 
        print("Nenhum cliente cadastrado. ")
        return
    
    print("=== Clientes cadastrados na base ===")
    for cont, cliente in enumerate(clientes):
        print(f"{cont} - {cliente}")        
    
    try: 
        indice = int(input("Qual cliente deseja deletar ?"))
        
        if 0 <= indice < len(clientes):
            removido = clientes.pop(indice)
            print(f"Cliente removido: {removido}")   
                
        else: print("indice inválido")    
        
    except ValueError:
        print("Digite um número valido.")    


if __name__ == "__main__":
    main()