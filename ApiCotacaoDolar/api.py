import requests 

dolar = requests.get('https://economia.awesomeapi.com.br/last/USD-BRL')
dolar = dolar.json()

dolar_real = dolar['USDBRL']
dolar_real = dolar_real['bid']

print(f'A cotação do Dolar hoje é {dolar_real}')
