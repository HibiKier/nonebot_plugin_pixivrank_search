from nonebot import get_plugin_config
from pydantic import Extra, BaseModel


class Config(BaseModel, extra=Extra.ignore):
    pixr_local_proxy: str
    pixr_rsshub: str = "https://rsshub.app/"
    pixr_retry: int = 3


config = get_plugin_config(Config)

config.pixr_rsshub = config.pixr_rsshub[:-1] if config.pixr_rsshub[-1] == "/" else config.pixr_rsshub
