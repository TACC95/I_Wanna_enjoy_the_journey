import pygame
from pygame.locals import *
from utils.utils import load_images
from classes.bullet import Bullet


class PlayerKid(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((32, 32))
        self.image.fill((255, 200, 0))
        self.rect = self.image.get_rect(topleft=(x, y))

        # 运动属性
        self.hspeed = 0 # 水平速度
        self.vspeed = 0 # 垂直速度
        self.jump_speed = 8.5
        self.djump_speed = 7
        self.has_djump = False
        self.gravity = 0.3
        self.max_hspeed = 3 # 最大水平速度
        self.max_vspeed = 9 # 最大垂直速度

        # 碰撞状态
        self.collisions = {'up': False, 'down': False, 'right': False, 'left': False}
        self.air_time = 0
        self.on_ground = False
        self.jump_pressed = False
        self.jump_triggered = False

        # 状态
        self.alive: bool = True
        self.facing_right = True

        # 动画
        self.animations = {}
        self.current_state = 'idle'
        self.current_frame = 0
        self.frame_timer = 0
        self.frame_interval = 0.11
        self._load_sprite()
        self._set_state('idle')

        # 子弹
        self.bullets: list[Bullet] = []
        self.bullet_limit = 4  # 参考 iwPygame 和 GM yuuutu 引擎：最多 4 颗

    def jump(self):
        """普通跳跃 + 二段跳，只在按键瞬间触发"""
        if self.jump_triggered:
            return
        self.jump_triggered = True

        if self.air_time <= 2:
            self.vspeed = -self.jump_speed
            self.has_djump = True
        elif self.has_djump:
            self.vspeed = -self.djump_speed
            self.has_djump = False

    def vjump(self):
        """松键提前终止垂直速度（短跳）"""
        if self.vspeed < -0.05:
            self.vspeed *= 0.45

    def shoot(self):
        """发射子弹，场上最多 self.bullet_limit 颗"""
        if len(self.bullets) >= self.bullet_limit:
            return

        direction = 1 if self.facing_right else -1
        # 子弹从玩家朝向的一侧射出，位置在玩家中心稍偏外
        spawn_x = self.rect.centerx + direction * 5
        spawn_y = self.rect.centery + 5
        self.bullets.append(Bullet(spawn_x, spawn_y, direction))

    def handle_event(self, event):
        """处理键盘事件"""
        if not self.alive:
            return
        if event.type == KEYDOWN:
            self.jump_triggered = False
            if event.key == K_LEFT:
                self.hspeed = -self.max_hspeed
                self.facing_right = False
            elif event.key == K_RIGHT:
                self.hspeed = self.max_hspeed
                self.facing_right = True
            elif event.key in (K_LSHIFT, K_RSHIFT):
                self.jump_pressed = True
                self.jump()
            elif event.key == K_z:
                self.shoot()
        elif event.type == KEYUP:
            if event.key == K_LEFT and self.hspeed < 0:
                self.hspeed = 0
            elif event.key == K_RIGHT and self.hspeed > 0:
                self.hspeed = 0
            elif event.key in (K_LSHIFT, K_RSHIFT, K_UP, K_z):
                self.jump_pressed = False
                self.vjump()

    def update(self, platforms: pygame.sprite.Group, dt: float=1/60) -> None:
        """
        每帧更新（帧率无关的运动计算）
        
        参数:
            dt: 距离上一帧的时间（秒）
                - 60 FPS 时: dt = 1/60 ≈ 0.0167
                - 30 FPS 时: dt = 1/30 ≈ 0.0333
                - 144 FPS 时: dt = 1/144 ≈ 0.0069
        """
        if not self.alive:
            return

        # 重置碰撞状态
        self.collisions = {'up': False, 'down': False, 'right': False, 'left': False}

        # ============================================
        # 动画状态更新（根据当前运动状态选择动画）
        # ============================================
        if not self.on_ground:
            if self.vspeed > 0:
                self._set_state('fall')
            elif getattr(self, '_is_djump', False):
                self._set_state('djump')
            else:
                self._set_state('jump')
        elif self.hspeed != 0:
            self._set_state('walk')
        else:
            self._set_state('idle')
        self._update_animation(dt)

        # ============================================
        # 落地检测（用于重置跳跃）
        # ============================================
        was_grounded = self.on_ground
        self.on_ground = False

        # ============================================
        # 重力应用（帧率无关）
        # 公式: vspeed += gravity * dt * 60
        # 
        # 解释:
        #   - gravity 的单位是 像素/秒²（GM 的重力单位）
        #   - dt 的单位是 秒（每帧的时间）
        #   - 乘以 60 是为了归一化（60 FPS 基准）
        # 
        # 示例（假设 60 FPS）:
        #   dt = 1/60
        #   新速度 = 0 + 0.3 * (1/60) * 60 = 0 + 0.3
        #   每秒速度增加 = 0.3 * 60 = 18 像素/秒
        # ============================================
        self.vspeed += self.gravity * dt * 60
        
        # 限制最大下落速度，防止速度过快穿墙
        if self.vspeed > self.max_vspeed:
            self.vspeed = self.max_vspeed

        # ============================================
        # 水平移动（帧率无关）
        # 公式: rect.x += hspeed * dt * 60
        # 
        # 解释:
        #   - hspeed 的单位是 像素/秒
        #   - dt 是每帧的秒数
        #   - 乘以 60 归一化到每秒的移动量
        # 
        # 示例（假设 60 FPS，hspeed = 2）:
        #   dt = 1/60
        #   每帧移动 = 2 * (1/60) * 60 = 2 像素
        #   每秒移动 = 2 * 60 = 120 像素
        # 
        # 对比 30 FPS:
        #   dt = 1/30
        #   每帧移动 = 2 * (1/30) * 60 = 4 像素
        #   每秒移动 = 4 * 30 = 120 像素（相同！）
        # ============================================
        self.rect.x += self.hspeed * dt * 60
        self._check_collision(platforms, axis='x')

        # ============================================
        # 垂直移动（帧率无关）
        # 注意：需要分开处理 X 和 Y 轴的碰撞，否则会有穿透问题
        # ============================================
        self.rect.y += self.vspeed * dt * 60
        self._check_collision(platforms, axis='y')

        # ============================================
        # 落地后重置跳跃状态
        # ============================================
        if self.on_ground and not was_grounded:
            self.air_time = 0
            self.has_djump = False
        elif not self.on_ground:
            self.air_time += 1

        # ============================================
        # 子弹更新
        # ============================================
        for bullet in self.bullets[:]:
            bullet.update(dt)
            # 寿命到期
            if not bullet.is_alive():
                self.bullets.remove(bullet)
                continue
            # 与实心块碰撞则销毁
            if pygame.sprite.spritecollideany(bullet, platforms):
                self.bullets.remove(bullet)
                continue

    def _check_collision(self, platforms, axis):
        """碰撞检测"""
        for sprite in pygame.sprite.spritecollide(self, platforms, False):
            if sprite.type == 'spike':
                self.die()
                return
            if sprite.type == 'solid':
                if axis == 'x':
                    if self.hspeed > 0:
                        self.rect.right = sprite.rect.left
                        self.collisions['right'] = True
                    elif self.hspeed < 0:
                        self.rect.left = sprite.rect.right
                        self.collisions['left'] = True
                    self.hspeed = 0
                elif axis == 'y':
                    if self.vspeed > 0:
                        self.rect.bottom = sprite.rect.top
                        self.collisions['down'] = True
                        self.on_ground = True
                    elif self.vspeed < 0:
                        self.rect.top = sprite.rect.bottom
                        self.collisions['up'] = True
                    self.vspeed = 0

    def _load_sprite(self):
        """加载玩家所有动画贴图"""
        self.animations = {
            'idle':     load_images('the_kid/idle'),
            'walk':     load_images('the_kid/walk'),
            'jump':     load_images('the_kid/jump'),
            'djump':    load_images('the_kid/jump')[1:],
            'fall':     load_images('the_kid/fall'),
            'walljump': load_images('the_kid/walljump'),
        }

    def _set_state(self, state):
        """切换动画状态"""
        if self.current_state != state:
            self.current_state = state
            self.current_frame = 0
            self.frame_timer = 0
            if state == 'jump' and getattr(self, '_is_djump', False):
                self.current_frame = 1
                self._is_djump = False

    def _update_animation(self, dt):
        """更新动画帧"""
        frames = self.animations.get(self.current_state, [])
        if not frames:
            return

        frame_intervals = {
            'walk': 0.04,
            'idle': 0.11,
            'jump': 0.1,
            'fall': 0.1,
            'walljump': 0.1,
        }
        interval = frame_intervals.get(self.current_state, 0.08)

        self.frame_timer += dt
        if self.frame_timer >= interval:
            self.frame_timer = 0
            self.current_frame = (self.current_frame + 1) % len(frames)

        self.image = frames[self.current_frame]
        if not self.facing_right:
            self.image = pygame.transform.flip(self.image, True, False)

    def die(self):
        self.alive = False
        # 可播放死亡音效、触发复活等

    def draw(self, screen, camera_offset=(0, 0)):
        """根据摄像机偏移绘制玩家和子弹"""
        for bullet in self.bullets:
            bullet.draw(screen, camera_offset)
        screen.blit(self.image, (self.rect.x - camera_offset[0],
                                 self.rect.y - camera_offset[1]))