# Yiping Cheng's Games Center — 项目文档

## 一、项目结构

```
games_center_work1_org/
│
├── flask_app.py              # Flask 主入口，定义路由
├── playcard.py               # 扑克牌工具模块（牌组创建、卡牌映射、排名）
├── requirements.txt          # Python 依赖（Flask, Gunicorn）
├── .gitignore                # Git 忽略规则
│
├── blackjack.py              # 标准21点游戏逻辑
├── blackjack_eu.py           # 欧洲21点游戏逻辑
├── whist.py                  # 惠斯特（Whist）游戏逻辑 [占位代码，尚未完全实现]
│
├── static/
│   ├── base.css              # 全局样式（导航栏、布局）
│   ├── blackjack.css         # 21点游戏专用样式
│   ├── whist.css             # Whist 游戏专用样式（四人桌布局、中央牌池）
│   ├── whist.js              # Whist 前端交互脚本（选牌、出牌、按钮）
│   ├── svg-cards.svg         # SVG 卡牌精灵图（完整52张牌）
│   ├── *.svg                 # 花色图标（club, diamond, heart, spade, arrow-down）
│   └── favicon.ico           # 网站图标
│
└── templates/
    ├── base.html             # 基础模板（导航栏菜单）
    ├── select.html           # 游戏选择页面
    ├── blackjack.html        # 标准21点游戏界面
    ├── blackjack_eu.html     # 欧洲21点游戏界面（只显示1张庄家牌）
    ├── whist.html            # Whist 四人桌牌界面
    ├── rules.html            # 游戏规则页面
    ├── about.html            # 关于页面
    └── userlog.html          # 日志面板
```

---

## 二、核心架构

### 2.1 Flask Session 状态管理

所有游戏状态存储在 Flask 的 `session['game_state']` 字典中，无需数据库。

```python
session['game_state'] = {
    'deck': [...],           # 剩余牌组
    'dealer_hand': [...],    # 庄家手牌
    'player_hand': [...],    # 玩家手牌
    'dealer_value': ...,     # 庄家点数
    'player_value': ...,     # 玩家点数
    'message': ...,          # 结果消息
    'message_class': ...,    # 消息CSS类
}
```

### 2.2 游戏注册机制

[`flask_app.py:8`](flask_app.py:8) 中通过 `SUPPORTED_GAMES` 字典注册所有可用游戏：

```python
SUPPORTED_GAMES = {
    'blackjack': blackjack,
    'blackjack_eu': blackjack_eu,
    'whist': whist,
}
```

### 2.3 路由流程

| 路由 | 功能 | 修改说明 |
|------|------|----------|
| `/` → `/game` | 首页重定向到游戏页 | - |
| `/select` | 游戏选择页 | - |
| `/select_game/<target_game>` | 选择游戏并初始化 | - |
| `/new_game` | 重新开始当前游戏 | - |
| `/game` | 渲染当前游戏模板 | - |
| `/game_update/<path:action>` | 处理游戏动作 | 原 `<action>` 改为 `<path:action>`，支持多段动作如 `play/<card>` |
| `/rules` | 规则页面 | - |
| `/log` | 用户日志 | - |
| `/about` | 关于页面 | - |

### 2.4 卡牌系统

- **牌张表示**：2字符字符串 `[rank][suit]`，如 `"AS"`=黑桃A
- **花色**：`S`(♠)、`H`(♥)、`D`(♦)、`C`(♣)
- **渲染**：通过 SVG `<use>` 标签引用 [`svg-cards.svg`](static/svg-cards.svg) 精灵图
- **公共函数**：`get_card_name()` 通过 [`flask_app.py:85`](flask_app.py:85) 的上下文处理器注入所有模板

---

## 三、游戏详解

### 3.1 标准 Blackjack ([`blackjack.py`](blackjack.py))

| 特性 | 说明 |
|------|------|
| **发牌** | 庄家2张（1明1暗），玩家2张 |
| **初始检查** | 检查庄家是否为 Blackjack（A+10点牌） |
| **玩家操作** | Hit（要牌）/ Stand（停牌） |
| **庄家规则** | 自动补牌到17点 |
| **胜负判定** | 比点数，爆牌则输 |

### 3.2 欧洲 Blackjack ([`blackjack_eu.py`](blackjack_eu.py))

| 特性 | 说明 |
|------|------|
| **发牌** | 庄家**只发1张明牌**（无暗牌/Hole Card） |
| **初始检查** | ❌ 不检查庄家 Blackjack（只有1张牌，不可能） |
| **玩家操作** | 玩家先完成所有 Hit/Stand 操作 |
| **庄家抽第二张牌** | 玩家 Stand **后**庄家才从牌堆抽取第二张牌 |
| **自然 Blackjack 特判** | 庄家头两张牌=21 且玩家非自然BJ → 庄家胜；双方都是自然BJ → 平局 |
| **其余规则** | 与标准 Blackjack 一致 |

**修改要点**（与标准版的核心差异）：
- [`new_game()`](blackjack_eu.py:39)：从牌堆抽3张牌（原4张），庄家仅持有1张
- [`game_update()` — `stand` 动作](blackjack_eu.py:108)：庄家抽第二张牌后先检查自然 Blackjack，再决定是否继续补牌
- [`player_has_natural`](blackjack_eu.py:56) 字段追踪玩家是否为自然 Blackjack

### 3.3 Whist (惠斯特) — [`whist.py`](whist.py)、[`whist.html`](templates/whist.html)、[`whist.js`](static/whist.js)、[`whist.css`](static/whist.css)

> ⚠️ **当前状态**：前端界面已完整实现，后端逻辑文件 [`whist.py`](whist.py) 中包含占位代码（`...`），尚未完全实现。

#### Whist 游戏规则

Whist 是一种经典的四人**吃墩**（Trick-taking）纸牌游戏：

| 规则 | 说明 |
|------|------|
| **玩家** | 4人，固定搭档：**南北** vs **东西** |
| **牌组** | 标准52张牌，每人13张 |
| **王牌** | 每局随机指定一种花色为王牌（Trump） |
| **出牌** | 顺时针方向，必须跟出同花色牌（Follow Suit） |
| **吃墩** | 无同花色牌时可出王牌或其他花色 |
| **计分** | 每赢一墩得1分，全部13墩打完结算 |
| **胜负** | 南北总分 vs 东西总分 |

#### 前端架构

[`whist.html`](templates/whist.html) 使用 CSS Grid 布局模拟四人牌桌：

```
┌─────────────────────────────────────────┐
│              North (AI)                  │
│            ♠ ♥ ♦ ♣ (手牌)               │
│                                          │
│  West (AI)    中央牌池      East (AI)    │
│  ♠ ♥ ♦ ♣   ┌─────────┐   ♠ ♥ ♦ ♣      │
│  (竖排)     │  出牌区  │   (竖排)        │
│             │  消息/按钮│                 │
│             │ 王牌 计分│                 │
│             └─────────┘                  │
│              South (你)                   │
│            ♠ ♥ ♦ ♣ (可点击)              │
└─────────────────────────────────────────┘
```

- `stop_type` 状态机：`new_trick` → `lead_card` → `follow_card` → (出牌) → `new_trick` → ... → `game_over`
- [`whist.js`](static/whist.js) 处理：卡牌可选性判断（必须跟同花色）、选中高亮、Proceed 按钮
- [`whist.css`](static/whist.css) 处理：90°旋转的东西手牌、中央牌池的金边绿底、卡牌悬停效果

#### 后端状态字段（`game_state`）

```python
{
    'players': {'north': 'Alice', 'south': 'You', 'east': 'Bob', 'west': 'Charlie'},
    'hands': {'north': [...], 'south': [...], 'east': [...], 'west': [...]},
    'trump_suit': 'S',          # 王牌花色
    'trump_suit_name': 'spade',  # 王牌名称（用于图标）
    'stop_type': 'new_trick',   # 状态：new_trick/lead_card/follow_card/game_over
    'leader': 'north',          # 当前领出者
    'tricks': [],               # 已完成的墩列表
    'scores': {'south_north': 0, 'east_west': 0},
    'message': None,
    'message_class': "info-message",
}
```

#### 已知待完成事项

1. **`whist.py` 后端逻辑**：`new_game()` 和 `game_update()` 函数需要填充完整实现
2. **`playcard.py` 缺少 `get_suit_name`**：`whist.py:2` 导入了 `get_suit_name`，但该函数尚未在 [`playcard.py`](playcard.py) 中定义
3. **`templates/select.html`**：尚未添加 Whist 游戏选择入口
4. **`templates/rules.html`**：尚未添加 Whist 规则说明

---

## 四、修改记录

### v1.0 → v1.1 — 欧洲 Blackjack 实现

| 文件 | 修改 |
|------|------|
| [`blackjack_eu.py`](blackjack_eu.py) | 重写 `new_game()` 和 `game_update()`，实现欧洲规则 |
| [`templates/blackjack_eu.html`](templates/blackjack_eu.html) | 根据庄家手牌长度动态显示卡牌 |
| [`DOCUMENTATION.md`](DOCUMENTATION.md) | 新增本文档 |

### v1.1 → v1.2 — Whist 游戏框架

| 文件 | 修改 |
|------|------|
| [`whist.py`](whist.py) | 新增 Whist 后端（占位代码） |
| [`templates/whist.html`](templates/whist.html) | 新增四人桌牌界面 |
| [`static/whist.css`](static/whist.css) | 新增 Whist 样式 |
| [`static/whist.js`](static/whist.js) | 新增 Whist 前端交互脚本 |
| [`flask_app.py`](flask_app.py) | 注册 `whist` 模块；路由 `game_update` 改为 `<path:action>` |
| [`DOCUMENTATION.md`](DOCUMENTATION.md) | 更新本文档 |

---

## 五、部署说明

### 本地运行

```bash
pip install -r requirements.txt
python flask_app.py
# 访问 http://localhost:80
```

### Render 部署

| 配置项 | 值 |
|--------|-----|
| **Runtime** | Python 3 |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn flask_app:app` |
| **环境变量** | `FLASK_SECRET_KEY` — 设置随机字符串用于 session 签名 |
