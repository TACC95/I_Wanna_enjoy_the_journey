"""
Tiled 地图加载测试
使用 resources/tilesets/rooms/room_test/test_map_01.tmj
"""
import sys
import pygame
from classes import PlayerKid
from classes.tilemap import TiledMapLoader

import os
print(os.getcwd())

# 窗口尺寸
SCREEN_W, SCREEN_H = 800, 608

pygame.init()
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
clock = pygame.time.Clock()
pygame.display.set_caption("Test 03: Tiled 地图加载")

FPS = 60

# 加载 Tiled 地图
MAP_PATH = './resources/tilesets/rooms/room_test/test_map_01.tmj'
loader = TiledMapLoader(MAP_PATH)

# 加载 Tile Layer 1 作为平台
try:
    platforms = loader.load_layer('Tile Layer 1')
except Exception as e:
    print(f"加载地图失败: {e}")
    raise

print(f"地图尺寸: {loader.get_map_size()}")
print(f"加载平台数量: {len(platforms)}")

# 创建玩家
player = PlayerKid(600, 600)

running = True
while running:
    dt = clock.tick(FPS) / 1000

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        player.handle_event(event)

    player.update(platforms, dt)

    # 渲染
    screen.fill((255, 255, 255))

    for sprite in platforms:
        sprite.draw(screen)

    player.draw(screen)

    pygame.display.flip()

pygame.quit()
sys.exit()
