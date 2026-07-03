import pygame
from classes.block import Sprite
from classes.player_kid import PlayerKid

class Room:
    def __init__(self, room_data, music_manager):
        """
        room_data: 包含精灵列表、玩家出生点等信息的字典
        music_manager: PlayMusic 实例
        """
        self.sprites = pygame.sprite.Group()
        self.spikes = pygame.sprite.Group()    # 可以单独管理刺
        self.solids = pygame.sprite.Group()
        self.saves = pygame.sprite.Group()
        self.player = None

        self.music_manager = music_manager
        self.room_id = room_data.get('id', 'room1')

        self._load_room(room_data)

    def _load_room(self, data):
        """根据数据生成精灵和玩家"""
        # 生成精灵
        for sprite_info in data.get('sprites', []):
            s = Sprite(sprite_info['x'], sprite_info['y'],
                       sprite_info['width'], sprite_info['height'],
                       sprite_info['type'], sprite_info.get('image'))
            self.sprites.add(s)
            if s.type == 'solid':
                self.solids.add(s)
            elif s.type == 'spike':
                self.spikes.add(s)
            elif s.type == 'save':
                self.saves.add(s)

        # 创建玩家
        player_start = data.get('player_start', (100, 100))
        self.player = PlayerKid(*player_start)

        # 启动本房间音乐
        self.music_manager.play_for_room(self.room_id)

    def update(self, dt):
        """
        更新玩家和交互检测
        注意传入了dt，这意味着物理与帧率不挂钩
        """
        if not self.player.alive:
            # 处理死亡（例如：等待按键重新开始）
            return

        # 玩家物理与碰撞（只与实心块进行物理碰撞，刺在内部单独处理）
        self.player.update(self.solids, dt)

        # 检测与尖刺的碰撞
        if pygame.sprite.spritecollide(self.player, self.spikes, False):
            self.player.die()

        # 检测存档点
        for save in pygame.sprite.spritecollide(self.player, self.saves, False):
            # 触发存档逻辑：记录存档位置，可播放音效
            print(f"存档点触发: {save.rect.topleft}")

        # 检测终点
        # ...

    def draw(self, screen, camera_offset):
        """绘制本房间所有物体"""
        for sprite in self.sprites:
            sprite.draw(screen, camera_offset)
        if self.player:
            self.player.draw(screen, camera_offset)