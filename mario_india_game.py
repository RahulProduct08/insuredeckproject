import pygame
import sys
import random
from enum import Enum
from dataclasses import dataclass
from typing import List, Tuple

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Constants
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600
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

class GameState(Enum):
    MENU = 1
    PLAYING = 2
    LEVEL_COMPLETE = 3
    GAME_OVER = 4
    BOSS_FIGHT = 5
    GAME_WON = 6

@dataclass
class Vector2:
    x: float
    y: float

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
        self.health = 1
        self.invulnerable = 0
        self.jump_available = True

    def handle_input(self, keys):
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vel.x = -6
            self.facing_right = False
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vel.x = 6
            self.facing_right = True
        else:
            self.vel.x = 0

        if (keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]) and self.on_ground and self.jump_available:
            self.vel.y = JUMP_STRENGTH
            self.on_ground = False
            self.jump_available = False

    def update(self, platforms, enemies, coins, world_width):
        # Gravity
        self.vel.y += GRAVITY
        self.vel.y = min(self.vel.y, 15)  # Terminal velocity

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
                if self.vel.y > 0:  # Falling
                    self.rect.bottom = platform.rect.top
                    self.vel.y = 0
                    self.on_ground = True
                    self.jump_available = True
                elif self.vel.y < 0:  # Jumping
                    self.rect.top = platform.rect.bottom
                    self.vel.y = 0

        self.rect.x += self.vel.x

        # Enemy collision
        for enemy in enemies:
            if self.rect.colliderect(enemy.rect):
                if self.invulnerable <= 0:
                    self.health -= 1
                    self.invulnerable = 120

        # Coin collection
        for coin in coins:
            if self.rect.colliderect(coin.rect):
                coin.kill()

        # Death by falling
        if self.rect.top > SCREEN_HEIGHT:
            return False

        self.invulnerable -= 1
        return True

    def draw(self, surface):
        if self.invulnerable % 10 < 5:  # Blinking effect
            # Draw player (simple block)
            pygame.draw.rect(surface, SAFFRON, self.rect, border_radius=5)

            # Draw eyes
            eye_y = self.rect.top + 10
            if self.facing_right:
                pygame.draw.circle(surface, DEEP_BLUE, (self.rect.left + 10, eye_y), 3)
                pygame.draw.circle(surface, DEEP_BLUE, (self.rect.left + 25, eye_y), 3)
            else:
                pygame.draw.circle(surface, DEEP_BLUE, (self.rect.right - 10, eye_y), 3)
                pygame.draw.circle(surface, DEEP_BLUE, (self.rect.right - 25, eye_y), 3)

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, patrol_range=100):
        super().__init__()
        self.width = 35
        self.height = 35
        self.image = pygame.Surface((self.width, self.height))
        self.image.fill(DARK_RED)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.vel_x = -3
        self.start_x = x
        self.patrol_range = patrol_range

    def update(self):
        self.rect.x += self.vel_x

        # Patrol logic
        if self.rect.x < self.start_x - self.patrol_range:
            self.vel_x = 3
        elif self.rect.x > self.start_x + self.patrol_range:
            self.vel_x = -3

    def draw(self, surface):
        pygame.draw.rect(surface, DARK_RED, self.rect, border_radius=3)
        # Draw eyes
        pygame.draw.circle(surface, GOLD, (self.rect.left + 8, self.rect.top + 8), 3)
        pygame.draw.circle(surface, GOLD, (self.rect.right - 8, self.rect.top + 8), 3)

class Boss(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.width = 80
        self.height = 80
        self.image = pygame.Surface((self.width, self.height))
        self.image.fill(DARK_RED)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.health = 5
        self.vel_x = -4
        self.attack_timer = 0
        self.projectiles = pygame.sprite.Group()
        self.invulnerable = 0

    def update(self):
        # Movement
        self.rect.x += self.vel_x
        if self.rect.left < 100 or self.rect.right > SCREEN_WIDTH - 100:
            self.vel_x *= -1

        # Attack logic
        self.attack_timer += 1
        if self.attack_timer > 60:
            self.shoot()
            self.attack_timer = 0

        self.invulnerable -= 1

        # Update projectiles
        for proj in self.projectiles:
            proj.update()
            if proj.rect.x < 0 or proj.rect.x > SCREEN_WIDTH:
                proj.kill()

    def shoot(self):
        projectile = Projectile(self.rect.centerx, self.rect.centery, -4, 0)
        self.projectiles.add(projectile)
        projectile = Projectile(self.rect.centerx, self.rect.centery, 4, 0)
        self.projectiles.add(projectile)

    def take_damage(self):
        if self.invulnerable <= 0:
            self.health -= 1
            self.invulnerable = 30

    def draw(self, surface):
        if self.invulnerable % 10 < 5:
            pygame.draw.rect(surface, DARK_RED, self.rect, border_radius=10)
            # Crown on top (boss indicator)
            pygame.draw.polygon(surface, GOLD, [
                (self.rect.centerx - 25, self.rect.top + 5),
                (self.rect.centerx - 15, self.rect.top - 10),
                (self.rect.centerx, self.rect.top + 5),
                (self.rect.centerx + 15, self.rect.top - 10),
                (self.rect.centerx + 25, self.rect.top + 5)
            ])

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
        self.bob_offset = 0
        self.bob_speed = 0.1

    def update(self):
        self.bob_offset += self.bob_speed
        self.rect.y = int(self.rect.y + self.bob_speed * 2)

    def draw(self, surface):
        pygame.draw.circle(surface, GOLD, self.rect.center, 10)
        pygame.draw.circle(surface, SAFFRON, self.rect.center, 7)

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, color=EMERALD):
        super().__init__()
        self.width = width
        self.height = height
        self.color = color
        self.image = pygame.Surface((width, height))
        self.image.fill(color)
        self.rect = self.image.get_rect(topleft=(x, y))

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect, border_radius=5)
        # Add temple pattern (simple dots)
        if self.width > 50:
            for i in range(0, self.width, 30):
                pygame.draw.circle(surface, SAFFRON, (self.rect.left + i, self.rect.top + 5), 3)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("🏛️ Temple Quest - Indian Mario Adventure 🏛️")
        self.clock = pygame.time.Clock()
        self.state = GameState.MENU
        self.font_large = pygame.font.Font(None, 56)
        self.font_medium = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 24)

        # Try to create a decorative font for Hindi/Indian feel
        try:
            self.font_hindi = pygame.font.Font(None, 48)
        except:
            self.font_hindi = self.font_medium

        self.score = 0
        self.level = 1
        self.total_coins = 0
        self.init_level()

    def init_level(self):
        self.player = Player(50, SCREEN_HEIGHT - 150)
        self.platforms = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.coins = pygame.sprite.Group()
        self.all_sprites = pygame.sprite.Group()
        self.boss = None

        if self.level == 1:
            self.create_level_1()
        elif self.level == 2:
            self.create_level_2()
        elif self.level == 3:
            self.create_boss_level()

    def create_level_1(self):
        # Ground
        ground = Platform(0, SCREEN_HEIGHT - 50, SCREEN_WIDTH, 50, EMERALD)
        self.platforms.add(ground)

        # Platforms
        platforms_data = [
            (200, 500, 150, 20),
            (450, 450, 150, 20),
            (700, 500, 150, 20),
            (150, 350, 200, 20),
            (700, 350, 200, 20),
            (400, 250, 150, 20),
        ]

        for x, y, w, h in platforms_data:
            self.platforms.add(Platform(x, y, w, h, EMERALD))

        # Enemies
        enemy_data = [
            (300, SCREEN_HEIGHT - 100, 80),
            (550, SCREEN_HEIGHT - 100, 80),
            (250, 300, 60),
        ]

        for x, y, patrol in enemy_data:
            self.enemies.add(Enemy(x, y, patrol))

        # Coins
        coin_positions = [
            (220, 460), (470, 410), (720, 460),
            (200, 300), (750, 300), (450, 200),
            (500, 150), (300, 400)
        ]

        for x, y in coin_positions:
            self.coins.add(Coin(x, y))
            self.total_coins += 1

    def create_level_2(self):
        # Ground
        ground = Platform(0, SCREEN_HEIGHT - 50, SCREEN_WIDTH, 50, EMERALD)
        self.platforms.add(ground)

        # More complex level
        platforms_data = [
            (100, 480, 120, 20),
            (280, 420, 120, 20),
            (460, 360, 120, 20),
            (640, 420, 120, 20),
            (800, 480, 120, 20),
            (200, 250, 100, 20),
            (650, 250, 100, 20),
            (400, 150, 100, 20),
        ]

        for x, y, w, h in platforms_data:
            self.platforms.add(Platform(x, y, w, h, EMERALD))

        # More enemies
        enemy_data = [
            (200, 400, 100),
            (500, 340, 100),
            (750, 400, 100),
            (300, 200, 80),
            (650, 200, 80),
        ]

        for x, y, patrol in enemy_data:
            self.enemies.add(Enemy(x, y, patrol))

        # Coins
        coin_positions = [
            (150, 440), (330, 380), (510, 320), (690, 380), (850, 440),
            (250, 200), (700, 200), (450, 100), (500, 50)
        ]

        for x, y in coin_positions:
            self.coins.add(Coin(x, y))
            self.total_coins += 1

    def create_boss_level(self):
        # Ground
        ground = Platform(0, SCREEN_HEIGHT - 50, SCREEN_WIDTH, 50, EMERALD)
        self.platforms.add(ground)

        # Boss platform
        boss_platform = Platform(SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT - 200, 400, 20, DARK_RED)
        self.platforms.add(boss_platform)

        # Side platforms
        self.platforms.add(Platform(50, SCREEN_HEIGHT - 150, 100, 20, EMERALD))
        self.platforms.add(Platform(SCREEN_WIDTH - 150, SCREEN_HEIGHT - 150, 100, 20, EMERALD))

        # Boss
        self.boss = Boss(SCREEN_WIDTH // 2 - 40, SCREEN_HEIGHT - 400)

        # Coins as health packs
        for i in range(5):
            self.coins.add(Coin(SCREEN_WIDTH // 2 - 100 + i * 50, SCREEN_HEIGHT - 300))
            self.total_coins += 1

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if self.state == GameState.MENU and event.key == pygame.K_SPACE:
                    self.state = GameState.PLAYING
                elif self.state == GameState.GAME_OVER and event.key == pygame.K_SPACE:
                    self.score = 0
                    self.level = 1
                    self.total_coins = 0
                    self.init_level()
                    self.state = GameState.PLAYING
                elif self.state == GameState.LEVEL_COMPLETE and event.key == pygame.K_SPACE:
                    self.level += 1
                    self.init_level()
                    if self.level <= 3:
                        self.state = GameState.PLAYING
                    else:
                        self.state = GameState.GAME_WON
                elif self.state == GameState.GAME_WON and event.key == pygame.K_SPACE:
                    self.score = 0
                    self.level = 1
                    self.total_coins = 0
                    self.init_level()
                    self.state = GameState.MENU
        return True

    def update(self):
        if self.state == GameState.PLAYING:
            keys = pygame.key.get_pressed()
            self.player.handle_input(keys)

            if not self.player.update(self.platforms, self.enemies, self.coins, SCREEN_WIDTH):
                self.state = GameState.GAME_OVER

            for enemy in self.enemies:
                enemy.update()

            for coin in self.coins:
                coin.update()

            # Check if all coins collected
            if len(self.coins) == 0 and self.level < 3:
                self.state = GameState.LEVEL_COMPLETE

            # Boss fight logic
            if self.boss:
                self.boss.update()

                # Check if boss projectiles hit player
                for proj in self.boss.projectiles:
                    if self.player.rect.colliderect(proj.rect):
                        if self.player.invulnerable <= 0:
                            self.player.health -= 1
                            self.player.invulnerable = 120
                            proj.kill()

                # Check if player hits boss
                if self.player.rect.colliderect(self.boss.rect):
                    if self.player.vel.y > 0:  # Jumping on boss
                        self.boss.take_damage()
                        self.player.vel.y = JUMP_STRENGTH
                        self.score += 100

                if self.boss.health <= 0:
                    self.state = GameState.LEVEL_COMPLETE

            # Score for coins
            self.score += len(self.coins) // 10

            if self.player.health <= 0:
                self.state = GameState.GAME_OVER

    def draw(self):
        self.screen.fill(SKY_BLUE)

        if self.state == GameState.MENU:
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

    def draw_menu(self):
        # Background pattern
        for i in range(0, SCREEN_WIDTH, 100):
            for j in range(0, SCREEN_HEIGHT, 100):
                pygame.draw.rect(self.screen, SAFFRON if (i + j) % 200 == 0 else DEEP_BLUE,
                               (i, j, 50, 50), 2)

        title = self.font_large.render("🏛️ TEMPLE QUEST 🏛️", True, SAFFRON)
        subtitle = self.font_medium.render("Indian Mario Adventure", True, DEEP_BLUE)
        start_text = self.font_medium.render("Press SPACE to Start", True, EMERALD)

        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 80))
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, 160))
        start_rect = start_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 150))

        self.screen.blit(title, title_rect)
        self.screen.blit(subtitle, subtitle_rect)
        self.screen.blit(start_text, start_rect)

        # Draw decorative elements
        pygame.draw.circle(self.screen, GOLD, (100, 100), 30)
        pygame.draw.circle(self.screen, GOLD, (SCREEN_WIDTH - 100, 100), 30)
        pygame.draw.circle(self.screen, GOLD, (100, SCREEN_HEIGHT - 100), 30)
        pygame.draw.circle(self.screen, GOLD, (SCREEN_WIDTH - 100, SCREEN_HEIGHT - 100), 30)

    def draw_game(self):
        # Draw platforms
        for platform in self.platforms:
            platform.draw(self.screen)

        # Draw enemies
        for enemy in self.enemies:
            enemy.draw(self.screen)

        # Draw coins
        for coin in self.coins:
            coin.draw(self.screen)

        # Draw player
        self.player.draw(self.screen)

        # Draw boss if exists
        if self.boss:
            self.boss.draw(self.screen)
            # Draw boss health
            health_text = self.font_small.render(f"Boss Health: {self.boss.health}", True, DARK_RED)
            self.screen.blit(health_text, (SCREEN_WIDTH // 2 - 80, 20))

        # Draw HUD
        level_text = self.font_medium.render(f"Level {self.level}", True, DEEP_BLUE)
        score_text = self.font_medium.render(f"Score: {self.score}", True, DEEP_BLUE)
        coins_text = self.font_medium.render(f"Coins: {self.total_coins - len(self.coins)}/{self.total_coins}", True, GOLD)
        health_text = self.font_medium.render(f"❤️ {self.player.health}", True, DARK_RED)

        self.screen.blit(level_text, (20, 20))
        self.screen.blit(score_text, (20, 60))
        self.screen.blit(coins_text, (SCREEN_WIDTH - 250, 20))
        self.screen.blit(health_text, (SCREEN_WIDTH - 250, 60))

    def draw_level_complete(self):
        text = self.font_large.render("🎉 LEVEL COMPLETE! 🎉", True, SAFFRON)
        next_text = self.font_medium.render("Press SPACE for Next Level", True, EMERALD)
        score_text = self.font_medium.render(f"Score: {self.score}", True, DEEP_BLUE)

        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, 150))
        next_rect = next_text.get_rect(center=(SCREEN_WIDTH // 2, 300))
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, 400))

        self.screen.blit(text, text_rect)
        self.screen.blit(next_text, next_rect)
        self.screen.blit(score_text, score_rect)

    def draw_game_over(self):
        text = self.font_large.render("GAME OVER", True, DARK_RED)
        retry_text = self.font_medium.render("Press SPACE to Restart", True, EMERALD)
        score_text = self.font_medium.render(f"Final Score: {self.score}", True, DEEP_BLUE)

        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, 150))
        retry_rect = retry_text.get_rect(center=(SCREEN_WIDTH // 2, 300))
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, 400))

        self.screen.blit(text, text_rect)
        self.screen.blit(retry_text, retry_rect)
        self.screen.blit(score_text, score_rect)

    def draw_game_won(self):
        text = self.font_large.render("🏆 YOU WON! 🏆", True, GOLD)
        msg_text = self.font_medium.render("You Have Conquered All Temples!", True, SAFFRON)
        menu_text = self.font_medium.render("Press SPACE to Return to Menu", True, EMERALD)
        score_text = self.font_medium.render(f"Final Score: {self.score}", True, DEEP_BLUE)

        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, 100))
        msg_rect = msg_text.get_rect(center=(SCREEN_WIDTH // 2, 200))
        menu_rect = menu_text.get_rect(center=(SCREEN_WIDTH // 2, 350))
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, 450))

        self.screen.blit(text, text_rect)
        self.screen.blit(msg_text, msg_rect)
        self.screen.blit(menu_text, menu_rect)
        self.screen.blit(score_text, score_rect)

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
