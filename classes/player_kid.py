import pygame
from pygame.locals import *
from utils.utils import load_images
from classes.bullet import Bullet
from classes.particle import Particle
import random

class PlayerKid(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.spawn_pos = (x, y)  # 记录重生点
        self.image = pygame.Surface((32, 32))
        self.image.fill((255, 200, 0))
        self.rect = self.image.get_rect(topleft=(x, y))

        # 用浮点数记录精确位置，解决每帧移动不足 1 像素时的抖动问题
        self.x = float(x)
        self.y = float(y)

        # 玩家实际碰撞盒比 32x32 贴图小，居中对齐。
        # 这里用 16x28 的矩形 mask，留出贴图边缘作为"安全边距"，
        # 这样玩家只有身体真正碰到刺才会死，而不是贴图边框碰到就死。
        mask_surface = pygame.Surface((32, 32), pygame.SRCALPHA)
        mask_surface.fill((0, 0, 0, 0))  # 周围透明
        pygame.draw.rect(mask_surface, (255, 255, 255, 255), (8, 2, 16, 28))
        self.mask = pygame.mask.from_surface(mask_surface)

        # 运动属性
        self.hspeed = 0 # 水平速度
        self.vspeed = 0 # 垂直速度
        self.jump_speed = 8.5
        self.djump_speed = 7

        # 跳跃状态机：
        # has_djump: 是否还能使用二段跳
        # first_jump_used: 是否已经使用过第一次跳跃（无论是地面跳还是空中跳）
        #
        # 为什么需要 first_jump_used？
        # 在 I Wanna 中，如果角色从平台边缘走下来（没有按过跳），
        # 空中按跳会直接消耗二段跳机会，而不是完全不能跳。
        # 仅靠 has_djump 无法区分"还没跳过"和"二段跳已用完"这两种状态。
        self.has_djump = False
        self.first_jump_used = False

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

        # 加载音效
        self.sfx = {
            'jump': pygame.mixer.Sound('./resources/the_kid/audio/Jump.wav'),
            'djump': pygame.mixer.Sound('./resources/the_kid/audio/Double Jump.wav'),
            'shoot': pygame.mixer.Sound('./resources/the_kid/audio/Shoot.wav'),
            'death': pygame.mixer.Sound('./resources/the_kid/audio/Death.wav'),
        }

        # 子弹
        self.bullets: list[Bullet] = []
        self.bullet_limit = 4  # 参考 iwPygame 和 GM yuuutu 引擎：最多 4 颗

        # 死亡效果
        self.particles: list[Particle] = []
        self.death_gravity = 0.4
        self.game_over_image = self._load_game_over_image()
        self.game_over_delay = 0.5  # 死亡后 0.5 秒显示 GameOver
        self.game_over_timer = 0
        self.show_game_over = False
        self._load_death_placeholder_images()

    def _load_game_over_image(self):
        """加载 GameOver 贴图，找不到则返回 None"""
        try:
            return pygame.image.load('./resources/sprite/ui/game_over/gameover.png').convert_alpha()
        except pygame.error:
            return None

    def _load_death_placeholder_images(self):
        """加载死亡效果占位贴图，后续可替换为真实素材"""
        # # 血液：3x3 红色小方块
        # blood = pygame.Surface((3, 3))
        # blood.fill((200, 0, 0))
        #
        # # 头部：8x8 橙色方块（占位）
        # head = pygame.Surface((8, 8))
        # head.fill((255, 160, 80))
        #
        # # 手臂：4x10 蓝色方块（占位）
        # arm = pygame.Surface((4, 10))
        # arm.fill((80, 120, 200))
        #
        # # 身体/躯干：8x10 黄色方块（占位）
        # body = pygame.Surface((8, 10))
        # body.fill((255, 200, 0))

        def _load(path):
            """加载图片，找不到返回 None"""
            try:
                return pygame.image.load(path).convert_alpha()
            except pygame.error:
                return None

        self.death_images = {
            'blood': _load('./resources/sprite/effects/bloods/blood_1.png'),
            'head': _load('./resources/sprite/effects/body_parts/kid_head_1.png'),
            'hand': _load('./resources/sprite/effects/body_parts/kid_hand_2.png'),
            'body': _load('./resources/sprite/effects/body_parts/kid_body.png'),
            'pants': _load('./resources/sprite/effects/body_parts/kid_pants.png'),
            'foot': _load('./resources/sprite/effects/body_parts/kid_foot.png'),
            'gun': _load('./resources/sprite/effects/body_parts/kid_gun.png'),
        }

    def jump(self):
        """普通跳跃 + 二段跳，只在按键瞬间触发"""
        if self.jump_triggered:
            return
        self.jump_triggered = True

        # 情况 1：在地上或刚离开地面 2 帧内（coyote time）
        # 执行普通跳跃，并开启二段跳资格。
        if self.air_time <= 2:
            self.vspeed = -self.jump_speed
            self.has_djump = True
            self.first_jump_used = True
            # 一段跳音效
            self.sfx['jump'].play().set_volume(0.5)

        # 情况 2：已经在空中，且拥有二段跳资格
        # 这是常规的二段跳（先跳了一次，再按跳）。
        elif self.has_djump:
            self.vspeed = -self.djump_speed
            self.has_djump = False
            # 二段跳音效
            self.sfx['djump'].play().set_volume(0.5)

        # 情况 3：从平台边缘走下来，没按过跳就直接下落
        # 此时 first_jump_used=False，has_djump=False。
        # 原版 I Wanna 允许这种情况下按跳直接消耗二段跳机会。
        elif not self.first_jump_used:
            self.vspeed = -self.djump_speed
            self.first_jump_used = True
            # 这里播放二段跳音效，因为实际消耗的是二段跳
            self.sfx['djump'].play().set_volume(0.5)

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
        # 播放射击音效
        self.sfx['shoot'].play().set_volume(0.5)
        self.bullets.append(Bullet(spawn_x, spawn_y, direction))

    def handle_event(self, event):
        """处理键盘事件"""
        if event.type == KEYDOWN:
            # 死亡状态下按 R 复活
            if not self.alive:
                if event.key == K_r:
                    self.respawn()
                return

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
            elif event.key == K_q:
                self.die()
            elif event.key == K_r:
                self.respawn()
                return
        elif event.type == KEYUP:
            if not self.alive:
                return
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
        # ============================================
        # 死亡状态：只更新粒子和 GameOver 计时器
        # ============================================

        # 防止切窗口/卡顿导致 dt 过大，玩家一飞冲天
        dt = min(dt, 1/30)

        if not self.alive:
            for particle in self.particles[:]:
                particle.update(dt, platforms)
                if not particle.is_alive():
                    self.particles.remove(particle)

            if not self.show_game_over:
                self.game_over_timer += dt
                if self.game_over_timer >= self.game_over_delay:
                    self.show_game_over = True
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
        self.x += self.hspeed * dt * 60
        self.rect.x = int(self.x)
        self._check_collision(platforms, axis='x')

        # ============================================
        # 垂直移动（帧率无关）
        # 注意：需要分开处理 X 和 Y 轴的碰撞，否则会有穿透问题
        # ============================================
        self.y += self.vspeed * dt * 60
        self.rect.y = int(self.y)
        self._check_collision(platforms, axis='y')

        # 如果当前不在地面，探测脚底往下 1 像素是否有实心块
        # 这是为了解决重力小于 1 像素/帧时，玩家悬在空中检测不到地面的抖动问题
        if not self.on_ground:
            check_rect = self.rect.move(0, 1)
            for sprite in platforms:
                if sprite.type == 'solid' and check_rect.colliderect(sprite.rect):
                    self.rect.bottom = sprite.rect.top
                    self.y = float(self.rect.y)
                    self.on_ground = True
                    self.vspeed = 0
                    break

        # ============================================
        # 落地后重置跳跃状态
        # ============================================
        if self.on_ground and not was_grounded:
            self.air_time = 0
            # 落地后清空二段跳和第一次跳跃标记，
            # 这样下次从平台边缘走下来时，又能触发"坠落直接二段跳"的机制。
            self.has_djump = False
            self.first_jump_used = False
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
                # 尖刺使用像素级碰撞（mask），避免矩形碰撞导致的误判。
                # 例如玩家碰到刺的透明角落时不应该死亡。
                # pygame.sprite.collide_mask 会先检查 rect 是否重叠，
                # 重叠后再对比双方 mask 的不透明像素是否真正接触。
                if pygame.sprite.collide_mask(self, sprite):
                    self.die()
                    return
                # 如果 rect 重叠但 mask 没重叠，说明只是透明区域碰到，不做处理。
                continue

            if sprite.type == 'solid':
                if axis == 'x':
                    if self.hspeed > 0:
                        self.rect.right = sprite.rect.left
                        self.collisions['right'] = True
                    elif self.hspeed < 0:
                        self.rect.left = sprite.rect.right
                        self.collisions['left'] = True
                    self.hspeed = 0
                    self.x = float(self.rect.x)
                elif axis == 'y':
                    if self.vspeed > 0:
                        self.rect.bottom = sprite.rect.top
                        self.collisions['down'] = True
                        self.on_ground = True
                    elif self.vspeed < 0:
                        self.rect.top = sprite.rect.bottom
                        self.collisions['up'] = True
                    self.vspeed = 0
                    self.y = float(self.rect.y)

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

    def _get_death_direction(self):
        """
        根据碰撞状态或速度判断死亡时的血液迸溅方向。
        返回值是 (dx, dy) 单位向量，表示血液主要飞溅方向的反方向。
        """
        if self.collisions['down']:
            return (0, -1)   # 从下方撞到刺，血液向上溅
        elif self.collisions['up']:
            return (0, 1)    # 从上方撞到刺，血液向下溅
        elif self.collisions['left']:
            return (1, 0)    # 从左侧撞到刺，血液向右溅
        elif self.collisions['right']:
            return (-1, 0)   # 从右侧撞到刺，血液向左溅

        # 没有碰撞信息时，根据速度反推
        if self.vspeed > 0:
            return (0, -1)
        elif self.vspeed < 0:
            return (0, 1)
        elif self.hspeed > 0:
            return (-1, 0)
        elif self.hspeed < 0:
            return (1, 0)

        return (0, -1)

    def _spawn_death_particles(self, direction):
        """
        生成死亡粒子：血液小方块 + 身体碎片。
        direction: 血液主要飞溅方向 (dx, dy)
        """
        import math
        center_x, center_y = self.rect.center

        def _random_velocity(base_dir, spread, speed_range):
            """
            根据基础方向生成扇形随机速度。
            base_dir: (dx, dy)
            spread: 散射角度（弧度）
            speed_range: (min, max)
            """
            base_angle = math.atan2(-base_dir[1], base_dir[0])
            angle = base_angle + random.uniform(-spread, spread)
            speed = random.uniform(*speed_range)
            vx = math.cos(angle) * speed
            vy = -math.sin(angle) * speed
            return vx, vy

        # ===== 血液粒子 =====
        blood_count = 300
        for _ in range(blood_count):
            vx, vy = _random_velocity(direction, 1.2, (3, 8))
            self.particles.append(Particle(
                center_x + random.randint(-5, 5),
                center_y + random.randint(-5, 5),
                self.death_images['blood'],
                vx, vy,
                gravity=self.death_gravity
            ))

        # ===== 身体碎片 =====
        fragments = [
            ('head', 1),
            ('hand', 2),
            ('body', 1),
            ('pants', 1),
            ('foot', 2),
            ('gun', 1),
        ]
        for part_name, count in fragments:
            for _ in range(count):
                vx, vy = _random_velocity(direction, 0.8, (2, 6))
                self.particles.append(Particle(
                    center_x + random.randint(-8, 8),
                    center_y + random.randint(-8, 8),
                    self.death_images[part_name],
                    vx, vy,
                    gravity=self.death_gravity
                ))

    def die(self):
        """触发死亡：生成粒子、播放音效、准备显示 GameOver"""
        if not self.alive:
            return
        self.alive = False

        # 根据碰撞/速度方向决定血液迸溅方向
        direction = self._get_death_direction()
        self._spawn_death_particles(direction)

        # 死亡音效（如果存在）
        if 'death' in self.sfx:
            self.sfx['death'].play()

        # 重置 GameOver 计时器
        self.game_over_timer = 0
        self.show_game_over = False

    def respawn(self):
        """按 R 复活：重置玩家状态和位置"""
        self.alive = True

        # 必须同时重置浮点位置 self.x/self.y 和 rect 位置。
        # 因为 update() 中物理移动基于 self.x/self.y，rect 只是它们的整数显示同步。
        # 如果只重置 rect.topleft，self.x/self.y 仍保留死亡前的值，下一帧会立即把 rect 拉回原位，
        # 导致角色看似没有重生或重生后瞬间回到死亡位置。
        self.x, self.y = self.spawn_pos[0], self.spawn_pos[1]

        self.rect.topleft = (int(self.x), int(self.y))
        self.hspeed = 0
        self.vspeed = 0
        self.on_ground = False
        self.air_time = 0
        # 复活后清空跳跃标记，确保从重生点边缘走下来时还能触发"坠落直接二段跳"。
        self.has_djump = False
        self.first_jump_used = False
        self.jump_pressed = False
        self.jump_triggered = False
        self.collisions = {'up': False, 'down': False, 'right': False, 'left': False}
        self.facing_right = True

        # 清除死亡粒子和 GameOver
        self.particles.clear()
        self.show_game_over = False
        self.game_over_timer = 0

        # 切回待机动画
        self._set_state('idle')

    def draw(self, screen, camera_offset=(0, 0)):
        """根据摄像机偏移绘制玩家、子弹、粒子和 GameOver"""
        # 绘制子弹
        for bullet in self.bullets:
            bullet.draw(screen, camera_offset)

        # 活着时绘制玩家本体，死亡后隐藏本体，只显示粒子
        if self.alive:
            screen.blit(self.image, (self.rect.x - camera_offset[0],
                                     self.rect.y - camera_offset[1]))

        # 绘制死亡粒子
        for particle in self.particles:
            particle.draw(screen, camera_offset)

        # 绘制 GameOver
        if self.show_game_over and self.game_over_image:
            go_rect = self.game_over_image.get_rect(
                center=(screen.get_width() // 2, screen.get_height() // 2)
            )
            screen.blit(self.game_over_image, go_rect)