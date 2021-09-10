from hoshino import Service
from hoshino.typing import CQEvent
import requests
sv = Service("网易云下载")

api= 'https://v2.alapi.cn/api/music/url'
token = 'Your_api_token' #请前往http://alapi.cn申请

@sv.on_prefix(('网易云下载'))
async def netease_down(bot, ev: CQEvent):
    kw = ev.message.extract_plain_text().strip()
    url = f'{api}?id={kw}&format=json&token={token}'
    song_info = requests.get(url).json()
    if song_info["code"] == 422:
        await bot.finish(ev, song_info["msg"] )
    elif song_info["code"] == 200:
        url = song_info["data"]["url"]
        encodeType = song_info["data"]["encodeType"]
        sv.logger.info('Download Link: ' + url)
        msg = f"下载链接：\n{url}\n格式：320Kbps{encodeType}"
        await bot.finish(ev, msg)
    else:
        await bot.finish(ev, "未知错误")
    
