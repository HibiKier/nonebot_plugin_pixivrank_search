from datetime import datetime

from nonebot import require
from nonebot.adapters import Event
from nonebot.plugin import PluginMetadata, inherit_supported_adapters

require("nonebot_plugin_alconna")

from nepattern import SwitchPattern, combine
from nepattern.base import CustomMatchPattern
from arclet.alconna import Args, Field, Option, Alconna, CommandMeta, store_true
from nonebot_plugin_alconna import Match, Query, MsgTarget, UniMessage, on_alconna

from .config import Config
from .util import UserExistLimiter
from .data_source import get_pixiv_urls, search_pixiv_urls, download_pixiv_imgs

__plugin_meta__ = PluginMetadata(
    name="PixivRankSearch",
    description="基于RSSHUB阅读器实现的获取P站排行和P站搜图",
    usage="""\
p站排行 [type] [count] [date]
搜图 [tag] [count] [sort] [r18]
    """,
    homepage="https://github.com/HibiKier/nonebot_plugin_pixivrank_search",
    type="application",
    config=Config,
    supported_adapters=inherit_supported_adapters("nonebot_plugin_alconna"),
    extra={
        "author": "HibiKier",
        "priority": 3,
        "version": "0.2.0",
    },
)

rank_dict = {
    "1": "day",
    "2": "week",
    "3": "month",
    "4": "week_original",
    "5": "week_rookie",
    "6": "day_r18",
    "7": "week_r18",
    "8": "day_male_r18",
    "9": "week_r18g",
}

_ulmt = UserExistLimiter()

RankPat = SwitchPattern(rank_dict)  # type: ignore
RankPat = combine(RankPat, alias="Rank")


def check_date(_, date):
    datetime.strptime(date, "%Y-%m-%d")
    return date


Date = CustomMatchPattern(str, check_date, "Date")


rank = Alconna(
    "p站排行",
    Args["rank#R18仅可私聊", RankPat, "day"]["count?", int]["date?", Date],
    meta=CommandMeta(
        "获得P站排行榜",
        usage="""\
p站排行榜 <类型> [数量] [日期]
其中类型为：
1. 日排行
2. 周排行
3. 月排行
4. 原创排行
5. 新人排行
6. R18日排行
7. R18周排行
8. R18受男性欢迎排行
9. R18重口排行【慎重！】
""",
        example="""\
p站排行   （无参数默认为日榜）
p站排行 1
p站排行 1 5
p站排行 1 5 2018-4-25
    """,
        hide_shortcut=True,
        fuzzy_match=True,
    ),
)

search = Alconna(
    "搜图",
    Args["tag", str]["count?", int]["sort#热度排序/时间排序", [1, 2], Field(1, alias="热度排序")],
    Option("r18", action=store_true, default=False, help_text="是否开启 R18，仅可私聊"),
    meta=CommandMeta(
        "搜索P站图片",
        usage="""\
搜图 <关键词> [数量] [排序方式] [r18]
其中排序方式为：
1. 热度排序
2. 时间排序
""",
        example="""\
搜图 樱岛麻衣
搜图 樱岛麻衣 5 1
搜图 樱岛麻衣 5 2 r18
""",
        hide_shortcut=True,
        fuzzy_match=True,
    ),
)

pixiv_rank = on_alconna(
    rank,
    aliases={"P站排行", "p站排行榜", "P站排行榜"},
    priority=5,
    block=True,
    use_cmd_start=True,
    auto_send_output=True,
    skip_for_unmatch=False,
)
pixiv_search = on_alconna(
    search, priority=5, block=True, use_cmd_start=True, skip_for_unmatch=False, auto_send_output=True
)


@pixiv_rank.handle()
async def _(target: MsgTarget, rank: str, count: Match[int], date: Match[str], event: Event):

    code = 0
    text_list = ["失败了..."]
    if not count.available:
        _count = 1
    else:
        _count = count.result
    if "r18" in rank and not target.private:
        await UniMessage.text("羞羞脸！私聊里自己看！").finish(at_sender=True)
    if _ulmt.check(event.get_user_id()):
        await pixiv_rank.finish("P站排行榜正在搜索噢，不要重复触发命令呀")
    _ulmt.set_true(event.get_user_id())
    text_list, urls, code = await get_pixiv_urls(rank, _count, date.result if date.available else "")
    if code != 200:
        _ulmt.set_false(event.get_user_id())
        await pixiv_rank.finish(text_list[0])
    elif not text_list or not urls:
        _ulmt.set_false(event.get_user_id())
        await UniMessage.text("没有找到啊，等等再试试吧~V").finish(at_sender=True)
    else:
        for i in range(len(text_list)):
            try:
                await (text_list[i] + await download_pixiv_imgs(urls[i], event.get_user_id())).send()
            except Exception as e:
                await UniMessage.text(f"这张图网络炸了！:{e!r}").finish(at_sender=True)
                # await pixiv_keyword.send('这张图网络炸了！', at_sender=True)
    _ulmt.set_false(event.get_user_id())


@pixiv_search.handle()
async def _(
    target: MsgTarget,
    event: Event,
    tag: str,
    sort: int,
    count: Match[int],
    r18: Query[bool] = Query("r18.value"),
):
    if r18.result and not target.private:
        await UniMessage.text("(脸红#) 你不会害羞的 八嘎！").finish(at_sender=True)
    if not r18.result:
        _r18 = 1
    else:
        _r18 = 2
    if _ulmt.check(event.get_user_id()):
        await pixiv_rank.finish("P站关键词正在搜索噢，不要重复触发命令呀")
    _ulmt.set_true(event.get_user_id())
    order = "popular" if sort == 1 else "date"
    num = count.result if count.available else 5
    text_list, urls, code = await search_pixiv_urls(tag, num, order, _r18)
    if code != 200:
        _ulmt.set_false(event.get_user_id())
        await pixiv_rank.finish(text_list[0])
    elif not text_list or not urls:
        _ulmt.set_false(event.get_user_id())
        await UniMessage.text("没有找到啊，等等再试试吧~V").finish(at_sender=True)
    else:
        for i in range(len(text_list)):
            try:
                await (text_list[i] + await download_pixiv_imgs(urls[i], event.get_user_id())).send()
            except Exception as e:
                await UniMessage.text(f"这张图网络炸了！:{e!r}").finish(at_sender=True)
    _ulmt.set_false(event.get_user_id())
