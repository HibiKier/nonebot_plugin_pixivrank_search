from nonebot.adapters.onebot.v11 import MessageSegment
from asyncio.exceptions import TimeoutError
from aiohttp.client_exceptions import ClientConnectorError
from bs4 import BeautifulSoup
import aiohttp
import aiofiles
import nonebot
import feedparser
import os
import platform
if platform.system() == 'Windows':
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

headers = {'User-Agent': "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; TencentTraveler 4.0)"}

driver: nonebot.Driver = nonebot.get_driver()

local_proxy = driver.config.local_proxy if driver.config.local_proxy else None

rsshub = driver.config.rsshub if driver.config.rsshub else 'https://rsshub.app/'
rsshub = rsshub[:-1] if rsshub[-1] == "/" else rsshub


IMAGE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__))) + '/'
if not os.path.exists(f'{IMAGE_PATH}/tmp/'):
    os.mkdir(f'{IMAGE_PATH}/tmp/')
IMAGE_PATH += '/tmp/'


async def get_pixiv_urls(mode: str, num: int = 5, date: str = '') -> 'list, list, int':
    url = f'{rsshub}/pixiv/ranking/{mode}'
    if date:
        url += f'/{date}'
    try:
        return await parser_data(url, num)
    except ClientConnectorError:
        return await get_pixiv_urls(mode, num, date)


async def download_pixiv_imgs(urls: list, user_id: int) -> str:
    result = ''
    index = 0
    for img in urls:
        async with aiohttp.ClientSession(headers=headers) as session:
            for _ in range(3):
                async with session.get(img, proxy=local_proxy, timeout=10) as response:
                    # print(response.url)
                    async with aiofiles.open(IMAGE_PATH + f'/{user_id}_{index}_pixiv.jpg', 'wb') as f:
                        try:
                            await f.write(await response.read())
                            result += MessageSegment.image(file=f'file:///{IMAGE_PATH}/{user_id}_{index}_pixiv.jpg')
                            index += 1
                            break
                        except TimeoutError:
                            # result += '\n这张图下载失败了..\n'
                            pass
            else:
                result += '\n这张图下载失败了..\n'
    return result


async def search_pixiv_urls(keyword: str, num: int, order: str, r18: int) -> 'list, list':
    url = f'{rsshub}/pixiv/search/{keyword}/{order}/{r18}'
    return await parser_data(url, num)


async def parser_data(url: str, num: int) -> 'list, list, int':
    text_list = []
    urls = []
    async with aiohttp.ClientSession() as session:
        for _ in range(3):
            try:
                async with session.get(url, proxy=local_proxy, timeout=2) as response:
                    data = feedparser.parse(await response.text())['entries']
                    break
            except TimeoutError:
                pass
        else:
            return ['网络不太好，也许过一会就好了'], [], 998
        try:
            if len(data) == 0:
                return ['没有搜索到喔'], [], 997
            if num > len(data):
                num = len(data)
            data = data[:num]
            for data in data:
                soup = BeautifulSoup(data['summary'], 'lxml')
                title = "标题：" + data['title']
                pl = soup.find_all('p')
                author = pl[0].text.split('-')[0].strip()
                imgs = []
                text_list.append(f'{title}\n{author}\n')
                for p in pl[1:]:
                    imgs.append(p.find('img').get('src'))
                urls.append(imgs)
        except ValueError as e:
            return ['是网站坏了啊，也许过一会就好了'], [], 999
        return text_list, urls, 200
