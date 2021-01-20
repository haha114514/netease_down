from hoshino import Service
from hoshino.typing import CQEvent
import requests
import json
from requests import get
import time
import re
se = requests.session()


sv = Service("网易云下载")
@sv.on_prefix(('网易云下载'))
async def yxh(bot, ev: CQEvent):
    kw = ev.message.extract_plain_text().strip()
    arr = kw.split('/')
    url = 'https://v1.alapi.cn/api/music/url?id=' + str(arr[0]) + '&format=json'
    r=requests.get(url)
    song_info=r.json()
    url = song_info["data"]["url"]
    encodeType = song_info["data"]["encodeType"]
    print (url)
    msg = "这首歌的下载链接是\n" + str(url) + " \n格式为:320Kbps " + str(encodeType)
    print (msg)
    await bot.send(ev, msg)
    