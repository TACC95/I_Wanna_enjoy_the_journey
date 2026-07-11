import random
import pygame


class Particle:
    """
    通用粒子：用于血液、身体碎片等死亡效果。
    受重力影响，碰到实心块会粘住。
    """

    def __init__(self, x, y, image, vx, vy, gravity=0.4, life=None):
        self.image = image
        self.rect = image.get_rect(center=(x, y))
        # 粒子的像素级碰撞遮罩，用于和尖刺做精确碰撞
        self.mask = pygame.mask.from_surface(image)
        self.vx = vx
        self.vy = vy
        self.gravity = gravity
        self.stuck = False
        # 寿命（秒），None 表示永久（粘住后一直显示）
        self.life = life
        self.age = 0

    def update(self, dt, solids):
        """
        更新粒子位置。

        参数:
            dt: 距离上一帧的时间（秒）
            solids: 实心块精灵组，用于碰撞检测
        """
        if self.stuck:
            if self.life is not None:
                self.age += dt
            return

        self.age += dt
        if self.life is not None and self.age >= self.life:
            self.stuck = True
            return

        # 重力
        self.vy += self.gravity * dt * 60

        # 计算新位置
        new_rect = self.rect.move(self.vx * dt * 60, self.vy * dt * 60)

        # 碰撞检测：碰到实心块或尖刺就粘住
        for sprite in solids:
            if not new_rect.colliderect(sprite.rect):
                continue

            if sprite.type == 'solid':
                # 实心块是矩形，用矩形碰撞即可
                # 根据速度方向调整贴边位置，让粒子看起来是"溅"在表面上
                if self.vy > 0 and self.rect.bottom <= sprite.rect.top:
                    new_rect.bottom = sprite.rect.top
                elif self.vy < 0 and self.rect.top >= sprite.rect.bottom:
                    new_rect.top = sprite.rect.bottom
                elif self.vx > 0 and self.rect.right <= sprite.rect.left:
                    new_rect.right = sprite.rect.left
                elif self.vx < 0 and self.rect.left >= sprite.rect.right:
                    new_rect.left = sprite.rect.right

                self.rect = new_rect
                self.stuck = True
                return

            elif sprite.type == 'spike':
                # 尖刺是非矩形贴图，必须用 mask 做像素级碰撞
                # 计算尖刺 mask 相对于粒子 mask 的偏移量
                offset = (sprite.rect.x - new_rect.x, sprite.rect.y - new_rect.y)
                # 如果双方不透明像素有重叠，才判定为真正碰到刺
                if self.mask.overlap(sprite.mask, offset):
                    self.rect = new_rect
                    self.stuck = True
                    return

        self.rect = new_rect

    def is_alive(self):
        """粒子是否还应该显示"""
        if self.life is None:
            return True
        return self.age < self.life

    def draw(self, screen, camera_offset=(0, 0)):
        screen.blit(self.image, (self.rect.x - camera_offset[0],
                                 self.rect.y - camera_offset[1]))
