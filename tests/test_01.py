"""
第一测试—————玩家贴图测试
"""

import sys
import pygame
from classes.player_kid import PlayerKid

# Pygame 初始化
pygame.init()
screen = pygame.display.set_mode((800, 600))
clock = pygame.time.Clock()
pygame.display.set_caption("Test 01: 玩家贴图加载")

# 帧率控制（限制为 60 FPS）
FPS = 60
clock = pygame.time.Clock()

# 用于计算实际帧率
fps_counter = 0
fps_timer = 0
current_fps = 0

# 创建玩家实例，初始位置居中
player: PlayerKid = PlayerKid(400, 300)

# 窗口尺寸常量
SCREEN_W, SCREEN_H = 800, 600

# 空气墙厚度
WALL_THICKNESS = 5

# 地面高度（窗口底部向上偏移）
FLOOR_Y = SCREEN_H - WALL_THICKNESS

# 左右墙壁边界
LEFT_WALL_X = WALL_THICKNESS
RIGHT_WALL_X = SCREEN_W - WALL_THICKNESS

# 顶部落点
CEILING_Y = WALL_THICKNESS

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
        pygame.display.set_caption(f"Test 01 - FPS: {current_fps}")

    # 事件处理
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        # 传递给玩家处理键盘输入
        player.handle_event(event)

    # 更新玩家逻辑（platforms 为空，无实心碰撞块）
    player.update([], dt)

    # ===== 空气墙检测 =====

    # 地面碰撞
    if player.rect.bottom >= FLOOR_Y:
        player.rect.bottom = FLOOR_Y
        player.vspeed = 0
        player.on_ground = True
        player.has_djump = False
        player.air_time = 0

    # 天花板碰撞
    if player.rect.top <= CEILING_Y:
        player.rect.top = CEILING_Y
        player.vspeed = 0

    # 左墙壁碰撞
    if player.rect.left <= LEFT_WALL_X:
        player.rect.left = LEFT_WALL_X
        player.hspeed = 0

    # 右墙壁碰撞
    if player.rect.right >= RIGHT_WALL_X:
        player.rect.right = RIGHT_WALL_X
        player.hspeed = 0

    # ===== 渲染 =====

    # 清屏（白色背景）
    screen.fill((255, 255, 255))

    # 绘制玩家（无相机偏移）
    player.draw(screen)

    # 更新屏幕显示
    pygame.display.flip()

# 退出 Pygame
pygame.quit()
sys.exit()
