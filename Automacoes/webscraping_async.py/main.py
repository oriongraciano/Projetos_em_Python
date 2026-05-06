import asyncio
import aiohttp
from bs4 import BeautifulSoup


async def buscar():

    url = "https://oriongraciano.github.io/Index.html"

    async with aiohttp.ClientSession() as session:

        async with session.get(url) as response:

            html = await response.text()

            pagina = BeautifulSoup(html, "html.parser")

            print(f"Titulo da pagina: {pagina.title.text}")

            links = pagina.find_all("a")    
            imgs = pagina.find_all("img")

            for img in imgs:
                print(img)
            print("Essas são todas imagens da pagina!")    

            for link in links:
                print(link.get("href"))                
            print("Esses são todos links da pagina!")


asyncio.run(buscar())
