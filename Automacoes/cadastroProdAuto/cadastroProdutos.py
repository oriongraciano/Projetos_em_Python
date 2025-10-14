import pyautogui
import pandas
import time


pyautogui.PAUSE = 0.5

pyautogui.press("win")
pyautogui.write("chrome")
pyautogui.press("enter")


pyautogui.write("https://dlp.hashtagtreinamentos.com/python/intensivao/login")
pyautogui.press("enter")
time.sleep(3)

pyautogui.click(x=817, y=408)
pyautogui.write("meuovoesquerdo@gmail.com")
pyautogui.press("tab")
pyautogui.write("ovodireito")
pyautogui.press("tab")
pyautogui.press("enter")
time.sleep(3)

#Função para pegar posição do mouse na tela.
'''posicao = pyautogui.position()
print(posicao)
time.sleep(5)'''

tabela = pandas.read_csv("produtos.csv")

for linha in tabela.index:
    pyautogui.click(x=831, y=298)

    codigo = str(tabela.loc[linha, "codigo"])
    pyautogui.write(codigo)
    pyautogui.press("tab")

    marca = str(tabela.loc[linha, "marca"])
    pyautogui.write(marca)
    pyautogui.press("tab")

    tipo = str(tabela.loc[linha, "tipo"])
    pyautogui.write(tipo)
    pyautogui.press("tab")

    categoria = str(tabela.loc[linha, "categoria"])
    pyautogui.write(categoria)
    pyautogui.press("tab")

    preço_unitario = str(tabela.loc[linha, "preco_unitario"])
    pyautogui.write(preço_unitario)
    pyautogui.press("tab")

    custo = str(tabela.loc[linha, "custo"])
    pyautogui.write(custo)
    pyautogui.press("tab")

    obs = str(tabela.loc[linha, "obs"])
    if obs != "Nan":
        pyautogui.write(obs)
    pyautogui.press("tab")
    
    pyautogui.press("enter")    

    pyautogui.scroll(10000)

