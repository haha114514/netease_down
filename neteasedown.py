import os
import sqlite3
import time
from hoshino import Service
from hoshino.typing import CQEvent
import requests
sv = Service("网易云下载")

api= 'https://v2.alapi.cn/api/music/url'
token = 'Your_api_token' # 请前往http://alapi.cn申请
DB_PATH = os.path.expanduser("~/.hoshino/limit_records.db") # 记录每日查询次数数据库路径
daily_limit_all = 1000 # API接口每日上限
daily_limit_user = 50 # 用户每日上限


class query_record:
    def __init__(self,key,db_path):
        self.db_path=db_path
        self.key=key
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._create_table()

    def connect(self):
        return sqlite3.connect(self.db_path)

    # 记录每日有API调用上限的token的使用情况的表，记录每日每用户调用次数（用于限制用户本身的调用次数）
    # key：使用的API名称（用于其它模块与该模块复用本表的情况）
    # date：日期，格式yyyymmdd
    # uid：调用API的用户QQ号
    # num：调用次数，uid填-1的行内此列数据为当日全用户调用总次数
    def _create_table(self):
        with self.connect() as conn:
            conn.execute(
                "create table if not exists token_limiter_day_user"
                "(key text not null, date int not null, uid int not null, num int not null, primary key(key, date, uid))"
            )

    # 获取特定用户当日调用次数
    def get_use_num(self, uid):
        with self.connect() as conn:
            r = conn.execute(
                "SELECT num FROM token_limiter_day_user WHERE key=? AND date=? AND uid=?", (self.key, time.strftime("%Y%m%d", time.localtime()), uid)
            ).fetchone()
            return r[0] if r else 0

    # 更新用户当日调用次数数据
    # 之所以不和下面那个函数合并是为了统计有没有人使用到每日次数上限后还在恶意刷屏（笑）
    def add_use_num(self, uid):
        num_user = self.get_use_num(uid)
        num_user += 1
        with self.connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO token_limiter_day_user (key, date, uid, num) VALUES (?, ?, ?, ?)",
                (self.key, time.strftime("%Y%m%d", time.localtime()), uid, num_user),
            )
        return num_user

    # 修改特定用户当日调用次数（用于给用户增加或减少当日可用调用次数，不影响当日总次数统计）
    def modify_use_num(self,uid, num_user):
        with self.connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO token_limiter_day_user (key, date, uid, num) VALUES (?, ?, ?, ?)",
                (self.key, time.strftime("%Y%m%d", time.localtime()), uid, num_user),
            )

    # 每次用户调用接口时先用此函数判断用户/总量是否超限并完成次数统计更新
    # limit_user与limit_all分别对应用户级和API级的调用上限
    def is_usable(self, uid, limit_user, limit_all):
        a = self.get_use_num(-1)
        b = self.add_use_num(uid)
        if a >= limit_all:
            return [-1, a, b]
        elif b > limit_user:
            return [0, a, b]
        else:
            a = self.add_use_num(-1)
            return [1, a, b]


db = query_record('ne_music_dl', DB_PATH)


@sv.on_prefix(('网易云下载'))
async def netease_down(bot, ev: CQEvent):
    uid = ev.user_id
    a = db.is_usable(uid, daily_limit_user, daily_limit_all)
    if a[0] == 1:
        kw = ev.message.extract_plain_text().strip()
        url = f'{api}?id={kw}&format=json&token={token}'
        song_info = requests.get(url).json()
        if song_info["code"] == 422:
            await bot.finish(ev, song_info["msg"] )
        elif song_info["code"] == 200:
            url = song_info["data"]["url"]
            encodeType = song_info["data"]["encodeType"]
            sv.logger.info('Download Link: ' + url)
            msg = f"下载链接：\n{url}\n格式：320Kbps-{encodeType}\n今日总计剩余查询次数：{daily_limit_all - a[1]}次，您剩余查询次数：{daily_limit_user - a[2]}次。"
            await bot.finish(ev, msg)
        elif song_info["code"] == 102:
            await bot.finish(ev, "哎呀，今天的羊毛好像薅了太多，被发现了……")
        elif song_info["code"] == 100 or song_info["code"] == 101:
            await bot.finish(ev, "请联系管理员更新账号或token。")
        elif song_info["code"] == 429:
            await bot.finish(ev, "薅羊毛速度太快，羊儿嫌疼了……")
        else:
            await bot.finish(ev, "未知错误～")
    elif a[0] == 0:
        msg = f"今日总计剩余查询次数：{daily_limit_all - a[1]}次，您剩余查询次数：{daily_limit_user - a[2]}次，您已超额。" + ("请不要继续尝试。" if a[2] - daily_limit_user >=5 else "")
        await bot.finish(ev, msg)
    elif a[0] == -1:
        msg = f"今日总计剩余查询次数：{daily_limit_all - a[1]}次，抱歉，请明日再尝试。"
        await bot.finish(ev, msg)
