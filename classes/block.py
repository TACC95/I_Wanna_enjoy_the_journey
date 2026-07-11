import pygame

class Sprite(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, sprite_type, image=None):
        super().__init__()
        self.type = sprite_type  # 'solid', 'spike', 'save', 'goal'
        self.rect = pygame.Rect(x, y, width, height)
        if image:
            self.image = image
        else:
            # 根据类型生成不同颜色的占位方块
            self.image = pygame.Surface((width, height))
            colors = {
                'solid': (100, 100, 100),
                'spike': (255, 0, 0),
                'save':  (0, 255, 0),
                'goal':  (0, 0, 255)
            }
            self.image.fill(colors.get(sprite_type, (200, 200, 200)))

        # 生成像素级碰撞遮罩。
        # 对于尖刺这类非矩形贴图，mask 能让碰撞只检测不透明像素，
        # 避免玩家碰到刺的透明角落就被判死。
        # solid/save/goal 用矩形 mask 即可，因为它们的碰撞框就是矩形。
        self.mask = pygame.mask.from_surface(self.image)

    def draw(self, screen, camera_offset=(0, 0)):
        screen.blit(self.image, (self.rect.x - camera_offset[0],
                                 self.rect.y - camera_offset[1]))