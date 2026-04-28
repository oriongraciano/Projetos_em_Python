#Sistema de oficina de reparo de Rodas (ARQUITETURA CLEAN CODE):

from time import sleep

def perguntar_sim_nao(pergunta):
        while True:
             resposta = input(pergunta).strip().upper()
             if resposta in ["SIM", "NÃO"]:
                     return resposta
             else:
                print("Resposta inválida! Digite apenas SIM ou NÃO.")
             
             
def processo_desempeno(modelo):
        print(f"\nEssa roda da {modelo} precisa de DESEMPENO...")
        for cont in range(1,6):
                sleep(1.0)
                print(f"Esquenta! {cont}º Marretada...")
        print("Pronto! Roda DESEMPENADA!")
        
        
def processo_solda(modelo):
        print(f"\nEssa roda esta com rachaduras, vai precisar de SOLDAR...")
        for cont in range(1,6):
                sleep(1.0)
                print(f"Abrindo trinca... Aplicando {cont}º Solda!")
        print("Pronto... RODA SOLDADA!")
        
        
def enviar_pintura(modelo):
        print(f"\nEssa roda {modelo} esta com estrutura ok, mandar direto para PINTURA!")
        

def conclusao_entrega(modelo):
        print(f"\nRoda {modelo} reforma concluida!, Ligar para cliente buscar...")        
        
        
def main():
        print("=== Reforma de Rodas Orion ===")
        
        modelo = input("Informe marca e modelo da Roda: ")
        
        roda_amassada = perguntar_sim_nao("A roda esta amassada? [SIM/NÃO]: ")   
        roda_trincada = perguntar_sim_nao("A roda esta trincada? [SIM/NÃO]: ")      

        if roda_amassada == "NÃO" and roda_trincada == "NÃO":
                sleep(1.0)
                enviar_pintura(modelo) 
                
        else: 
              if roda_amassada == "SIM" and roda_trincada == "SIM":
                      print("Roda com dano critico! terá que passar por todos os processos")
                
              if roda_amassada == "SIM":
                  sleep(1.0)
                  processo_desempeno(modelo)
                  
              if roda_trincada == "SIM":
                  sleep(1.0)    
                  processo_solda(modelo)
                  
              print("\nFinalizado processo estrutural...")
              sleep(1.0)
              enviar_pintura(modelo)
              sleep(1.0)
              print("\n===>" * 3)
              conclusao_entrega(modelo)

if __name__ == "__main__":
        main()