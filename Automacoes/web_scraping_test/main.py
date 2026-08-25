import asyncio
import aiohttp
from bs4 import BeautifulSoup

url = 'https://webscraper.io/test-sites/pagination'
url_dolar = 'https://economia.awesomeapi.com.br/last/USD-BRL'

async def cotacao_dolar(session):

        async with session.get(url_dolar) as response:
        
            dolar = await response.json()

            dolar_real = dolar['USDBRL']
            dolar_real = dolar_real['bid']

            print(f'A cotação do Dolar hoje é {dolar_real}')

        return dolar_real    


async def baixar_pagina(session, url):
    async with session.get(url) as response:
        html = await response.text()  
        soup = BeautifulSoup(html, "html.parser")  

    return soup


def extrair_links_paginas(soup):
    paginacao = soup.find('ul', class_='pagination')
    links = paginacao.find_all("a")

    paginas = []

    for link in links:
        hrefs = link.get("href")
        
        if not hrefs:
            continue

        if hrefs:
            numero = link.text.strip()
            paginas.append({
                "numero": numero,
                "url": hrefs
            })

    return paginas


def extrair_produtos(soup, dolar_real):
    produtos = soup.find_all('div', class_='card sitemap-card test-sites-card') 

    lista_produtos = []

    for produto in produtos:
        nome = produto.find("h3", itemprop="name").text.strip()
        preco = produto.find("span", itemprop="price").text.strip()
        imagem = produto.find("img", itemprop="image").get("src")
        disponibilidade = produto.find('div', class_="badge")
        estrelas = produto.find('div', class_= 'col-6 rarity-rating d-flex flex-row justify-content-start p-0')
        avaliacao = estrelas.get("data-rating")
        texto = disponibilidade.text.strip()

        preco = preco.replace("USD", "").replace(" ", "")
        preco = float(preco)

        valor_convertido = preco * float(dolar_real)
    
        if texto.startswith("Available"):
            lista_produtos.append({
                "nome": nome,
                "imagem": imagem,
                "disponibilidade": texto,
                "avaliacao": avaliacao,
                "preco_usd": preco,
                "preco_brl": valor_convertido
            })
    
    
    return lista_produtos  


async def scraping_test():
    async with aiohttp.ClientSession() as session:

        dolar_real = await cotacao_dolar(session)

        soup = await baixar_pagina(session, url)

        todos_produtos = extrair_produtos(soup, dolar_real)

        paginas = extrair_links_paginas(soup)[0:]

        
        for pagina in paginas:
            numero = pagina["numero"] 
            url_pagina = pagina["url"]

            soup = await baixar_pagina(session, url_pagina)

            produtos = extrair_produtos(soup, dolar_real)

            print("\nProdutos disponíveis:")
            print(f"Página {numero}: {len(produtos)} produtos")
            print("=-=" * 10)      
            todos_produtos.extend(produtos)
        
        for produto in todos_produtos:
            print(
                f"{produto['nome']} | "
                f"USD {produto['preco_usd']:.2f} | "
                f"R$ {produto['preco_brl']:.2f} | "
                f"Avaliação: {produto['avaliacao']}"
            )   

asyncio.run(scraping_test())
