"""
简单瓦片测试
- 底部铺满 floor_1.png
- 随机放置两个朝上的刺
- 测试角色与瓦片碰撞、死亡效果
"""
import sys
import random
import pygame
from pathlib import Path

# 把项目根目录加入 sys.path，方便直接运行本文件
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from classes import PlayerKid, Sprite

# 窗口尺寸常量（I Wanna yuuutu 引擎标准：800x608）
SCREEN_W, SCREEN_H = 800, 608

# Pygame 初始化
pygame.init()
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
clock = pygame.time.Clock()
pygame.display.set_caption("Test 02: 瓦片加载")

# 帧率控制（限制为 60 FPS）
FPS = 60

# 用于计算实际帧率
fps_counter = 0
fps_timer = 0
current_fps = 0

# 加载贴图
floor_image = pygame.image.load('resources/sprite/blocks/floor_1.png').convert_alpha()
spike_image = pygame.image.load('resources/sprite/enemies/spikes/spike_up.png').convert_alpha()

# 瓦片大小
TILE_SIZE = 32

# 创建平台精灵组
platforms = pygame.sprite.Group()

# ===== 底部铺满地板 =====
floor_y = SCREEN_H - TILE_SIZE
for x in range(0, SCREEN_W, TILE_SIZE):
    floor_tile = Sprite(x, floor_y, TILE_SIZE, TILE_SIZE, 'solid', floor_image)
    platforms.add(floor_tile)

# ===== 随机放两个朝上的刺 =====
# 刺放在地板上，x 随机取整数格位置
spike_positions = random.sample(range(5, SCREEN_W // TILE_SIZE - 5), 2)
for tile_x in spike_positions:
    spike = Sprite(tile_x * TILE_SIZE, floor_y - TILE_SIZE, TILE_SIZE, TILE_SIZE, 'spike', spike_image)
    platforms.add(spike)

# 创建玩家实例，初始位置居中偏上
player = PlayerKid(400, 200)

# 游戏主循环
running = True
while running:
    # 控制帧率，返回距上一帧的时间（秒）
    dt = clock.tick(FPS) / 1000

    # 计算实际帧率
    fps_counter += 1
    fps_timer += dt
    if fps_timer >= 1.0:
        current_fps = fps_counter
        fps_counter = 0
        fps_timer = 0
        pygame.display.set_caption(f"Test 02 - FPS: {current_fps}")

    # 事件处理
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        # 传递给玩家处理键盘输入
        player.handle_event(event)

    # 更新玩家逻辑（传入平台组，用于碰撞检测）
    player.update(platforms, dt)

    # ===== 渲染 =====
    # 清屏（白色背景）
    screen.fill((255, 255, 255))

    # 绘制所有瓦片
    for sprite in platforms:
        sprite.draw(screen)

    # 绘制玩家
    player.draw(screen)

    # ===== 调试：画出刺的 mask 轮廓 =====
    for sprite in platforms:
        if sprite.type == 'spike' and hasattr(sprite, 'mask'):
            outline = sprite.mask.outline()
            for point in outline:
                screen.set_at((sprite.rect.x + point[0], sprite.rect.y +
                               point[1]), (0, 255, 0))

    # 更新屏幕显示
    pygame.display.flip()

# 退出 Pygame
pygame.quit()
sys.exit()
