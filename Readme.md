# European Blackjack (Blackjack_eu) 实现文档

## 一、项目整体理解

### 项目结构

该项目是一个基于 **Flask** 框架的 **Web 游戏中心**，目录结构如下：

```
games_center_work1_org/
├── flask_app.py              # Flask 主入口，定义路由
├── playcard.py               # 扑克牌工具模块（创建牌组、卡牌名称映射）
├── blackjack.py              # 标准21点游戏逻辑
├── blackjack_eu.py           # 欧洲21点游戏逻辑（本次修改目标）
├── static/
│   ├── base.css              # 全局样式
│   ├── blackjack.css         # 21点游戏专用样式
│   ├── svg-cards.svg         # SVG 卡牌精灵图
│   └── ...
└── templates/
    ├── base.html             # 基础模板（导航栏）
    ├── select.html           # 游戏选择页面
    ├── blackjack.html        # 标准21点游戏界面
    ├── blackjack_eu.html     # 欧洲21点游戏界面（本次修改目标）
    ├── rules.html            # 游戏规则页面
    ├── about.html            # 关于页面
    └── userlog.html          # 日志面板（日志系统未启用）
```

### 核心架构

1. **Flask Session 状态管理**：所有游戏状态（牌组、手牌、点数、消息）存储在 [`flask_app.py`](flask_app.py) 的 `session['game_state']` 字典中。
2. **游戏注册机制**：[`flask_app.py:7`](flask_app.py:7) 中 `SUPPORTED_GAMES = {'blackjack': blackjack, 'blackjack_eu': blackjack_eu}` 字典注册所有可用游戏。
3. **路由流程**：
   - `/select` → 选择游戏
   - `/select_game/<target_game>` → 设置当前游戏并初始化
   - `/game` → 渲染当前游戏模板
   - `/game_update/<action>` → 处理 Hit/Stand 等动作
4. **卡牌渲染**：通过 SVG `<use>` 标签引用 [`svg-cards.svg`](static/svg-cards.svg) 精灵图，如 `<use href="/static/svg-cards.svg#heart_10"/>`。
5. **Ace 智能处理**：[`calculate_hand_value()`](blackjack.py:22) 在手牌超过21点时自动将 Ace 从 11 降为 1。

### 数据流

```
用户访问 /select
    ↓ 点击游戏卡片
/select_game/blackjack_eu
    ↓ 调用 blackjack_eu.new_game(session)
    ↓ 重定向到 /game
/game → 渲染 blackjack_eu.html
    ↓ 玩家点击 Hit/Stand
/game_update/hit 或 /game_update/stand
    ↓ 调用 blackjack_eu.game_update(session, action)
    ↓ 重定向到 /game
/game → 显示更新后的状态或结果
```

## 二、欧洲版 vs 标准版对比总结

| 特性 | 标准 Blackjack [`blackjack.py`](blackjack.py) | 欧洲 Blackjack [`blackjack_eu.py`](blackjack_eu.py) |
|------|:---:|:---:|
| 庄家初始手牌 | 2张（1明+1暗） | **1张（全明）** |
| 初始检查庄家 Blackjack | ✅ 是 | ❌ 否（只有1张牌） |
| 玩家操作顺序 | 玩家先 Hit/Stand | 玩家先 Hit/Stand |
| 庄家获取第二张牌时机 | 发牌时已有暗牌 | **玩家 Stand 后才从牌堆抽取** |
| 庄家自然 Blackjack 特判 | 发牌时判断 | **玩家 Stand 后判断** |
| 多张牌21点 vs 自然Blackjack | 按点数平比 | **自然Blackjack 胜多张牌21点** |
| `player_has_natural` 追踪 | 无 | **新增字段记录** |
| 模板显示 | 始终显示2张牌 | **根据手牌长度动态显示** |

---

## 三、验证方法

1. 启动 Flask 应用：
   ```bash
   python flask_app.py
   ```
2. 访问 `http://localhost:80/select`
3. 点击 "Blackjack_eu" 开始游戏
4. 验证要点：
   - ✅ 庄家区域只显示1张明牌（无暗牌背）
   - ✅ 玩家可以正常 Hit/Stand
   - ✅ 玩家爆牌时游戏结束
   - ✅ 玩家 Stand 后庄家抽取第二张牌
   - ✅ 若庄家自然 Blackjack（A+10），庄家胜出
   - ✅ 若双方都是自然 Blackjack，平局
   - ✅ 无自然 Blackjack 时庄家补牌到17点后正常比大小
