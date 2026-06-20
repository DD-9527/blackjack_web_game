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

---

## 二、修改思路

### 原代码问题

修改前，[`blackjack_eu.py`](blackjack_eu.py) 的代码与 [`blackjack.py`](blackjack.py) 几乎完全一致，**并没有真正实现欧洲21点规则**。具体问题如下：

| 问题 | 标准版 (blackjack.py) | 原欧洲版 (blackjack_eu.py - 错误) | 正确的欧洲版行为 |
|------|----------------------|-----------------------------------|------------------|
| **发牌** | 庄家2张牌（1明1暗） | 同标准版，立即抽出 card4 加入庄家手牌 | 庄家只发1张明牌 |
| **初始检查** | 检查庄家是否为 Blackjack | 同标准版，检查 `dealer_total_value == 21` | 庄家只有1张牌，不可能 Blackjack，不应检查 |
| **玩家行动** | 玩家先 Hit/Stand | 同标准版 | 同标准版，玩家先行动 |
| **庄家抽第二张牌** | 玩家 Stand 后，庄家亮出暗牌 | 同标准版（但暗牌 card4 早已加入） | **玩家 Stand 后，庄家才从牌堆抽取第二张牌** |
| **自然 Blackjack** | 发牌时立刻判断 | 同标准版 | 玩家 Stand 后，庄家抽第二张牌，检查是否为自然 Blackjack。若是则庄家胜（除非玩家也有自然 Blackjack） |

### 修改目标

根据欧洲 Blackjack 的规则要求：

1. **发牌时庄家只发1张明牌**，不预先发放暗牌
2. **玩家操作前不检查庄家 Blackjack**（因为庄家只有1张牌，不可能构成 Blackjack）
3. **玩家先完成所有操作**（Hit 或 Stand），直到停牌或爆牌
4. **玩家停牌后，庄家才抽取第二张牌**
5. **庄家自然 Blackjack 特殊规则**：若庄家头两张牌为 21（A + 10点牌），则庄家获胜或平局——玩家也是自然 Blackjack 则平局，否则庄家胜
6. 其余规则（胜负判断、爆牌规则等）保持与标准版一致

---

## 三、具体修改内容

### 修改 1：[`blackjack_eu.py`](blackjack_eu.py) — `new_game()` 函数

**原代码（第39-79行）**：
```python
# 从牌堆抽出4张牌
card1, card2, card3, card4 = deck.pop(), deck.pop(), deck.pop(), deck.pop()
player_hand = [card1, card3]
dealer_hand = [card2]
# ...计算点数...
dealer_hand.append(card4)          # ← 立即给庄家第二张牌
dealer_total_value = calculate_hand_value(dealer_hand)
game_over = dealer_total_value == 21  # ← 立即检查庄家 Blackjack
```

**修改后**：
```python
# 只从牌堆抽出3张牌
card1, card2, card3 = deck.pop(), deck.pop(), deck.pop()
player_hand = [card1, card3]
dealer_hand = [card2]              # 庄家只持有1张牌
# 不再检查庄家 Blackjack
# 新增：记录玩家是否为自然 Blackjack（头两张牌=21）
player_has_natural = (len(player_hand) == 2 and player_value == 21)
```

**关键变更**：
- 发牌从4张减少到3张（少抽一张 `card4`）
- 庄家手牌只有1张牌 `[card2]`
- 移除了 `dealer_total_value` 的计算和 `game_over` 判断
- 新增 [`player_has_natural`](blackjack_eu.py:56) 字段，用于后续庄家自然 Blackjack 的比较
- 初始 `message` 永远为 `None`（不会在发牌时结束游戏）

### 修改 2：[`blackjack_eu.py`](blackjack_eu.py) — `game_update()` 函数中的 `stand` 动作

**原代码（第105-135行）**：
```python
elif action == 'stand':
    player_value = game_state['player_value']
    dealer_value = calculate_hand_value(dealer_hand)
    while dealer_value < 17:           # 直接让庄家补牌到17点
        card = deck.pop()
        dealer_hand.append(card)
        dealer_value = calculate_hand_value(dealer_hand)
    # ...然后比较胜负...
```

**修改后**：
```python
elif action == 'stand':
    player_value = game_state['player_value']
    player_has_natural = game_state.get('player_has_natural', False)

    # 第1步：庄家从牌堆抽取第二张牌（欧洲规则核心）
    card = deck.pop()
    dealer_hand.append(card)
    dealer_value = calculate_hand_value(dealer_hand)

    # 第2步：检查庄家是否为自然 Blackjack（头两张牌=21）
    if dealer_value == 21 and len(dealer_hand) == 2:
        game_state['dealer_value'] = dealer_value
        if player_has_natural:
            game_state['message'] = "It's a tie of double blackjack!"
            game_state['message_class'] = 'tie-message'
        else:
            game_state['message'] = 'Dealer wins with a natural blackjack!'
            game_state['message_class'] = 'lose-message'
    else:
        # 第3步：无自然 Blackjack，庄家正常补牌到17点
        while dealer_value < 17:
            card = deck.pop()
            dealer_hand.append(card)
            dealer_value = calculate_hand_value(dealer_hand)
        # ...然后比较胜负（与标准版一致）...
```

**关键变更**：
- 庄家先抽取第二张牌（`deck.pop()`），而不是像标准版那样直接利用已有的暗牌
- 新增自然 Blackjack 检查：若庄家头两张牌点数为21，则：
  - 玩家也是自然 Blackjack → **平局**
  - 否则 → **庄家胜**（即使玩家通过多张牌凑成21点也输）
- 只有非自然 Blackjack 时，庄家才继续补牌到17点

### 修改 3：[`templates/blackjack_eu.html`](templates/blackjack_eu.html)

**原模板**（与 `blackjack.html` 相同）：
```html
{% if not game_state['message'] %}
    <!-- 始终显示 1 张明牌 + 1 张背牌（标准版模式） -->
    <svg ...>{{ get_card_name(game_state['dealer_hand'][0]) }}</svg>
    <svg ...>back</svg>
{% else %}
    <!-- 显示所有卡牌 -->
{% endif %}
```

**修改后**：
```html
{% if not game_state['message'] %}
    {% if game_state['dealer_hand'] | length == 1 %}
        {# 欧洲风格：庄家只有1张牌，只显示这张明牌 #}
        <svg ...>{{ get_card_name(game_state['dealer_hand'][0]) }}</svg>
    {% else %}
        {# 玩家Stand后庄家已抽第二张牌，显示1明+1背 #}
        <svg ...>{{ get_card_name(game_state['dealer_hand'][0]) }}</svg>
        <svg ...>back</svg>
    {% endif %}
{% else %}
    {# 游戏结束：显示庄家所有牌 #}
{% endif %}
```

**关键变更**：
- 根据 `dealer_hand` 的长度动态判断显示方式
- 游戏进行中（`message` 为空）且庄家只有1张牌→只显示1张明牌
- 玩家 Stand 后但还未刷新页面时，庄家可能有2张牌→显示1明+1背（过渡状态）
- 游戏结束后显示庄家所有牌

---

## 四、欧洲版 vs 标准版对比总结

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

## 五、验证方法

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
