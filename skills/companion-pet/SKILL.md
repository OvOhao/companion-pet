---
name: companion-pet
description: Control the companion-pet desktop companion (桌面陪伴小精灵) for Claude Code/Codex. Use when the user wants to start/show/hide/stop the desktop pet, switch or add a character image, list characters, change what it says (台词/通知文案), check status, or install it. Triggers include "桌宠", "陪伴小精灵", "启动/关闭桌宠", "换个角色", "把这张图加进桌宠/加个角色", "我的桌宠有哪些角色", "改一下桌宠说的话", "companion pet", "show/hide my pet", "desktop pet".
---

# Companion Pet 控制

桌面上一个会浮在屏幕角落、陪用户开 Claude Code/Codex 的二次元小精灵，会在
完成/报错/等待时用「主人」口吻软萌提醒。这个 skill 让你**用自然语言指挥它**。

## 先找到 CLI

所有操作都通过本 skill 目录下的 `companion` 包装脚本执行，它会自动定位真正的
companion-pet 安装位置（插件目录 / 用户克隆的仓库）：

```bash
"<skill_dir>/companion" <子命令>
```

`<skill_dir>` 就是本 SKILL.md 所在目录。先用它跑一次 `status` 确认能找到安装；
如果报 "CLI not found"，让用户告诉你仓库路径，然后用
`COMPANION_ROOT=/path/to/companion-pet "<skill_dir>/companion" status` 重试，
并提示用户：还没安装的话先去仓库跑 `./install.sh`（Windows 用 `./install.ps1`）。

## 命令速查

| 用户意图 | 执行 |
|---|---|
| 启动 / 显示桌宠 | `companion start` |
| 关闭 / 让它休息 | `companion stop` |
| 查看运行状态、角色数、GUI 后端 | `companion status` |
| 列出所有角色 | `companion list` |
| 添加一个角色图 | `companion add <图片路径>` |
| 演示一遍所有提醒 | `companion demo` |
| 手动触发某事件 | `companion event <session_start\|done\|error\|waiting\|goodbye>` |

## 常见任务怎么做

**「帮我启动桌宠 / 关掉它」**
→ `companion start` 或 `companion stop`，然后简短确认。

**「把这张图加进桌宠 / 加个角色」**（用户给了图片路径）
1. 跑 `companion add <路径>`（自动复制进角色池，文件名就是角色名）。
2. 检查它是不是白底不透明：`sips -g hasAlpha <路径>`（mac）。若是白底，建议/帮他抠成
   透明：`python3 <repo>/scripts/remove_bg.py <角色文件夹>/<文件名>`；
   白身体白背景的线稿用 `COMPANION_CLOSE=16 python3 .../remove_bg.py ...`。
3. `companion list` 确认，提示重启或右键「换一个角色」即可看到。
   - JPG/WebP 先转 PNG：`sips -s format png in.jpg --out out.png`。

**「换一个角色」**
→ 桌面上**右键小精灵 → 换一个角色** 可循环切换（随机）。也可以
`companion stop && companion start` 重新随机抽一个。

**「我的桌宠有哪些角色」**
→ `companion list`，把 `[yours]`（用户自己的）和 `[builtin]`（内置原创）分类念给他。

**「改一下桌宠说的话 / 通知文案」**
→ 编辑仓库里的 `companion/messages.py`，里面是「事件 → (通知标题, [气泡台词列表])」
表，每个事件可加删台词，保留 `{name}` 会自动填角色名。改完
`companion stop && companion start` 生效。可改事件：session_start / done / error /
waiting / goodbye / idle。

**「装到 Claude Code / 让它每次自动出现」**
→ 桌宠的自动出场靠 plugin 的 hooks。指导用户：
`/plugin marketplace add <仓库路径>` 然后
`/plugin install companion-pet@companion-pet-marketplace`，重启会话即生效。
Windows 用户改跑 `./install.ps1`（会把 hook 写进 settings.json）。

## 注意
- 它是一个后台 GUI 守护进程，一个进程服务所有会话；纯本地、不联网。
- 跨平台（macOS/Windows/Linux），GUI 用 PySide6 真透明，缺依赖时自动降级为
  tkinter 卡片或纯系统通知。
- 改动是面向用户桌面的可见行为，启停/换角色这类直接执行即可；不确定路径时先问用户。
