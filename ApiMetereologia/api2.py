import requests

url = "https://wttr.in/Belo+Horizonte"

response = requests.get(url)

if response.status_code == 200:
    data = response.text
    print(data)
else: 
    print("Ouve uma falha ao realizar requisição", response.status_code)    