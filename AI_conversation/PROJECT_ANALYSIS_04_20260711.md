# I_Wanna_enjoy_the_journey 对话总结 2026-07-11

> 本文件记录本次 AI 对话中的关键决策、问题排查、代码改动和待跟进事项。所有路径使用相对路径。

---

## 一、死亡效果实现

### 完成内容

实现了 Kid 死亡后的粒子迸溅效果：
- 原贴图消失
- 生成血液小方块
- 生成身体碎片（头、手、身体等）
- 粒子受重力影响，碰到实心块/尖刺后粘住
- 死亡 0.5 秒后显示 GameOver
- 按 **R** 复活

### 新增文件

- `classes/particle.py`
  - `Particle` 类：通用粒子，支持重力、碰撞粘滞、可选寿命
  - 与实心块用矩形碰撞
  - 与尖刺用 mask 像素级碰撞

### 修改文件

- `classes/player_kid.py`
  - `__init__` 中加载死亡占位贴图和 GameOver 贴图
  - 新增 `_get_death_direction()`：根据碰撞状态/速度判断血液迸溅方向
  - 新增 `_spawn_death_particles()`：生成血液和身体碎片
  - 修改 `die()`：触发死亡、生成粒子、播放音效
  - 新增 `respawn()`：按 R 复活，重置位置、速度、跳跃状态
  - `draw()`：死亡后隐藏玩家本体，绘制粒子和 GameOver
  - `update()`：死亡状态下继续更新粒子和 GameOver 计时器

### 关键设计决策

**为什么玩家 mask 用固定矩形而不是动画帧实时生成？**
- 动画帧手脚会摆动，实时生成 mask 会导致碰撞框忽大忽小
- 固定 mask 能保证站在地面上时碰撞稳定
- 后续可用 `resources/sprite/player/maskPlayer.png` 替换

**玩家 mask 尺寸优化：**
- 最初使用完整 32×32 矩形 mask
- 发现死亡判定范围过大，感觉像碰到矩形就死
- 改为 16×28 居中矩形 mask，留出贴图边缘作为安全边距
- 死亡判定精确很多

---

## 二、跳跃机制完善

### 问题

角色从平台边缘走下来（没有按过跳），空中按跳无法跳跃。

### 原因

原代码只用 `has_djump` 标志，无法区分：
- 从平台边缘走下来没跳过
- 二段跳已经用完

### 修复

新增 `first_jump_used` 标志：
- 地面跳：普通跳跃高度，开启二段跳资格
- 空中且 `has_djump=True`：常规二段跳
- 空中且 `first_jump_used=False`：从平台边缘走下来的情况，直接消耗二段跳机会

落地和复活时重置 `has_djump` 和 `first_jump_used`。

---

## 三、尖刺像素级碰撞

### 完成内容

尖刺碰撞从矩形碰撞改为 `pygame.mask` 像素级碰撞：
- `classes/block.py` 中每个 Sprite 都根据 `self.image` 生成 `self.mask`
- `classes/player_kid.py` 的 `_check_collision()` 对尖刺使用 `pygame.sprite.collide_mask`
- `classes/particle.py` 的粒子与尖刺也使用 mask 碰撞

### 关键发现

- 尖刺贴图 `resources/sprite/enemies/spikes/spike_up.png` 本身有透明通道
- mask 只覆盖尖刺的白色实体部分（约 544/1024 像素）
- 血液能正确粘在尖刺形状上，证明 mask 生效

### 调试方法

在 `tests/test_02.py` 里画刺的 mask 轮廓：

```python
for sprite in platforms:
    if sprite.type == 'spike' and hasattr(sprite, 'mask'):
        outline = sprite.mask.outline()
        for point in outline:
            x = int(sprite.rect.x + point[0])
            y = int(sprite.rect.y + point[1])
            pygame.draw.rect(screen, (0, 255, 0), (x, y, 2, 2))
```

---

## 四、物理稳定性修复

### 问题 1：idle/fall 状态疯狂切换

**原因**：`pygame.Rect` 坐标是整数。重力较小（0.3/帧）时，每帧 Y 轴移动不足 1 像素被截断，导致多帧检测不到地面。

**修复**：
- 用浮点数 `self.x` / `self.y` 记录精确位置
- 每帧同步 `self.rect.x = int(self.x)` / `self.rect.y = int(self.y)`
- 增加脚底 1 像素探测：不在地面时检查脚底往下 1 像素是否有实心块

### 问题 2：切窗口后角色消失/一飞冲天

**原因**：窗口失焦时 `dt` 变得巨大，速度暴增。

**修复**：限制最大 dt：

```python
dt = min(dt, 1 / 30)
```

### 问题 3：重生后位置不对

**原因**：只重置了 `rect.topleft`，没重置浮点位置 `self.x/self.y`。`update()` 基于浮点位置移动，下一帧会把 rect 拉回死亡位置。

**修复**：`respawn()` 同时重置 `self.x/self.y` 和 `self.rect.topleft`。

---

## 五、新增测试场景 `tests/test_02.py`

### 场景内容

- 窗口大小 800×608
- 底部铺满 `resources/sprite/blocks/floor_1.png`
- 随机放置两个 `resources/sprite/enemies/spikes/spike_up.png`
- 玩家初始位置 `(400, 200)`，落下站在地板上
- 按 **Q** 触发死亡，按 **R** 复活

### 用途

测试：
- 瓦片加载和绘制
- 玩家与地板碰撞
- 玩家与尖刺碰撞死亡
- 死亡粒子效果
- 复活机制

---

## 六、像素感与窗口缩放问题

### 结论

- Windows 虚拟机下 800×608 直接 1:1 显示，像素感清晰
- macOS Retina 会因系统缩放导致轻微模糊
- 这是显示层问题，不影响游戏逻辑
- 后续发布阶段再加窗口缩放选项

---

## 七、Tiled 地图相关知识

### 图层类型

| 类型 | 用途 |
|---|---|
| Tile Layer | 用 tileset 拼地图 |
| Object Layer | 放出生点、存档点、触发器、陷阱区域 |
| Image Layer | 大背景图/前景氛围图 |
| Group Layer | 把多个图层打包管理 |

### 推荐图层结构

```
Tile Layers:
  - bg
  - solid
  - spike
  - fg

Object Layers:
  - markers
  - traps
  - enemies
```

### 导出格式

- 推荐使用 **JSON** 而非 CSV
- JSON 能保留 Object Layer、自定义属性、图层名称等完整信息
- CSV 只能表达 Tile Layer 数据

### 陷阱实现方式

Tiled 只负责标位置，实际行为用代码写：
1. 在 Object Layer 或特殊 tile ID 标记陷阱触发点
2. 游戏加载时读取位置
3. 根据类型生成对应的陷阱对象

---

## 八、资源文件夹结构建议

推荐结构：

```
resources/
├── player/
│   ├── idle/
│   ├── walk/
│   ├── jump/
│   ├── fall/
│   ├── walljump/
│   ├── bullet/
│   └── mask.png
├── sprites/
│   ├── blocks/
│   ├── spikes/
│   ├── enemies/
│   ├── effects/
│   │   ├── blood/
│   │   └── body_parts/
│   └── ui/
│       └── game_over/
├── tilesets/
├── audio/
│   ├── player/
│   ├── bgm/
│   └── sfx/
└── backgrounds/
```

---

## 九、GM mask 概念

- `mask`：碰撞判定用的隐藏贴图，通常比可见动画更稳定
- `maskNothing`：空碰撞遮罩，表示不参与碰撞
- I Wanna 中玩家通常用固定 mask 做碰撞，动画只负责显示

---

## 十、Windows ARM 安装 Pygame 问题

- Python 3.14 ARM64 没有 pygame 预编译 wheel
- 推荐在 Windows 11 ARM 上使用 **Python 3.10/3.11/3.12 AMD64** 版本（通过转译运行）
- 避免从源码编译 pygame

---

## 十一、文件改动清单

| 文件 | 改动类型 | 说明 |
|---|---|---|
| `classes/particle.py` | 新增 | 粒子类 |
| `classes/player_kid.py` | 修改 | 死亡效果、mask 碰撞、浮点位置、二段跳修复 |
| `classes/block.py` | 修改 | Sprite 生成 mask |
| `tests/test_02.py` | 新增/修改 | 瓦片和尖刺测试场景 |

---

## 十二、当前已知问题 / 待做事项

1. `classes/game.py` 仍为空，需要主游戏循环
2. `classes/camera.py` 仍为空，需要摄像机跟随
3. `classes/ui.py` 仍为空，需要血条、死亡计数等 UI
4. 墙滑 / 墙跳尚未实现
5. 重力翻转尚未实现
6. 暂停 / swap / shift / freeze2 状态冻结系统尚未实现
7. 死亡重生与存档系统尚未实现
8. Tiled JSON 地图导入尚未实现
9. 方块贴图系统已初步测试，还需扩展更多类型
10. 陷阱系统尚未实现

---

## 十三、后续建议方向

按优先级：
1. 实现 Tiled JSON 地图导入
2. 扩展方块类型系统（背景、可交互、移动平台等）
3. 实现摄像机跟随
4. 实现墙滑 / 墙跳
5. 实现死亡重生和存档点
6. 补全 `classes/game.py` 主循环
7. 加入全局状态冻结（pause / swap / shift / freeze2）

---

## 十四、相关参考

- 上一次项目分析：`AI_conversation/PROJECT_ANALYSIS_03_20260704.md`
- 最初项目分析：`AI_conversation/PROJECT_ANALYSIS.md`
- iwPygame 参考项目：外部参考项目，位于本仓库同级目录 `../iwPygame/I-wanna-pygame`
- GM 引擎参考代码：`gm_to_pygame/`
