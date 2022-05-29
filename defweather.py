from bs4 import BeautifulSoup
import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}


async def weatherc(ctx, city):

    try:
        res = requests.get(
            f'https://www.google.com/search?q=weather+{city}&oq=weatherr+{city}&aqs=chrome.0.35i39l2j0l4j46j69i60.6128j1j7&sourceid=chrome&ie=UTF-8',
            headers=headers)
        print("Searching...\n")
        soup = BeautifulSoup(res.text, 'html.parser')
        location = soup.select('#wob_loc')[0].getText().strip()
        info = soup.select('#wob_dc')[0].getText().strip()
        tm = soup.select('#wob_tm')[0].getText().strip()
        return location,info,tm

    except IndexError:

        await ctx.send('Sorry I can`t find such a city. Try another one')