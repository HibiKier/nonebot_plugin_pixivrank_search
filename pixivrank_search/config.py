from pydantic import BaseModel, Extra
from nonebot import get_driver


class Config(BaseModel, extra=Extra.ignore):
    local_proxy: str
    rsshub: str = "https://rsshub.app/"


config = Config.parse_obj(get_driver().config)

config.rsshub = config.rsshub[:-1] if config.rsshub[-1] == "/" else config.rsshub
