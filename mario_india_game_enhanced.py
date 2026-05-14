import pygame
import sys
import random
import math
from enum import Enum
from dataclasses import dataclass
from typing import List, Tuple, Optional

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Constants
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 700
FPS = 60
GRAVITY = 0.5
JUMP_STRENGTH = -15

# Colors (Indian themed)
SAFFRON = (255, 140, 0)      # Saffron orange
DEEP_BLUE = (25, 25, 112)    # Deep blue
EMERALD = (50, 205, 50)      # Emerald green
GOLD = (255, 215, 0)         # Gold
CREAM = (245, 245, 220)      # Cream
DARK_RED = (139, 0, 0)       # Dark red
SKY_BLUE = (135, 206, 250)   # Sky blue
PURPLE = (128, 0, 128)       # Purple for power-ups
LIGHT_GREEN = (144, 238, 144) # Light green

class Difficulty(Enum):
    EASY = 1
    NORMAL = 2
    HARD = 3

class GameState(Enum):
    DIFFICULTY_SELECT = 0
    MENU = 1
    PLAYING = 2
    LEVEL_COMPLETE = 3
    GAME_OVER = 4
    BOSS_FIGHT = 5
    GAME_WON = 6

class PowerUpType(Enum):
    SHIELD = 1
    SPEED_BOOST = 2
    DOUBLE_JUMP = 3
    INVINCIBLE = 4

@dataclass
class Vector2:
    x: float
    y: float

class SoundManager:
    """Manages all game sounds"""
    def __init__(self):
        self.enabled = True
        self.volume = 0.5

    def play_jump(self):
        if self.enabled:
            self.generate_beep(440, 100)

    def play_coin(self):
        if self.enabled:
            self.generate_beep(880, 150)

    def play_hit(self):
        if self.enabled:
            self.generate_beep(220, 200)

    def play_boss_hit(self):
        if self.enabled:
            self.generate_beep(600, 300)

    def play_level_complete(self):
        if self.enabled:
            self.generate_beep(1200, 500)

    def play_power_up(self):
        if self.enabled:
            self.generate_beep(1000, 250)

    def generate_beep(self, frequency, duration_ms):
        """Generate a simple beep sound"""
        try:
            sample_rate = 22050
            duration = int(duration_ms * sample_rate / 1000)
            frames = int(sample_rate / frequency)
            arr = [int(32767.0 * 0.3 * math.sin(2.0 * math.pi * x / frames)) for x in range(duration)]
            arr_array = pygame.sndarray.make_sound(arr)
            arr_array.play()
        except:
            pass  # Sound generation failed, continue without sound

class PowerUp(pygame.sprite.Sprite):
    def __init__(self, x, y, power_type: PowerUpType):
        super().__init__()
        self.power_type = power_type
        self.width = 25
        self.height = 25
        self.image = pygame.Surface((self.width, self.height))

        if power_type == PowerUpType.SHIELD:
            self.image.fill(LIGHT_GREEN)
        elif power_type == PowerUpType.SPEED_BOOST:
            self.image.fill(PURPLE)
        elif power_type == PowerUpType.DOUBLE_JUMP:
            self.image.fill(GOLD)
        else:
            self.image.fill(SAFFRON)

        self.rect = self.image.get_rect(topleft=(x, y))
        self.bob_offset = 0
        self.bob_speed = 0.15
        self.rotation = 0

    def update(self):
        self.bob_offset += self.bob_speed
        self.rect.y += math.sin(self.bob_offset) * 0.5
        self.rotation = (self.rotation + 5) % 360

    def draw(self, surface):
        # Draw rotating star for power-up
        size = 12
        angle_step = 72
        points = []
        for i in range(5):
            angle = math.radians(i * angle_step + self.rotation)
            x = self.rect.centerx + size * math.cos(angle)
            y = self.rect.centery + size * math.sin(angle)
            points.append((x, y))

            angle2 = math.radians(i * angle_step + 36 + self.rotation)
            x2 = self.rect.centerx + (size // 2) * math.cos(angle2)
            y2 = self.rect.centery + (size // 2) * math.sin(angle2)
            points.append((x2, y2))

        if len(points) > 2:
            pygame.draw.polygon(surface, self.get_color(), points)

    def get_color(self):
        if self.power_type == PowerUpType.SHIELD:
            return LIGHT_GREEN
        elif self.power_type == PowerUpType.SPEED_BOOST:
            return PURPLE
        elif self.power_type == PowerUpType.DOUBLE_JUMP:
            return GOLD
        else:
            return SAFFRON

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.width = 40
        self.height = 50
        self.image = pygame.Surface((self.width, self.height))
        self.image.fill(SAFFRON)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.vel = Vector2(0, 0)
        self.on_ground = False
        self.facing_right = True
        self.health = 3
        self.max_health = 3
        self.invulnerable = 0
        self.jump_available = True
        self.double_jump_available = False

        # Power-ups
        self.has_shield = False
        self.speed_boost_time = 0
        self.double_jump_time = 0
        self.invincible_time = 0

        self.base_speed = 6
        self.sound_manager = SoundManager()

    def handle_input(self, keys):
        speed = self.base_speed
        if self.speed_boost_time > 0:
            speed *= 1.5

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vel.x = -speed
            self.facing_right = False
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vel.x = speed
            self.facing_right = True
        else:
            self.vel.x = 0

        if (keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]):
            if self.on_ground and self.jump_available:
                self.vel.y = JUMP_STRENGTH
                self.on_ground = False
                self.jump_available = False
                self.sound_manager.play_jump()
            elif self.double_jump_available and self.double_jump_time > 0:
                self.vel.y = JUMP_STRENGTH
                self.double_jump_available = False
                self.sound_manager.play_jump()

    def update(self, platforms, enemies, coins, power_ups, world_width):
        # Update power-up timers
        self.speed_boost_time -= 1
        self.double_jump_time -= 1
        self.invincible_time -= 1

        # Gravity
        self.vel.y += GRAVITY
        self.vel.y = min(self.vel.y, 15)

        # Boundary checking
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > world_width:
            self.rect.right = world_width

        # Platform collision
        self.rect.y += self.vel.y
        self.on_ground = False

        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.vel.y > 0:
                    self.rect.bottom = platform.rect.top
                    self.vel.y = 0
                    self.on_ground = True
                    self.jump_available = True
                    self.double_jump_available = self.double_jump_time > 0
                elif self.vel.y < 0:
                    self.rect.top = platform.rect.bottom
                    self.vel.y = 0

        self.rect.x += self.vel.x

        # Enemy collision
        for enemy in enemies:
            if self.rect.colliderect(enemy.rect):
                if self.invulnerable <= 0 and self.invincible_time <= 0:
                    if self.has_shield:
                        self.has_shield = False
                        self.sound_manager.play_hit()
                    else:
                        self.health -= 1
                        self.sound_manager.play_hit()
                    self.invulnerable = 120

        # Power-up collection
        for power_up in power_ups:
            if self.rect.colliderect(power_up.rect):
                self.apply_power_up(power_up.power_type)
                power_up.kill()
                self.sound_manager.play_power_up()

        # Coin collection
        for coin in coins:
            if self.rect.colliderect(coin.rect):
                coin.kill()
                self.sound_manager.play_coin()

        # Death by falling
        if self.rect.top > SCREEN_HEIGHT:
            return False

        self.invulnerable -= 1
        return True

    def apply_power_up(self, power_type: PowerUpType):
        if power_type == PowerUpType.SHIELD:
            self.has_shield = True
        elif power_type == PowerUpType.SPEED_BOOST:
            self.speed_boost_time = 300
        elif power_type == PowerUpType.DOUBLE_JUMP:
            self.double_jump_time = 300
            self.double_jump_available = True
        elif power_type == PowerUpType.INVINCIBLE:
            self.invincible_time = 300

    def draw(self, surface):
        if self.invulnerable % 10 < 5 or self.invincible_time > 0:
            # Draw player as an Indian warrior
            pygame.draw.rect(surface, SAFFRON, self.rect, border_radius=8)

            # Draw turban/crown
            pygame.draw.polygon(surface, GOLD, [
                (self.rect.left + 5, self.rect.top + 5),
                (self.rect.left + 15, self.rect.top - 5),
                (self.rect.right - 15, self.rect.top - 5),
                (self.rect.right - 5, self.rect.top + 5)
            ])

            # Draw eyes
            eye_y = self.rect.top + 12
            if self.facing_right:
                pygame.draw.circle(surface, DEEP_BLUE, (self.rect.left + 10, eye_y), 3)
                pygame.draw.circle(surface, DEEP_BLUE, (self.rect.left + 22, eye_y), 3)
            else:
                pygame.draw.circle(surface, DEEP_BLUE, (self.rect.right - 10, eye_y), 3)
                pygame.draw.circle(surface, DEEP_BLUE, (self.rect.right - 22, eye_y), 3)

            # Draw shield if active
            if self.has_shield:
                pygame.draw.circle(surface, LIGHT_GREEN, self.rect.center, 25, 3)

            # Draw speed boost aura
            if self.speed_boost_time > 0:
                pygame.draw.circle(surface, PURPLE, self.rect.center, 28, 2)

            # Draw invincible aura
            if self.invincible_time > 0:
                pygame.draw.circle(surface, GOLD, self.rect.center, 30, 3)

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, patrol_range=100, speed=3):
        super().__init__()
        self.width = 35
        self.height = 35
        self.image = pygame.Surface((self.width, self.height))
        self.image.fill(DARK_RED)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.vel_x = -speed
        self.start_x = x
        self.patrol_range = patrol_range

    def update(self):
        self.rect.x += self.vel_x

        if self.rect.x < self.start_x - self.patrol_range:
            self.vel_x = abs(self.vel_x)
        elif self.rect.x > self.start_x + self.patrol_range:
            self.vel_x = -abs(self.vel_x)

    def draw(self, surface):
        pygame.draw.rect(surface, DARK_RED, self.rect, border_radius=3)
        # Draw demon face
        pygame.draw.circle(surface, GOLD, (self.rect.left + 8, self.rect.top + 8), 3)
        pygame.draw.circle(surface, GOLD, (self.rect.right - 8, self.rect.top + 8), 3)
        # Horns
        pygame.draw.line(surface, GOLD, (self.rect.left + 8, self.rect.top), (self.rect.left + 5, self.rect.top - 8), 2)
        pygame.draw.line(surface, GOLD, (self.rect.right - 8, self.rect.top), (self.rect.right - 5, self.rect.top - 8), 2)

class Boss(pygame.sprite.Sprite):
    def __init__(self, x, y, difficulty=Difficulty.NORMAL):
        super().__init__()
        self.width = 80
        self.height = 80
        self.image = pygame.Surface((self.width, self.height))
        self.image.fill(DARK_RED)
        self.rect = self.image.get_rect(topleft=(x, y))

        # Difficulty adjustments
        health_multiplier = 1 if difficulty == Difficulty.EASY else (1.5 if difficulty == Difficulty.NORMAL else 2)
        self.health = int(5 * health_multiplier)
        self.max_health = self.health

        self.vel_x = -4 if difficulty == Difficulty.EASY else (-5 if difficulty == Difficulty.NORMAL else -6)
        self.attack_timer = 0
        self.projectiles = pygame.sprite.Group()
        self.invulnerable = 0
        self.difficulty = difficulty

    def update(self):
        self.rect.x += self.vel_x
        if self.rect.left < 100 or self.rect.right > SCREEN_WIDTH - 100:
            self.vel_x *= -1

        self.attack_timer += 1
        attack_interval = 80 if self.difficulty == Difficulty.EASY else (60 if self.difficulty == Difficulty.NORMAL else 40)

        if self.attack_timer > attack_interval:
            self.shoot()
            self.attack_timer = 0

        self.invulnerable -= 1

        for proj in self.projectiles:
            proj.update()
            if proj.rect.x < 0 or proj.rect.x > SCREEN_WIDTH:
                proj.kill()

    def shoot(self):
        projectile = Projectile(self.rect.centerx, self.rect.centery, -5, 0)
        self.projectiles.add(projectile)
        projectile = Projectile(self.rect.centerx, self.rect.centery, 5, 0)
        self.projectiles.add(projectile)

        if self.difficulty == Difficulty.HARD:
            projectile = Projectile(self.rect.centerx, self.rect.centery, -3, -3)
            self.projectiles.add(projectile)
            projectile = Projectile(self.rect.centerx, self.rect.centery, 3, -3)
            self.projectiles.add(projectile)

    def take_damage(self):
        if self.invulnerable <= 0:
            self.health -= 1
            self.invulnerable = 30

    def draw(self, surface):
        if self.invulnerable % 10 < 5:
            pygame.draw.rect(surface, DARK_RED, self.rect, border_radius=10)

            # Crown on top
            pygame.draw.polygon(surface, GOLD, [
                (self.rect.centerx - 25, self.rect.top + 5),
                (self.rect.centerx - 15, self.rect.top - 15),
                (self.rect.centerx, self.rect.top + 5),
                (self.rect.centerx + 15, self.rect.top - 15),
                (self.rect.centerx + 25, self.rect.top + 5)
            ])

            # Eyes
            pygame.draw.circle(surface, GOLD, (self.rect.left + 20, self.rect.top + 25), 4)
            pygame.draw.circle(surface, GOLD, (self.rect.right - 20, self.rect.top + 25), 4)

        # Draw projectiles
        for proj in self.projectiles:
            proj.draw(surface)

class Projectile(pygame.sprite.Sprite):
    def __init__(self, x, y, vel_x, vel_y):
        super().__init__()
        self.width = 10
        self.height = 10
        self.image = pygame.Surface((self.width, self.height))
        self.image.fill(GOLD)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.vel_x = vel_x
        self.vel_y = vel_y

    def update(self):
        self.rect.x += self.vel_x
        self.rect.y += self.vel_y

    def draw(self, surface):
        pygame.draw.circle(surface, GOLD, self.rect.center, 5)

class Coin(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.width = 20
        self.height = 20
        self.image = pygame.Surface((self.width, self.height))
        self.image.fill(GOLD)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.rotation = 0

    def update(self):
        self.rotation = (self.rotation + 5) % 360

    def draw(self, surface):
        pygame.draw.circle(surface, GOLD, self.rect.center, 10)
        pygame.draw.circle(surface, SAFFRON, self.rect.center, 7)
        # Draw rupee symbol (₹) representation
        pygame.draw.line(surface, DEEP_BLUE,
                        (self.rect.centerx - 3, self.rect.centery - 3),
                        (self.rect.centerx + 3, self.rect.centery - 3), 2)

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, color=EMERALD, is_spike=False):
        super().__init__()
        self.width = width
        self.height = height
        self.color = color
        self.is_spike = is_spike
        self.image = pygame.Surface((width, height))
        self.image.fill(color)
        self.rect = self.image.get_rect(topleft=(x, y))

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect, border_radius=5)

        if self.is_spike:
            # Draw spikes
            spike_spacing = 20
            for i in range(0, self.width, spike_spacing):
                pygame.draw.polygon(surface, DARK_RED, [
                    (self.rect.left + i + 5, self.rect.top),
                    (self.rect.left + i + 10, self.rect.top - 8),
                    (self.rect.left + i + 15, self.rect.top)
                ])
        else:
            # Temple pattern
            if self.width > 50:
                for i in range(0, self.width, 30):
                    pygame.draw.circle(surface, SAFFRON, (self.rect.left + i, self.rect.top + 5), 3)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("🏛️ Temple Quest - Indian Mario Adventure 🏛️")
        self.clock = pygame.time.Clock()
        self.state = GameState.DIFFICULTY_SELECT
        self.difficulty = Difficulty.NORMAL

        self.font_large = pygame.font.Font(None, 56)
        self.font_medium = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 24)

        self.score = 0
        self.level = 1
        self.total_coins = 0
        self.levels_count = 8

    def init_level(self):
        self.player = Player(50, SCREEN_HEIGHT - 150)
        self.platforms = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.coins = pygame.sprite.Group()
        self.power_ups = pygame.sprite.Group()
        self.boss = None

        if self.level == 1:
            self.create_level_1()
        elif self.level == 2:
            self.create_level_2()
        elif self.level == 3:
            self.create_level_3()
        elif self.level == 4:
            self.create_level_4()
        elif self.level == 5:
            self.create_level_5()
        elif self.level == 6:
            self.create_level_6()
        elif self.level == 7:
            self.create_level_7()
        elif self.level == 8:
            self.create_boss_level()

    def create_level_1(self):
        """Temple Gardens"""
        ground = Platform(0, SCREEN_HEIGHT - 50, SCREEN_WIDTH, 50, EMERALD)
        self.platforms.add(ground)

        platforms_data = [
            (200, 550, 150, 20),
            (450, 490, 150, 20),
            (700, 550, 150, 20),
            (150, 380, 200, 20),
            (750, 380, 200, 20),
            (400, 280, 150, 20),
        ]

        for x, y, w, h in platforms_data:
            self.platforms.add(Platform(x, y, w, h, EMERALD))

        # Difficulty adjustment
        enemy_speed = 2 if self.difficulty == Difficulty.EASY else (3 if self.difficulty == Difficulty.NORMAL else 4)
        enemy_data = [
            (300, SCREEN_HEIGHT - 100, 80),
            (550, SCREEN_HEIGHT - 100, 80),
        ]

        for x, y, patrol in enemy_data:
            self.enemies.add(Enemy(x, y, patrol, enemy_speed))

        coin_positions = [
            (220, 510), (470, 450), (720, 510),
            (200, 330), (800, 330), (450, 230)
        ]

        for x, y in coin_positions:
            self.coins.add(Coin(x, y))
            self.total_coins += 1

        # Add a power-up
        self.power_ups.add(PowerUp(600, 430, PowerUpType.SHIELD))

    def create_level_2(self):
        """Temple Steps"""
        ground = Platform(0, SCREEN_HEIGHT - 50, SCREEN_WIDTH, 50, EMERALD)
        self.platforms.add(ground)

        platforms_data = [
            (100, 600, 120, 20),
            (280, 540, 120, 20),
            (460, 480, 120, 20),
            (640, 540, 120, 20),
            (820, 600, 120, 20),
            (200, 350, 100, 20),
            (800, 350, 100, 20),
            (400, 250, 100, 20),
        ]

        for x, y, w, h in platforms_data:
            self.platforms.add(Platform(x, y, w, h, EMERALD))

        enemy_speed = 2.5 if self.difficulty == Difficulty.EASY else (3.5 if self.difficulty == Difficulty.NORMAL else 5)
        enemy_count = 3 if self.difficulty == Difficulty.EASY else (5 if self.difficulty == Difficulty.NORMAL else 7)

        enemy_data = [
            (200, 500, 100),
            (500, 440, 100),
            (750, 500, 100),
        ]

        for x, y, patrol in enemy_data:
            self.enemies.add(Enemy(x, y, patrol, enemy_speed))

        coin_positions = [
            (150, 560), (330, 500), (510, 440), (690, 500), (870, 560),
            (250, 300), (750, 300), (450, 200)
        ]

        for x, y in coin_positions:
            self.coins.add(Coin(x, y))
            self.total_coins += 1

        self.power_ups.add(PowerUp(500, 380, PowerUpType.SPEED_BOOST))

    def create_level_3(self):
        """Sacred Hall"""
        ground = Platform(0, SCREEN_HEIGHT - 50, SCREEN_WIDTH, 50, EMERALD)
        self.platforms.add(ground)

        platforms_data = [
            (0, 500, 200, 20),
            (300, 450, 150, 20),
            (600, 500, 150, 20),
            (900, 450, 200, 20),
            (200, 320, 200, 20),
            (800, 320, 200, 20),
            (400, 180, 150, 20),
        ]

        for x, y, w, h in platforms_data:
            self.platforms.add(Platform(x, y, w, h, EMERALD))

        enemy_speed = 3 if self.difficulty == Difficulty.EASY else (4 if self.difficulty == Difficulty.NORMAL else 5.5)

        enemy_data = [
            (150, 450, 100),
            (450, 400, 100),
            (750, 450, 100),
            (300, 270, 80),
            (900, 270, 80),
        ]

        for x, y, patrol in enemy_data:
            self.enemies.add(Enemy(x, y, patrol, enemy_speed))

        coin_positions = [
            (100, 450), (350, 400), (650, 450), (950, 400),
            (300, 270), (850, 270), (475, 130)
        ]

        for x, y in coin_positions:
            self.coins.add(Coin(x, y))
            self.total_coins += 1

        self.power_ups.add(PowerUp(600, 230, PowerUpType.DOUBLE_JUMP))

    def create_level_4(self):
        """Spice Market"""
        ground = Platform(0, SCREEN_HEIGHT - 50, SCREEN_WIDTH, 50, EMERALD)
        self.platforms.add(ground)

        # Add spike platforms
        platforms_data = [
            (100, 550, 120, 20, False),
            (300, 480, 120, 20, False),
            (500, 550, 120, 20, False),
            (700, 480, 120, 20, False),
            (900, 550, 120, 20, False),
            (200, 350, 150, 20, False),
            (800, 350, 150, 20, False),
            (450, 220, 120, 20, False),
        ]

        for x, y, w, h, is_spike in platforms_data:
            self.platforms.add(Platform(x, y, w, h, EMERALD, is_spike))

        enemy_speed = 3 if self.difficulty == Difficulty.EASY else (4.5 if self.difficulty == Difficulty.NORMAL else 6)

        for i in range(5 if self.difficulty != Difficulty.HARD else 8):
            x = random.randint(100, 900)
            y = random.randint(200, 500)
            self.enemies.add(Enemy(x, y, 100, enemy_speed))

        coin_positions = [
            (150, 500), (350, 430), (550, 500), (750, 430), (950, 500),
            (275, 300), (825, 300), (500, 170)
        ]

        for x, y in coin_positions:
            self.coins.add(Coin(x, y))
            self.total_coins += 1

        self.power_ups.add(PowerUp(700, 380, PowerUpType.INVINCIBLE))

    def create_level_5(self):
        """Mountain Path"""
        ground = Platform(0, SCREEN_HEIGHT - 50, SCREEN_WIDTH, 50, EMERALD)
        self.platforms.add(ground)

        # Zigzag platforms
        for i in range(8):
            x = 100 + i * 140
            y = SCREEN_HEIGHT - 150 - (i % 2) * 80
            self.platforms.add(Platform(x, y, 120, 20, EMERALD))

        enemy_speed = 3.5 if self.difficulty == Difficulty.EASY else (4.5 if self.difficulty == Difficulty.NORMAL else 6.5)

        for i in range(6 if self.difficulty != Difficulty.HARD else 10):
            x = random.randint(50, 1100)
            y = random.randint(250, 500)
            self.enemies.add(Enemy(x, y, 120, enemy_speed))

        coin_positions = [
            (160, 480), (300, 380), (440, 480), (580, 380),
            (720, 480), (860, 380), (1000, 480), (600, 200)
        ]

        for x, y in coin_positions:
            self.coins.add(Coin(x, y))
            self.total_coins += 1

        self.power_ups.add(PowerUp(300, 320, PowerUpType.SHIELD))
        self.power_ups.add(PowerUp(900, 320, PowerUpType.SPEED_BOOST))

    def create_level_6(self):
        """Golden Palace"""
        ground = Platform(0, SCREEN_HEIGHT - 50, SCREEN_WIDTH, 50, EMERALD)
        self.platforms.add(ground)

        # More complex layout
        platforms_data = [
            (0, 600, 150, 20),
            (200, 550, 150, 20),
            (400, 500, 150, 20),
            (600, 450, 150, 20),
            (800, 500, 150, 20),
            (1000, 550, 150, 20),
            (100, 320, 200, 20),
            (900, 320, 200, 20),
            (450, 180, 150, 20),
        ]

        for x, y, w, h in platforms_data:
            self.platforms.add(Platform(x, y, w, h, EMERALD))

        enemy_speed = 4 if self.difficulty == Difficulty.EASY else (5 if self.difficulty == Difficulty.NORMAL else 7)

        for i in range(8 if self.difficulty != Difficulty.HARD else 12):
            x = random.randint(50, 1100)
            y = random.randint(250, 500)
            self.enemies.add(Enemy(x, y, 100, enemy_speed))

        coin_positions = [
            (75, 550), (275, 500), (475, 450), (675, 400), (875, 450),
            (1075, 500), (200, 270), (900, 270), (525, 130)
        ]

        for x, y in coin_positions:
            self.coins.add(Coin(x, y))
            self.total_coins += 1

        self.power_ups.add(PowerUp(400, 410, PowerUpType.DOUBLE_JUMP))
        self.power_ups.add(PowerUp(800, 410, PowerUpType.INVINCIBLE))

    def create_level_7(self):
        """Ancient Temple"""
        ground = Platform(0, SCREEN_HEIGHT - 50, SCREEN_WIDTH, 50, EMERALD)
        self.platforms.add(ground)

        # Circular pattern
        center_x, center_y = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        import math

        for i in range(6):
            angle = (i * 60) * math.pi / 180
            x = center_x + 300 * math.cos(angle)
            y = center_y + 200 * math.sin(angle)
            self.platforms.add(Platform(int(x) - 60, int(y) - 50, 120, 20, EMERALD))

        # Center platform
        self.platforms.add(Platform(center_x - 75, center_y - 10, 150, 20, GOLD))

        enemy_speed = 4 if self.difficulty == Difficulty.EASY else (5.5 if self.difficulty == Difficulty.NORMAL else 7.5)

        for i in range(10 if self.difficulty != Difficulty.HARD else 15):
            x = random.randint(50, 1100)
            y = random.randint(200, 550)
            self.enemies.add(Enemy(x, y, 120, enemy_speed))

        coin_positions = []
        for i in range(6):
            angle = (i * 60 + 30) * math.pi / 180
            x = center_x + 250 * math.cos(angle)
            y = center_y + 150 * math.sin(angle)
            coin_positions.append((int(x), int(y)))

        for x, y in coin_positions:
            self.coins.add(Coin(x, y))
            self.total_coins += 1

        self.power_ups.add(PowerUp(center_x, center_y - 100, PowerUpType.INVINCIBLE))
        self.power_ups.add(PowerUp(center_x - 150, center_y, PowerUpType.DOUBLE_JUMP))
        self.power_ups.add(PowerUp(center_x + 150, center_y, PowerUpType.SPEED_BOOST))

    def create_boss_level(self):
        """Final Temple Guardian"""
        ground = Platform(0, SCREEN_HEIGHT - 50, SCREEN_WIDTH, 50, EMERALD)
        self.platforms.add(ground)

        boss_platform = Platform(SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT - 250, 400, 20, DARK_RED)
        self.platforms.add(boss_platform)

        self.platforms.add(Platform(50, SCREEN_HEIGHT - 150, 150, 20, EMERALD))
        self.platforms.add(Platform(SCREEN_WIDTH - 200, SCREEN_HEIGHT - 150, 150, 20, EMERALD))

        self.boss = Boss(SCREEN_WIDTH // 2 - 40, SCREEN_HEIGHT - 450, self.difficulty)

        for i in range(8):
            self.coins.add(Coin(SCREEN_WIDTH // 2 - 150 + i * 40, SCREEN_HEIGHT - 350))
            self.total_coins += 1

        self.power_ups.add(PowerUp(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 280, PowerUpType.SHIELD))
        self.power_ups.add(PowerUp(SCREEN_WIDTH // 2 + 100, SCREEN_HEIGHT - 280, PowerUpType.INVINCIBLE))

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if self.state == GameState.DIFFICULTY_SELECT and event.key in [pygame.K_1, pygame.K_2, pygame.K_3]:
                    if event.key == pygame.K_1:
                        self.difficulty = Difficulty.EASY
                    elif event.key == pygame.K_2:
                        self.difficulty = Difficulty.NORMAL
                    else:
                        self.difficulty = Difficulty.HARD
                    self.state = GameState.MENU
                    self.init_level()
                elif self.state == GameState.MENU and event.key == pygame.K_SPACE:
                    self.state = GameState.PLAYING
                elif self.state == GameState.GAME_OVER and event.key == pygame.K_SPACE:
                    self.score = 0
                    self.level = 1
                    self.total_coins = 0
                    self.state = GameState.DIFFICULTY_SELECT
                elif self.state == GameState.LEVEL_COMPLETE and event.key == pygame.K_SPACE:
                    self.level += 1
                    if self.level <= self.levels_count:
                        self.init_level()
                        self.state = GameState.PLAYING
                    else:
                        self.state = GameState.GAME_WON
                elif self.state == GameState.GAME_WON and event.key == pygame.K_SPACE:
                    self.score = 0
                    self.level = 1
                    self.total_coins = 0
                    self.state = GameState.DIFFICULTY_SELECT
        return True

    def update(self):
        if self.state == GameState.PLAYING:
            keys = pygame.key.get_pressed()
            self.player.handle_input(keys)

            if not self.player.update(self.platforms, self.enemies, self.coins, self.power_ups, SCREEN_WIDTH):
                self.state = GameState.GAME_OVER

            for enemy in self.enemies:
                enemy.update()

            for coin in self.coins:
                coin.update()

            for power_up in self.power_ups:
                power_up.update()

            if len(self.coins) == 0 and self.level < self.levels_count:
                self.state = GameState.LEVEL_COMPLETE

            if self.boss:
                self.boss.update()

                for proj in self.boss.projectiles:
                    if self.player.rect.colliderect(proj.rect):
                        if self.player.invulnerable <= 0 and self.player.invincible_time <= 0:
                            if self.player.has_shield:
                                self.player.has_shield = False
                            else:
                                self.player.health -= 1
                            self.player.invulnerable = 120
                            proj.kill()

                if self.player.rect.colliderect(self.boss.rect):
                    if self.player.vel.y > 0:
                        self.boss.take_damage()
                        self.player.vel.y = JUMP_STRENGTH
                        self.score += 100
                        self.player.sound_manager.play_boss_hit()

                if self.boss.health <= 0:
                    self.state = GameState.LEVEL_COMPLETE
                    self.player.sound_manager.play_level_complete()

            self.score += 1

            if self.player.health <= 0:
                self.state = GameState.GAME_OVER

    def draw(self):
        self.screen.fill(SKY_BLUE)

        if self.state == GameState.DIFFICULTY_SELECT:
            self.draw_difficulty_select()
        elif self.state == GameState.MENU:
            self.draw_menu()
        elif self.state == GameState.PLAYING:
            self.draw_game()
        elif self.state == GameState.LEVEL_COMPLETE:
            self.draw_level_complete()
        elif self.state == GameState.GAME_OVER:
            self.draw_game_over()
        elif self.state == GameState.GAME_WON:
            self.draw_game_won()

        pygame.display.flip()

    def draw_difficulty_select(self):
        title = self.font_large.render("Choose Difficulty", True, SAFFRON)
        easy = self.font_medium.render("1. EASY", True, EMERALD)
        normal = self.font_medium.render("2. NORMAL", True, DEEP_BLUE)
        hard = self.font_medium.render("3. HARD", True, DARK_RED)

        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 100))
        easy_rect = easy.get_rect(center=(SCREEN_WIDTH // 2, 250))
        normal_rect = normal.get_rect(center=(SCREEN_WIDTH // 2, 350))
        hard_rect = hard.get_rect(center=(SCREEN_WIDTH // 2, 450))

        self.screen.blit(title, title_rect)
        self.screen.blit(easy, easy_rect)
        self.screen.blit(normal, normal_rect)
        self.screen.blit(hard, hard_rect)

    def draw_menu(self):
        for i in range(0, SCREEN_WIDTH, 100):
            for j in range(0, SCREEN_HEIGHT, 100):
                pygame.draw.rect(self.screen, SAFFRON if (i + j) % 200 == 0 else DEEP_BLUE,
                               (i, j, 50, 50), 2)

        title = self.font_large.render("🏛️ TEMPLE QUEST 🏛️", True, SAFFRON)
        subtitle = self.font_medium.render("Indian Mario Adventure", True, DEEP_BLUE)
        difficulty_text = self.font_small.render(f"Difficulty: {self.difficulty.name}", True, GOLD)
        start_text = self.font_medium.render("Press SPACE to Start", True, EMERALD)

        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 80))
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, 160))
        difficulty_rect = difficulty_text.get_rect(center=(SCREEN_WIDTH // 2, 220))
        start_rect = start_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 150))

        self.screen.blit(title, title_rect)
        self.screen.blit(subtitle, subtitle_rect)
        self.screen.blit(difficulty_text, difficulty_rect)
        self.screen.blit(start_text, start_rect)

        pygame.draw.circle(self.screen, GOLD, (100, 100), 30)
        pygame.draw.circle(self.screen, GOLD, (SCREEN_WIDTH - 100, 100), 30)
        pygame.draw.circle(self.screen, GOLD, (100, SCREEN_HEIGHT - 100), 30)
        pygame.draw.circle(self.screen, GOLD, (SCREEN_WIDTH - 100, SCREEN_HEIGHT - 100), 30)

    def draw_game(self):
        for platform in self.platforms:
            platform.draw(self.screen)

        for enemy in self.enemies:
            enemy.draw(self.screen)

        for coin in self.coins:
            coin.draw(self.screen)

        for power_up in self.power_ups:
            power_up.draw(self.screen)

        self.player.draw(self.screen)

        if self.boss:
            self.boss.draw(self.screen)
            health_bar_width = 200
            health_bar_height = 20
            health_ratio = max(0, self.boss.health / self.boss.max_health)

            pygame.draw.rect(self.screen, DARK_RED,
                           (SCREEN_WIDTH // 2 - health_bar_width // 2, 30, health_bar_width, health_bar_height))
            pygame.draw.rect(self.screen, EMERALD,
                           (SCREEN_WIDTH // 2 - health_bar_width // 2, 30, int(health_bar_width * health_ratio), health_bar_height))

            boss_text = self.font_small.render("BOSS", True, DARK_RED)
            self.screen.blit(boss_text, (SCREEN_WIDTH // 2 - 20, 35))

        level_text = self.font_medium.render(f"Level {self.level}/{self.levels_count}", True, DEEP_BLUE)
        score_text = self.font_medium.render(f"Score: {self.score}", True, DEEP_BLUE)
        coins_text = self.font_small.render(f"₹ {self.total_coins - len(self.coins)}/{self.total_coins}", True, GOLD)
        health_display = "❤️ " * self.player.health
        health_text = self.font_medium.render(health_display, True, DARK_RED)

        self.screen.blit(level_text, (20, 20))
        self.screen.blit(score_text, (20, 60))
        self.screen.blit(coins_text, (SCREEN_WIDTH - 150, 20))
        self.screen.blit(health_text, (SCREEN_WIDTH - 150, 60))

        # Power-up indicators
        if self.player.has_shield:
            shield_text = self.font_small.render("🛡️ SHIELD", True, LIGHT_GREEN)
            self.screen.blit(shield_text, (SCREEN_WIDTH // 2 - 60, 20))
        if self.player.speed_boost_time > 0:
            speed_text = self.font_small.render("⚡ SPEED", True, PURPLE)
            self.screen.blit(speed_text, (SCREEN_WIDTH // 2 + 20, 20))
        if self.player.double_jump_time > 0:
            jump_text = self.font_small.render("🔆 2-JUMP", True, GOLD)
            self.screen.blit(jump_text, (SCREEN_WIDTH // 2 + 120, 20))

    def draw_level_complete(self):
        level_name = [
            "Temple Gardens",
            "Temple Steps",
            "Sacred Hall",
            "Spice Market",
            "Mountain Path",
            "Golden Palace",
            "Ancient Temple",
            "Final Guardian"
        ]

        text = self.font_large.render(f"🎉 LEVEL {self.level} COMPLETE! 🎉", True, SAFFRON)
        next_text = self.font_medium.render("Press SPACE for Next Level", True, EMERALD)
        score_text = self.font_medium.render(f"Score: {self.score}", True, DEEP_BLUE)

        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, 150))
        next_rect = next_text.get_rect(center=(SCREEN_WIDTH // 2, 350))
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, 450))

        self.screen.blit(text, text_rect)
        self.screen.blit(next_text, next_rect)
        self.screen.blit(score_text, score_rect)

    def draw_game_over(self):
        text = self.font_large.render("GAME OVER", True, DARK_RED)
        retry_text = self.font_medium.render("Press SPACE to Select Difficulty", True, EMERALD)
        score_text = self.font_medium.render(f"Final Score: {self.score}", True, DEEP_BLUE)

        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, 200))
        retry_rect = retry_text.get_rect(center=(SCREEN_WIDTH // 2, 350))
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, 450))

        self.screen.blit(text, text_rect)
        self.screen.blit(retry_text, retry_rect)
        self.screen.blit(score_text, score_rect)

    def draw_game_won(self):
        text = self.font_large.render("🏆 YOU CONQUERED ALL TEMPLES! 🏆", True, GOLD)
        msg_text = self.font_medium.render("You Have Restored Peace to the Kingdom!", True, SAFFRON)
        menu_text = self.font_medium.render("Press SPACE to Return to Difficulty Select", True, EMERALD)
        score_text = self.font_medium.render(f"Final Score: {self.score}", True, DEEP_BLUE)
        difficulty_text = self.font_small.render(f"Completed on: {self.difficulty.name}", True, DEEP_BLUE)

        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, 80))
        msg_rect = msg_text.get_rect(center=(SCREEN_WIDTH // 2, 180))
        menu_rect = menu_text.get_rect(center=(SCREEN_WIDTH // 2, 350))
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, 450))
        difficulty_rect = difficulty_text.get_rect(center=(SCREEN_WIDTH // 2, 520))

        self.screen.blit(text, text_rect)
        self.screen.blit(msg_text, msg_rect)
        self.screen.blit(menu_text, menu_rect)
        self.screen.blit(score_text, score_rect)
        self.screen.blit(difficulty_text, difficulty_rect)

    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()
