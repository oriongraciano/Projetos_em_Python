from time import sleep

print("===== CADASTRO DE CLIENTES =====")

clientes = []

print("Para cadastrar prencha os campos abaixo!")

#Cadastro de cliente
while True:
    print("\n==== MENU ====")
    print("1 - Cadastrar cliente")
    print("2 - Listar clientes")
    print("3 - Atualizar cliente")
    print("4 - Deletar cliente")
    print("5 - Sair")
    
    opcao = input("Escolha uma opção: ")
    
    if opcao == "5":
        sleep(1.5)
        print("Saindo...")
        sleep(1.5)
        break
    
    
    elif opcao == "1":
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
    
    
    #Lista clientes cadastrados
    elif opcao == "2":
        print("=== Clientes cadastrados na base ===")
        for cont, cliente in enumerate(clientes):
            print(f"{cont} - {cliente}")


    #Edita cliente cadastrado de acordo com indice selecionado    
    elif opcao == "3":
        if not clientes:
            print("Nenhum cliente cadastrado.")
            continue
        
        print("=== Clientes cadastrados na base ===")
        for cont, cliente in enumerate(clientes):
            print(f"{cont} - {cliente}")
        
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
            
            
    #Exclui cliente cadastrado de acordo com indice selecionado        
    elif opcao == "4": 
        if not clientes: 
            print("Nenhum cliente cadastrado. ")
            continue
        
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
       