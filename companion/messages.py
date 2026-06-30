"""Event -> speech-bubble + notification text.

All lines are cute and address the user as "主人". Lightly randomized so the
companion doesn't repeat itself; {name} is filled with the character's name.

Want to change what the companion says? Just edit the lists below — each event
maps to (notification-title, [bubble-text variants]). Add or remove lines
freely; keep "{name}" if you want the character's name spliced in.
"""
import random

# event_type -> (notification title, [bubble/body variants])
_TEXT = {
    "session_start": ("{name}来陪主人啦~", [
        "主人~ {name}上线啦，今天也一起加油鸭！",
        "主人好呀，人家来陪你写代码咯 ✨",
        "{name}来报到~ 主人今天想做点什么呢？",
        "嘿嘿，主人我来啦，有我在不怕 bug 哦！",
    ]),
    "done": ("搞定啦主人~ ✅", [
        "主人，任务完成啦~ 要不要摸摸我奖励一下嘛 ✨",
        "搞定收工！主人好厉害呀 (≧▽≦)",
        "这一轮做完啦~ 主人快来看看嘛！",
        "嘿嘿，又帮主人搞定一件事 🎉",
    ]),
    "error": ("呜…出小状况了主人 ⚠️", [
        "主人不好啦，代码闹脾气了 >_< 快来看看嘛~",
        "呜呜…这里好像报错了，主人救命呀！",
        "诶呀，出了点小状况，主人陪我一起看看好不好~",
        "卡住啦卡住啦，主人快来摸摸 bug 的头 😣",
    ]),
    "waiting": ("主人~ 人家在等你哦 👀", [
        "主人~ 人家在等你哦，戳一下嘛 👉👈",
        "在等主人的指示呢，不要丢下我呀~",
        "主人主人，轮到你啦，快回来嘛 🥺",
        "我乖乖等着主人哦 (｡･ω･｡)",
    ]),
    "goodbye": ("主人辛苦啦~ 👋", [
        "主人今天辛苦啦，记得早点休息哦 💤",
        "拜拜~ 主人要好好吃饭呀！",
        "先溜啦，主人明天也要元气满满哦 🌈",
        "下次见啦主人，想我了就喊我 (´｡• ᵕ •｡`)",
    ]),
    "idle": ("", ["…", "♪", "🌸", "ฅ^•ﻌ•^ฅ", "~"]),
}


def bubble(event_type, char=None, rng=None):
    rng = rng or random
    title, variants = _TEXT.get(event_type, _TEXT["idle"])
    name = (char or {}).get("name", "我")
    return rng.choice(variants).format(name=name)


def notification(event_type, char=None, rng=None):
    rng = rng or random
    title, _ = _TEXT.get(event_type, ("", [""]))
    name = (char or {}).get("name", "我")
    return title.format(name=name), bubble(event_type, char, rng)
