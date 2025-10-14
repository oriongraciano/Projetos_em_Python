import pyautogui
import time

pyautogui.PAUSE = 0.8

pyautogui.press("win")
pyautogui.write("chrome")
pyautogui.press("enter")

pyautogui.click(x=493, y=61)
pyautogui.write("https://remoincorporadora.com.br")
pyautogui.press("enter")
time.sleep(5)

# Metodo para achar posição do mouse
'''posicao = pyautogui.position()
time.sleep(5)
print(posicao)'''

pyautogui.click(x=493, y=61)
pyautogui.press("backspace")
pyautogui.write("https://residencialencanto.com.br")
pyautogui.press("enter")
time.sleep(5)

pyautogui.click(x=493, y=61)
pyautogui.press("backspace")
pyautogui.write("https://hmincorporadora.com.br")
pyautogui.press("enter")
time.sleep(5)