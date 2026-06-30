<div align="center">

# 🐾 Companion Pet · 桌面陪伴小精灵

### *“主人~ 人家来陪你写代码啦 ✨”*

一个会**浮在你桌面上**的二次元小伙伴，
陪你开 **Claude Code / Codex**，在你**写完代码、报错、等待**时
奶声奶气地提醒你 —— 还会喊你「主人」哦 (´｡• ᵕ •｡`)

`ฅ^•ﻌ•^ฅ`　`(≧▽≦)`　`(｡･ω･｡)`　`>_<`　`🌸`

</div>

---

## 🌟 这是什么

启动 Claude Code（或 Codex）时，它会**随机抽一个角色**出现在桌面角落，
真透明、无边框，像真的小宠物一样浮在屏幕上。然后在关键时刻给你软萌提醒：

> 🎀 「主人，任务完成啦~ 要不要摸摸我奖励一下嘛 ✨」
> 🎀 「主人不好啦，代码闹脾气了 >_< 快来看看嘛~」
> 🎀 「主人~ 人家在等你哦，戳一下嘛 👉👈」

自带 6 个**原创小可爱**，更棒的是 —— **你可以放任何你喜欢的角色图**（蕾姆、芙宁娜、皮卡丘、倒霉熊…随你！）。

---

## ✨ 特性

| | |
|---|---|
| 🪟 **真透明浮窗** | PySide6 逐像素透明，角色干净地浮在桌面，无背景无边框 |
| 🎲 **随机出场** | 每次开会话随机抽一个角色陪你 |
| 💬 **软萌提醒** | 完成 / 报错 / 等待 / 结束，都有可爱的「主人」文案 + 系统通知 |
| 🖼️ **自带角色 + 自定义** | 6 个原创吉祥物，外加你自己的任意 PNG/GIF |
| 🖱️ **可拖动** | 拖到任意位置，双击隐藏，右键换角色 |
| 🖥️ **跨平台** | macOS / Windows / Linux 都能用 |
| 🪶 **零负担** | 不打扰、不抢焦点，纯本地运行，不联网 |

---

## 🚀 安装

### macOS / Linux

```bash
./install.sh
```
然后在 Claude Code 里注册一次（以后每次开会话自动启动）：
```
/plugin marketplace add /你的路径/companion-pet
/plugin install companion-pet@companion-pet-marketplace
```

### Windows（PowerShell）

```powershell
./install.ps1      # 自动建 venv、装 PySide6、把 hook 写进 settings.json
```
装好后重启 Claude Code 即可。

> 💡 没有 PySide6 也没关系：会自动降级成 tkinter 卡片，再不行就纯系统通知，**任何机器都能跑**。

---

## 🎮 使用

装好插件后**什么都不用做** —— 每次开 Claude Code 会话，小可爱会自己蹦出来陪你 🎉

也可以手动用命令（macOS/Linux 用 `bin/companion`，Windows 用 `bin\companion.cmd`）：

```bash
bin/companion start      # 让小可爱出场
bin/companion demo       # 演示一遍所有提醒
bin/companion list       # 看看角色池里都有谁
bin/companion add 图.png  # 添加一个新角色
bin/companion stop       # 让它先去休息
bin/companion status     # 看看运行状态
```

**桌面上的交互**：　🖐️ 拖动移动　·　👆👆 双击隐藏　·　🖱️ 右键 → 换一个角色 / 隐藏 / 退出

---

## 🐾 换成你喜欢的角色（放图片）

超简单！把图片丢进角色文件夹，自动加入随机池：

```bash
# 方法一：命令添加（推荐，自动放好）
bin/companion add ~/Downloads/蕾姆.png

# 方法二：直接把图片拖进这个文件夹
#   macOS / Linux :  ~/.companion/characters/
#   Windows       :  %USERPROFILE%\.companion\characters\
```

**图片要求** 📋

| 项目 | 要求 |
|---|---|
| 格式 | **PNG 或 GIF**（JPG 请先转 PNG，见下） |
| 背景 | 建议**透明背景**，浮在桌面最好看 |
| 尺寸 | 任意！会自动缩放，正方形最佳 |
| 名字 | **文件名 = 角色名字，由你自己定** 🏷️ |

> 🏷️ **关于名字**：桌面上**不会**显示名字标签（保持画面干净）。
> 但**角色名 = 你的图片文件名**，会出现在打招呼的气泡里 —— 比如文件叫
> `蕾姆.png`，它就会说「**蕾姆**来陪主人啦~」。想叫什么，把文件改名就行；
> 不想要名字露出，把台词里的 `{name}` 删掉即可（见下方「改台词」）。

**白底图想抠成透明？** 自带工具一键搞定（纯本地，不联网）：
```bash
# JPG 先转 PNG（macOS 自带 sips）：
sips -s format png 图.jpg --out 图.png
# 去白底变透明：
python3 scripts/remove_bg.py 图.png
# 白身体白背景（如线稿小熊）封不住开口？加大闭合半径：
COMPANION_CLOSE=16 python3 scripts/remove_bg.py 图.png
```

> 🎯 **挑图小贴士**：选**透明背景 / 纯色背景**的角色立绘（render）最好；
> 带边框、文字、复杂背景的"卡片插画"不适合当桌宠哦。

### 🆓 去哪儿找图？（免费素材推荐）

**完全免费、可商用、可公开分享（CC0，放心用）👇**

| 来源 | 说明 |
|---|---|
| [Kenney](https://kenney.nl/assets) · [itch 版](https://kenney-assets.itch.io/) | 6 万+ 免费游戏素材，统一可爱风，CC0 零门槛 |
| [itch.io chibi 精灵](https://itch.io/game-assets/tag-chibi) · [免费筛选](https://itch.io/game-assets/free/tag-chibi/tag-sprites) | 一堆社区做的 Q 版小人 |
| [いらすとや](https://www.irasutoya.com/) | 日本超火的免费可爱插画，海量小动物/吉祥物透明 PNG |
| [OpenGameArt 等导航](https://www.hackingtons.com/free-game-art.html) | 免费游戏美术资源汇总 |

**二次元角色透明 PNG（搜「角色名 + png/render」，个人本地使用）👇**

[PNGKey](https://www.pngkey.com/pngs/anime-character/) · [CleanPNG](https://www.cleanpng.com/free/anime.html) · [NicePNG](https://www.nicepng.com/s/anime-characters/) · [PNGAnime](https://pnganime.com/) · [PNGItem](https://www.pngitem.com/so/anime-characters/) · [PNGAAA](https://www.pngaaa.com/search/anime-characters-png/) · [HiClipart](https://www.hiclipart.com/search?clipart=anime+Render)

> ⚠️ 角色版权图仅建议**个人本地**当桌宠用，别二次分发/商用；想公开分享请用上面的 CC0 素材。

### 🎀 示例角色（作者的收藏）

仓库 `examples/characters/` 里放了几个抠好的示例角色，想用的话复制到你的角色文件夹即可：

```bash
# macOS / Linux
cp examples/characters/*.png ~/.companion/characters/
# Windows (PowerShell)
copy examples\characters\*.png $env:USERPROFILE\.companion\characters\
```

<p align="center">
  <img src="examples/characters/蕾姆.png" height="92" />
  <img src="examples/characters/草神.png" height="92" />
  <img src="examples/characters/皮卡丘.png" height="92" />
  <img src="examples/characters/三玖.png" height="92" />
  <img src="examples/characters/自嘲熊.png" height="92" />
</p>

> 📛 **版权声明 / Disclaimer**：`examples/` 内的二次元角色图，版权归各自原作者
> 及版权方所有，此处**仅作个人桌宠演示用途**，不作任何商业用途。若版权方认为
> 不妥，请提 [Issue](https://github.com/OvOhao/companion-pet/issues)，我会**立即移除**。
> 自带的 `assets/builtin/` 小可爱则是本项目原创，可自由使用。

---

## 💬 改成你想说的话

想让它说别的？只要改一个文件：**`companion/messages.py`** 🖊️

里面是一张「事件 → 文案」表，每个事件对应 *(通知标题, [气泡台词列表])*，
随便加、随便删，保留 `{name}` 就能自动嵌进角色名：

```python
_TEXT = {
    "done": ("搞定啦主人~ ✅", [
        "主人，任务完成啦~ 要不要摸摸我奖励一下嘛 ✨",
        "搞定收工！主人好厉害呀 (≧▽≦)",
        "{name}又帮主人搞定一件事 🎉",   # ← {name} 会变成角色名
        # 在这里加你自己的台词 👇
    ]),
    ...
}
```

可改的事件：`session_start`（上线）· `done`（完成）· `error`（报错）· `waiting`（等待）· `goodbye`（结束）· `idle`（发呆）。
改完重启一下 `bin/companion stop && bin/companion start` 就生效啦~

---

## 🪄 什么时候会提醒我

| Claude Code 发生了… | 小可爱的反应 |
|---|---|
| 🟢 开始会话 | 蹦出来 + 「{name}来陪主人啦~」 |
| ✅ 回答完成 | 「主人，任务完成啦~」 |
| ⚠️ 命令报错 | 「主人不好啦，代码闹脾气了 >_<」 |
| 👀 等你确认 | 「主人~ 人家在等你哦」 |
| 👋 会话结束 | 「主人辛苦啦，记得早点休息哦 💤」 |

---

## 🖥️ 平台 & 工作原理

```
Claude Code 钩子 ─┐                        ┌─ PySide6 透明浮窗（真·桌面宠物）
Codex notify ────┼─ companion ──本地TCP─────┤   ↘ 降级：tkinter 卡片
                 │   (任意 python3)  +token  └─ 系统通知（mac/win/linux）
                 └─ 浮窗起不来时，自动退回系统通知，绝不漏提醒
```

- **GUI**：PySide6（跨平台真透明）
- **通信**：本地回环 TCP + 随机 token 鉴权（不开放端口、不联网）
- **通知**：osascript(mac) / PowerShell toast(win) / notify-send(linux)
- **降级链**：透明浮窗 → tkinter 卡片 → 纯通知，**总有一档能用**

## 🔌 Codex 接入（可选）

在 `~/.codex/config.toml` 加一行：
```toml
notify = ["python3", "/你的路径/companion-pet/scripts/codex-notify.py"]
```

---

## 💖 欢迎来玩 & 给个 Star 吧

这个小项目是用爱发电做的，希望能给每个敲代码的你带来一点点陪伴和快乐 (´｡• ᵕ •｡`)

- 🌟 **喜欢的话，点个 Star 支持一下嘛~** 这是对作者最大的鼓励啦！
- 🐛 **遇到 bug / 有想法**？欢迎来 [Issues](https://github.com/OvOhao/companion-pet/issues) 提，我会认真看每一条！
- 🎨 **做了好看的角色 / 改了有趣的台词**？欢迎 PR 分享给大家～
- 💌 不管是吐槽还是夸夸，都超欢迎，主人们的反馈是更新的动力！

> ⭐️ 仓库地址：`https://github.com/OvOhao/companion-pet` *（按你的实际仓库修改）*

<div align="center">

### 谢谢你看到这里，记得给小可爱点个 ⭐️ 哦~

`ฅ^•ﻌ•^ฅ`　「主人，要一直一起写代码哦~」

</div>
