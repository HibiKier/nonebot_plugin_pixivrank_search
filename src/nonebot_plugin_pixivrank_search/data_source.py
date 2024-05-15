import asyncio
import platform
from asyncio.exceptions import TimeoutError

import aiohttp
import aiofiles
import feedparser
from bs4 import BeautifulSoup
from nonebot.log import logger
from nonebot import require, get_driver

from .config import config

require("nonebot_plugin_localstore")

from nonebot_plugin_alconna import UniMessage
from nonebot_plugin_localstore import get_cache_dir

if platform.system() == "Windows":

    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

headers = {"User-Agent": "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; TencentTraveler 4.0)"}

IMAGE_PATH = get_cache_dir("pixivrank_search")


driver = get_driver()
session: aiohttp.ClientSession


@driver.on_startup
async def _():
    global session
    session = aiohttp.ClientSession()


@driver.on_shutdown
async def _():
    await session.close()


async def get_pixiv_urls(mode: str, num: int = 5, date: str = ""):
    url = f"{config.pixr_rsshub}/pixiv/ranking/{mode}"
    if date:
        url += f"/{date}"
    return await parser_data(url, num)


async def search_pixiv_urls(keyword: str, num: int, order: str, r18: int):
    url = f"{config.pixr_rsshub}/pixiv/search/{keyword}/{order}/{r18}"
    return await parser_data(url, num)


async def parser_data(url: str, num: int) -> tuple[list[str], list[list[str]], int]:
    text_list = []
    urls = []
    for _ in range(config.pixr_retry):
        try:
            async with session.get(url, proxy=config.pixr_local_proxy, timeout=5) as response:
                resp = feedparser.parse(await response.text())["entries"]
                break
        except TimeoutError:
            logger.warning("网络超时, 重试")
    else:
        return ["网络不太好，也许过一会就好了"], [], 998
    try:
        if len(resp) == 0:
            return ["没有搜索到喔"], [], 997
        if num > len(resp):
            num = len(resp)
        for data in resp[:num]:
            soup = BeautifulSoup(data["summary"], "lxml")
            title = f"标题：{data['title']}"
            pl = soup.find_all("p")
            author = pl[0].text.split("-")[0].strip()
            imgs = []
            text_list.append(f"{title}\n{author}\n")
            for p in pl[1:]:
                imgs.append(p.find("img").get("src"))
            urls.append(imgs)
    except ValueError:
        return ["是网站坏了啊，也许过一会就好了"], [], 999
    return text_list, urls, 200


async def download_pixiv_imgs(urls: list, user_id: str) -> UniMessage:
    result = UniMessage()
    for index, img in enumerate(urls):
        # async with aiohttp.ClientSession(headers=headers) as session:
        for _ in range(config.pixr_retry):
            try:
                async with session.get(
                    img, proxy=config.pixr_local_proxy, timeout=10, headers=headers
                ) as response:
                    raw = await response.read()
                    # print(response.url)
                    async with aiofiles.open(
                        (IMAGE_PATH / f"{user_id}_{index}_pixiv.jpg").resolve(), "wb"
                    ) as f:
                        await f.write(raw)
                    result.image(
                        path=f"file:///{IMAGE_PATH}/{user_id}_{index}_pixiv.jpg", mimetype="image/jpeg"
                    )
                    break
            except TimeoutError:
                logger.warning("网络超时, 重试")
        else:
            result += "\n这张图下载失败了..\n"
    return result
