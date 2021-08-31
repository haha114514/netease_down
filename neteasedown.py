from hoshino import Service
from hoshino.typing import CQEvent
import requests
se = requests.session()


sv = Service("网易云下载")


@sv.on_prefix(('网易云下载'))
async def yxh(bot, ev: CQEvent):
    kw = ev.message.extract_plain_text().strip()
    arr = kw.split('/')
    url = 'https://v.alapi.cn/api/music/url?id=' + str(arr[0]) + '&format=json'
    r = requests.get(url)
    song_info = r.json()
    url = song_info["data"]["url"]
    encodeType = song_info["data"]["encodeType"]
    sv.logger.info('Download Link: ' + url)
    msg = "下载链接：\n" + str(url) + " \n格式：320Kbps " + str(encodeType)
    await bot.send(ev, msg)
