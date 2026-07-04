# I_Wanna_enjoy_the_journey 对话总结 2026-07-04

> 本文件记录本次 AI 对话中的关键决策、问题排查、代码改动和待跟进事项。所有路径使用相对路径。

---

## 一、像素感与窗口缩放问题

### 问题现象
在 macOS 上运行 `tests/test_01.py` 时，人物贴图没有 GM8.1 I Wanna 那种硬像素感，看起来像是被抗锯齿了一样。

### 结论
**问题不在 Pygame 代码，而在 macOS Retina 屏幕的系统缩放**。

- Windows 11 虚拟机（非高分屏 / 整数缩放）下，`pygame.display.set_mode((800, 608))` 直接 1:1 显示，像素感清晰，和 GM8.1 一致。
- macOS Retina 会把 800×608 的逻辑窗口缩放到 1600×1216 物理像素显示，中间经过双线性过滤，导致像素边缘发软。

### 验证方法
1. 用 `pygame.image.save(screen, "cap.png")` 保存原始帧，放大检查是否本身清晰。
2. 把窗口改得很小（如 400×300），观察是否异常清晰。

### 尝试过的方案
- **方案：小分辨率游戏表面 + 整数倍放大**
  - 逻辑分辨率 `400×304`，窗口 `800×608`
  - 结果：人物被放大两倍，视野范围减半（ undesirable ）
  - 原因：逻辑分辨率砍半导致整个世界被拉近
  - 如果要保持原来视野，应该逻辑分辨率 `800×608`、窗口 `1600×1216`，但屏幕装不下
- **结论**：在当前屏幕尺寸下无法在 macOS 上同时做到"窗口够大"和"绝对清晰像素"。

### 最终决策
- 开发和测试以 **Windows 虚拟机** 为准，800×608 窗口，像素清晰。
- macOS 上的轻微模糊是系统缩放导致，不影响游戏逻辑。
- 后续发布阶段再加入"窗口缩放选项"（1x / 2x / 全屏），让玩家自己根据屏幕选择。

---

## 二、窗口尺寸确定为 800×608

### 背景
I Wanna yuuutu 引擎的窗口标准尺寸通常为 **800×608**：
- 水平 25 格 × 32 = 800
- 垂直 19 格 × 32 = 608

用户解包的 GM 工程可能是 800×640（20 格高），但 yuuutu 主流是 800×608。

### 修改文件
- `tests/test_01.py`
  - 窗口大小：`800×600` → `800×608`
  - 玩家初始 Y 坐标：`300` → `304`（垂直居中）
  - 空气墙相关常量基于 `SCREEN_W` / `SCREEN_H`，随窗口尺寸自动调整

---

## 三、Windows 导入路径问题

### 问题
在 Windows 上运行 `test_01.py` 时报错：
```
ModuleNotFoundError: No module named 'classes'
```

### 原因
运行方式导致项目根目录不在 `sys.path` 中。例如：
- `cd tests && python test_01.py`
- `python tests/test_01.py`

这两种方式只把 `tests/` 加入 `sys.path`，所以找不到 `classes`。

### 正确运行方式
在项目根目录执行：
```bash
python -m tests.test_01
```

### 可选修复
在 `tests/test_01.py` 开头加入：
```python
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
```

---

## 四、Windows 11 ARM 虚拟机安装 Pygame 问题

### 问题 1：SSL 证书错误
```
URLError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed
```

### 问题 2：Python 3.14 ARM64 没有预编译 wheel
PyPI 上基本没有 Windows ARM64 (`win_arm64`) 的 pygame wheel，尤其是 Python 3.14 这种新版本。

### 解决方案
**推荐：安装 Python 3.10/3.11/3.12 的 AMD64 (x64) 版本**，Windows 11 ARM 可以通过转译运行 x64 程序，且所有第三方库都有 wheel。

不推荐从源码编译 pygame，因为需要 C 编译器、SDL2 系列库和大量 Windows 链接配置。

---

## 五、音效系统实现

### 新增音效文件
位于 `resources/the_kid/audio/`：
- `Jump.wav` — 一段跳
- `Double Jump.wav` — 二段跳
- `Shoot.wav` — 射击
- `Death.wav` — 死亡（暂未使用）

### 修改位置

#### `classes/player_kid.py`

1. **`__init__` 中加载音效**
   ```python
   self.sfx = {
       'jump':  pygame.mixer.Sound('resources/the_kid/audio/Jump.wav'),
       'djump': pygame.mixer.Sound('resources/the_kid/audio/Double Jump.wav'),
       'shoot': pygame.mixer.Sound('resources/the_kid/audio/Shoot.wav'),
   }
   ```

2. **`jump()` 中按类型播放音效**
   - 普通跳：`self.sfx['jump'].play()`
   - 二段跳：`self.sfx['djump'].play()`

3. **`shoot()` 中播放射击音效**
   - `self.sfx['shoot'].play()`
   - 射击音效属于玩家动作，放在 `PlayerKid` 中语义更合适。

#### `classes/bullet.py`
**无需修改**。子弹只负责飞行、动画和碰撞，不处理声音。

---

## 六、类型提示建议

针对本项目规模，建议：
- 公共接口、工具函数、类方法参数/返回值优先加类型
- 内部临时变量、循环变量可以不加
- 容器类型尽量具体：`list[Bullet]`、`dict[str, pygame.Surface]`
- `| None` 要标清楚
- `__init__` 是集中声明成员属性的好地方
- 现阶段不必追求 100% 类型覆盖，重点机制跑通后再补全

---

## 七、子弹类设计回顾

**子弹单独成 `Bullet` 类的原因**：
- 子弹是独立实体，有自己的位置、速度、动画、寿命
- 便于独立更新和绘制
- 方便后续扩展（反弹、不同弹种、命中敌人等）
- 符合 GM 原作中 `objBullet` 作为独立对象的设计

---

## 八、文件改动清单

| 文件 | 改动类型 | 说明 |
|---|---|---|
| `classes/bullet.py` | 新增 | 子弹类 |
| `classes/player_kid.py` | 修改 | 集成射击、跳跃音效 |
| `tests/test_01.py` | 修改 | 窗口改为 800×608 |

---

## 九、当前已知问题 / 待做事项

1. `classes/game.py` 仍为空，需要主游戏循环
2. `classes/camera.py` 仍为空，需要摄像机跟随
3. `classes/ui.py` 仍为空，需要血条、死亡计数等 UI
4. 墙滑 / 墙跳尚未实现
5. 重力翻转尚未实现
6. 暂停 / swap / shift / freeze2 状态冻结系统尚未实现
7. 死亡重生与存档系统尚未实现
8. 完整关卡读取与切换系统尚未实现
9. 射击目前只与实心块碰撞销毁，还没有命中敌人/机关的交互
10. 摄像机跟随实现后，需要把 `player.draw()` 和 `bullet.draw()` 的 `camera_offset` 用起来

---

## 十、后续建议方向

按优先级：
1. 补全 `classes/game.py` 主循环
2. 实现 `classes/camera.py` 摄像机跟随
3. 用 JSON 瓦片地图替换硬编码的 `room_data`
4. 实现墙滑 / 墙跳
5. 实现死亡重生和存档点
6. 加入全局状态冻结（pause / swap / shift / freeze2）
7. 重力翻转、水、冰等 GM 机关

---

## 十一、相关参考

- 上一次项目分析：`AI_conversation/PROJECT_ANALYSIS_02_20260703.md`
- 最初项目分析：`AI_conversation/PROJECT_ANALYSIS.md`
- iwPygame 参考项目：外部参考项目，位于本仓库同级目录 `../iwPygame/I-wanna-pygame`
- GM 引擎参考代码：`gm_to_pygame/`
