import pygame
from utils.utils import load_images


class Bullet(pygame.sprite.Sprite):
    """玩家射出的子弹"""

    def __init__(self, x, y, direction, dt=1/60):
        super().__init__()
        self.images = load_images('the_kid/bullet')
        self.direction = direction  # 1 = 右, -1 = 左
        self.image = self.images[0]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

        # 动画
        self.frame = 0
        self.frame_timer = 0
        self.frame_interval = 0.05

        # 运动（参考 iwPygame：14 像素/帧 @ 60fps）
        self.speed = 14 * 60  # 像素/秒

        # 寿命（参考 iwPygame：42 帧 @ 60fps）
        self.age = 0
        self.life = 42 / 60  # 秒

    def update(self, dt):
        self.age += dt
        self.rect.x += self.direction * self.speed * dt
        self._update_animation(dt)

    def _update_animation(self, dt):
        self.frame_timer += dt
        if self.frame_timer >= self.frame_interval:
            self.frame_timer = 0
            self.frame = (self.frame + 1) % len(self.images)
            self.image = self.images[self.frame]
            if self.direction < 0:
                self.image = pygame.transform.flip(self.image, True, False)

    def is_alive(self):
        return self.age < self.life

    def draw(self, screen, camera_offset=(0, 0)):
        screen.blit(self.image, (self.rect.x - camera_offset[0],
                                 self.rect.y - camera_offset[1]))
