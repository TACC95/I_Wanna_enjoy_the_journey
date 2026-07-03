# I_Wanna_enjoy_the_journey 项目分析

> 本文件由 AI 对话分析整理生成，用于后续快速回顾项目状态。

---

## 一、项目定位

这是一个 **Pygame 复刻/移植项目**，目标是把经典 GameMaker 同人游戏引擎 **"I Wanna Be The Engine"**（yuutu edition，《I Wanna》系列常用引擎）移植到 Python/Pygame 上运行。

证据：
- 目录 `gm_to_pygame/` 下包含原 GM 引擎的 `.gmk` 源文件和导出的对象脚本（`PlayerTutaJump.txt`、`PausedGravity.txt`、`PlayerMuki.txt` 等）。
- 项目名 `I_Wanna_enjoy_the_journey` 致敬 I Wanna 系列。

**结论：这是一个学习/还原项目，想用 Pygame 重新实现 I Wanna 的物理、机关和关卡系统。**

---

## 二、目录结构

```
I_Wanna_enjoy_the_journey/
├── .venv/                  # Python 虚拟环境
├── .idea/                  # PyCharm 配置
├── classes/                # 游戏核心类
│   ├── __init__.py         # 空
│   ├── game.py             # 空
│   ├── camera.py           # 空
│   ├── ui.py               # 空
│   ├── player_kid.py       # 玩家实现
│   ├── block.py            # 地图精灵实现
│   ├── room.py             # 房间/关卡实现
│   └── play_music.py       # 音乐管理器
├── gm_to_pygame/           # GM 引擎参考代码与文档
│   ├── CollisionBlock.txt
│   ├── GravityChange.txt
│   ├── Muteki.txt
│   ├── PausedGravity.txt
│   ├── PlayerMuki.txt
│   ├── PlayerSprite.txt
│   ├── PlayerTutaJump.txt
│   └── IWBTE yuuutu edition ver2.17/
│       ├── i wanna be the engine yuuutu edition.gmk
│       └── readme/
├── resources/              # 游戏素材
│   └── the_kid/
│       ├── idle/
│       ├── walk/
│       ├── jump/
│       ├── fall/
│       ├── walljump/
│       └── bullet/
├── tests/                  # 测试/演示
│   └── test_01.py          # 玩家贴图/动画测试
└── utils/
    └── utils.py            # 图片加载工具
```

---

## 三、已实现的模块

| 文件 | 状态 | 作用 |
|---|---|---|
| `classes/player_kid.py` | ✅ 已实现 | 玩家 `The Kid`：跑、跳、二段跳、短跳、重力、动画状态机、贴图翻转、死亡判定 |
| `classes/block.py` | ✅ 已实现 | 通用精灵 `Sprite`：solid（墙）、spike（刺）、save（存档）、goal（终点） |
| `classes/room.py` | ✅ 已实现 | 房间/关卡：加载精灵组、玩家出生点、物理更新、尖刺/存档点检测、音乐切换 |
| `classes/play_music.py` | ✅ 已实现 | 音乐管理器：按房间 ID 播放 BGM 列表、自动切歌、音量控制 |
| `utils/utils.py` | ✅ 已实现 | 图片加载工具：`load_images` / `load_image` |
| `tests/test_01.py` | ✅ 可运行 | 玩家贴图/动画测试：窗口 800×600，四面空气墙，可跑跳看动画 |
| `classes/game.py` | ❌ 空文件 | 本应是主游戏循环和场景管理 |
| `classes/camera.py` | ❌ 空文件 | 本应是摄像机跟随 |
| `classes/ui.py` | ❌ 空文件 | 本应是血条、死亡计数、菜单等 UI |
| `classes/__init__.py` | ❌ 空文件 | 包入口 |

---

## 四、玩家物理还原情况

`player_kid.py` 已实现的 I Wanna 核心手感：

- 左右移动：固定速度 `max_hspeed = 3`
- 跳跃：`jump_speed = 8.5`
- 二段跳：`djump_speed = 7`
- 短跳（松键减速）：`vjump()` 把上升速度乘 0.45
- 重力 `0.3`，最大下落速度 `9`
- 动画状态机：`idle / walk / jump / djump / fall / walljump`
- 帧率无关运动：使用 `dt * 60` 归一化
- 四面碰撞状态记录：`collisions['up/down/left/right']`

---

## 五、素材文件

`resources/the_kid/` 下已切好的素材：

- `idle/`：4 帧待机
- `walk/`：6 帧跑步
- `jump/`：4 帧跳跃
- `djump/`：代码中复用 `jump[1:]`
- `fall/`：2 帧下落
- `walljump/`：2 帧墙滑
- `bullet/`：2 帧子弹贴图（射击功能未实现）

素材尺寸与 `PlayerKid` 中 32×32 的碰撞框一致。

---

## 六、参考的 GM 引擎文件

`gm_to_pygame/` 目录保存了从原 GM 引擎中提取的参考代码：

| 文件 | 对应机制 |
|---|---|
| `CollisionBlock.txt` | 碰撞块处理 |
| `GravityChange.txt` | 重力翻转 |
| `PausedGravity.txt` | 暂停/swap/shift/freeze2 等状态对运动和重力的冻结恢复 |
| `PlayerMuki.txt` | 玩家朝向（sprite 翻转） |
| `PlayerSprite.txt` | 玩家贴图/动画切换 |
| `PlayerTutaJump.txt` | 墙滑与墙跳（Tuta Jump） |
| `Muteki.txt` | 无敌/调试模式 |

这些文件目前只作为参考，尚未完全移植到 Pygame 代码中。

---

## 七、尚未实现的核心机制

- 墙滑 / 墙跳（`PlayerTutaJump.txt`）
- 重力翻转（`GravityChange.txt`）
- 暂停 / swap / shift / freeze 状态（`PausedGravity.txt`）
- 无敌 / 调试模式（`Muteki.txt`）
- 射击子弹
- 死亡重生与存档系统
- 摄像机跟随
- 完整关卡读取与切换
- 主游戏循环（`game.py`）

---

## 八、当前已知问题

1. **空文件太多**：`game.py`、`camera.py`、`ui.py` 都是 0 字节，项目还不能作为完整游戏启动，只能跑 `tests/test_01.py`。
2. **音乐事件可能被吞**：`play_music.py` 的 `update()` 使用 `pygame.event.get(eventtype=pygame.USEREVENT+1)` 获取音乐结束事件，但如果主循环里还有另一个 `pygame.event.get()`，该事件可能被漏掉。
3. **`dt` 未传入 Room**：`room.update()` 没有接收 `dt`，`player.update(self.solids)` 使用默认 `dt=1/60`，帧率无关做得不彻底。
4. **测试文件导入路径问题**：`tests/test_01.py` 中 `from classes.player_kid import PlayerKid` 直接在 `tests/` 目录运行可能会因路径问题报错，建议在项目根目录执行 `python -m tests.test_01` 或添加 `sys.path` 处理。
5. **二段跳触发逻辑较微妙**：`jump_triggered` 在 `KEYDOWN` 时先重置为 `False` 再调用 `jump()` 设为 `True`，连续按键时二段跳判断可能需要进一步验证。

---

## 九、后续可做的事情

- 补全 `game.py` 主循环
- 实现摄像机跟随（`camera.py`）
- 做关卡/房间切换系统
- 实现墙滑墙跳
- 加死亡重生和存档点
- 跑通 `test_01.py` 并修复路径问题
- 把 `dt` 正确传递到 `Room.update()` 和 `PlayerKid.update()`
- 实现射击、重力翻转、暂停等 GM 机关

---

## 十、总体评价

这是一个 **起步良好、方向明确的 I Wanna 复刻项目**。玩家核心手感已经搭好，素材也准备齐全，但还处在"能跑一个角色测试 Demo"的阶段，距离完整游戏还差主循环、摄像机、关卡加载、死亡重生、墙跳等机制。
