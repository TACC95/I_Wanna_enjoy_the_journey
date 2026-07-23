# I_Wanna_enjoy_the_journey 对话总结 2026-07-23

> 本文件记录 2026-07-11 之后至 2026-07-23 期间的 AI 对话关键决策、问题排查和代码改动。所有路径使用相对路径。
> 上一次总结：`AI_conversation/PROJECT_ANALYSIS_04_20260711.md`

---

## 一、Tiled 方块映射表

### 文件位置

- `data/block_registry.json`

### 设计思路

模仿方块数据库，集中保存项目中所有可用方块。每个方块记录：

| 字段 | 说明 |
|---|---|
| `name` | 方块名称，如 `floor_1`、`spike_up` |
| `type` | 方块类型，如 `solid`、`spike`、`bg`、`save`、`trigger` |
| `file` | 贴图相对路径，`null` 表示无贴图 |

### 当前已注册方块

- `1` `floor_1` → `solid`
- `2` `floor_2` → `solid`
- `3` ~ `6` 四个方向尖刺 → `spike`
- `7` ~ `8` 樱桃 → `spike`
- `9` ~ `10` 存档点 → `save`

### 为什么用 JSON 而不是 CSV

- CSV 适合二维表，但难以表达复杂字段（例如触发器参数、多值属性）。
- JSON 可以方便地扩展每个方块的属性，例如动画帧、碰撞偏移、自定义脚本参数等。
- 与用户数据分析习惯不完全一致，但为了后期可扩展性选择 JSON。

---

## 二、方块注册脚本

### 文件位置

- `utils/register_block.py`（后从 `tools/` 移动到 `utils/`）

### 功能

交互式快速注册新方块到 `data/block_registry.json`：

1. 输入方块名称
2. 输入方块类型
3. 输入贴图相对路径（可为空）
4. 自动分配最小未使用 ID
5. 写入注册表

### 使用提示

注册完成后，还需要在 Tiled 的 tileset 中给对应 tile 添加自定义属性 `block_id = <新ID>`，否则地图加载时无法把 tile 和注册表关联起来。

---

## 三、Tiled JSON 地图加载

### 新增文件

- `classes/tilemap.py`
  - `TiledMapLoader` 类：加载 Tiled 导出的 `.tmj` 地图

### 核心流程

```
TiledMapLoader(map_path)
  ├── 读取 .tmj 地图文件
  ├── 解析地图尺寸、tile 尺寸
  ├── 加载引用的外部 tileset（.tsj）
  ├── 建立 tileset 内 local_id → block_id 映射
  │   └── 依据 tile 的自定义属性 block_id
  ├── 加载 data/block_registry.json
  └── 按图层生成 Sprite 组
```

### 关键方法

- `load_layer(layer_name)`：加载指定 `tilelayer`，返回 `pygame.sprite.Group`
- `load_object_layer(layer_name)`：加载 `objectgroup`，返回对象列表（用于出生点、触发器、陷阱区域）
- `get_map_size()`：返回地图总像素尺寸

### gid 处理

- Tiled 把翻转、旋转信息编码到 gid 高位。
- 加载时先用 `raw_gid & 0x1FFFFFFF` 去掉标志位。
- 再减去 tileset 的 `firstgid`，得到 tileset 内的 `local_id`。

### 图片加载

- tileset 中 `image` 路径是相对于 tileset 文件位置的。
- `TiledMapLoader` 会根据地图文件位置解析 tileset 路径，再解析图片路径。
- 使用图片缓存，避免同一贴图重复加载。

---

## 四、Tiled 地图测试

### 文件位置

- `tests/test_03.py`

### 测试内容

- 加载 `resources/tilesets/rooms/room_test/test_map_01.tmj`
- 读取 `Tile Layer 1` 作为平台
- 玩家 `PlayerKid` 在地图中移动、跳跃、死亡
- 窗口尺寸 800×608

### 路径约定

```python
MAP_PATH = './resources/tilesets/rooms/room_test/test_map_01.tmj'
```

所有资源路径均以项目根目录为基准，使用 `./` 开头。

---

## 五、路径问题与解决方案

### 问题

直接运行 `test_03.py` 时，相对路径解析错误，例如找不到 `data/block_registry.json`。

### 原因

Python 脚本的工作目录不一定是项目根目录，取决于从哪个目录启动脚本。

### 尝试过的方案

- 在代码里用 `PROJECT_ROOT = Path(__file__).parent.parent` 强制定位项目根目录。
- 用 `sys.path.insert` 修正模块导入路径。

### 最终方案

通过 **PyCharm 运行配置** 设置工作目录为项目根目录：

- 打开 `Run / Edit Configurations...`
- 找到对应运行配置
- 把 `Working directory` 设为项目根目录

这样代码里统一使用 `./` 相对路径即可，不需要在运行时写 `PROJECT_ROOT` 或 `sys.path.insert`。

### 清理结果

已删除以下运行时路径修正代码：

- `classes/tilemap.py` 中无 `PROJECT_ROOT`、`_resolve_path`、`_find_project_root`
- `tests/test_03.py` 中无 `sys.path.insert`、无 `../resources` 或 `../data` 路径

> 注：`utils/register_block.py` 作为独立命令行工具，仍保留 `PROJECT_ROOT` 用于定位 `data/block_registry.json`，这是合理的。

---

## 六、Tiled 相关概念确认

### 图层类型

| 类型 | 用途 |
|---|---|
| Tile Layer | 拼地图方块 |
| Object Layer | 出生点、存档点、触发器、陷阱区域 |
| Image Layer | 大背景图 |
| Group Layer | 图层分组管理 |

### tileset 自定义属性

- 在 Tiled 中给 tile 添加自定义属性 `block_id`，值对应 `data/block_registry.json` 中的 ID。
- 这是地图与游戏内方块系统关联的桥梁。

### Object Layer 用途

- 触发器、陷阱、敌人出生点、玩家出生点、存档点等不适合用 tile 表达的内容，用 Object Layer 标位置。
- 游戏加载后根据对象名称和属性生成对应逻辑对象。

---

## 七、当前已知问题 / 待做事项

1. `classes/game.py` 仍为空，需要主游戏循环。
2. `classes/camera.py` 仍为空，需要摄像机跟随。
3. `classes/ui.py` 仍为空，需要血条、死亡计数等 UI。
4. 墙滑 / 墙跳尚未实现。
5. 重力翻转尚未实现。
6. 暂停 / swap / shift / freeze2 状态冻结系统尚未实现。
7. 死亡重生与存档系统尚未实现（存档点贴图已注册，逻辑未做）。
8. 陷阱系统尚未实现。
9. 需要继续扩展方块类型和注册表。
10. 摄像机与大地图滚动需要结合 Tiled 地图尺寸实现。

---

## 八、文件改动清单

| 文件 | 改动类型 | 说明 |
|---|---|---|
| `data/block_registry.json` | 新增 | 方块映射表 |
| `utils/register_block.py` | 新增/移动 | 方块注册工具脚本 |
| `classes/tilemap.py` | 新增 | Tiled JSON 地图加载器 |
| `tests/test_03.py` | 新增 | Tiled 地图加载测试 |

---

## 九、后续建议方向

按优先级：

1. 验证 `tests/test_03.py` 在 PyCharm 中能否正常加载并显示地图。
2. 实现摄像机跟随，支持比窗口大的 Tiled 地图。
3. 扩展方块类型：背景块、可交互块、移动平台等。
4. 实现存档点逻辑（碰到存档点更新出生位置）。
5. 实现 Object Layer 解析，用于出生点和触发器。
6. 实现陷阱系统。
7. 实现墙滑 / 墙跳。
8. 补全 `classes/game.py` 主循环。
9. 加入全局状态冻结（pause / swap / shift / freeze2）。
