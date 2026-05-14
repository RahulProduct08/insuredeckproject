# 🎨 Customization Guide - Temple Quest

Easily modify the game without touching the complex code!

## Color Customization

Edit these colors in `mario_india_game_enhanced.py` (around line 25-33):

```python
# Indian Traditional Colors
SAFFRON = (255, 140, 0)      # Orange - Main player color
DEEP_BLUE = (25, 25, 112)    # Blue - Text and UI
EMERALD = (50, 205, 50)      # Green - Platforms
GOLD = (255, 215, 0)         # Golden - Coins and decorations
DARK_RED = (139, 0, 0)       # Red - Enemies and boss
SKY_BLUE = (135, 206, 250)   # Blue - Background
```

### Popular Color Palettes

**Modern India:**
```python
SAFFRON = (255, 102, 0)
DEEP_BLUE = (0, 51, 102)
EMERALD = (0, 153, 76)
GOLD = (255, 184, 28)
DARK_RED = (192, 0, 0)
```

**Mystic Temple:**
```python
SAFFRON = (230, 126, 34)
DEEP_BLUE = (44, 62, 80)
EMERALD = (39, 174, 96)
GOLD = (241, 196, 15)
DARK_RED = (127, 140, 141)
```

**Festive Diwali:**
```python
SAFFRON = (255, 165, 0)
DEEP_BLUE = (30, 30, 100)
EMERALD = (72, 209, 204)
GOLD = (255, 223, 0)
DARK_RED = (220, 20, 60)
```

## Game Mechanics Customization

### Player Speed
Find line ~200 in `Player.__init__()`:
```python
self.base_speed = 6  # Change this value
# Higher = faster (try 5-8)
```

### Jump Height
Find line ~235 in `Player.handle_input()`:
```python
self.vel.y = JUMP_STRENGTH  # Currently -15
# JUMP_STRENGTH = -15 at top of file
# More negative = higher jump (try -10 to -20)
```

### Gravity
Find line ~26:
```python
GRAVITY = 0.5  # Change this
# Higher = faster falling (try 0.3-0.8)
```

### Health
Find line ~204:
```python
self.max_health = 3  # Change initial health
# Can be 1-9 hearts
```

## Enemy Customization

### Patrol Distance
Find enemy spawning in each level (e.g., line ~450):
```python
Enemy(x, y, patrol_range=80)  # Second parameter
# Higher = roams wider area
```

### Enemy Speed
In level creation methods:
```python
self.enemies.add(Enemy(x, y, patrol, enemy_speed))
# enemy_speed is adjustable (2-8 recommended)
```

### Number of Enemies
Modify the list sizes:
```python
enemy_data = [  # Add or remove entries
    (300, 450, 100),
    (600, 450, 100),
]
```

## Platform Customization

### Platform Width/Height
Find platform creation:
```python
Platform(x, y, width, height, color)
# Customize width and height for each platform
```

### Add Spikes
Change the last parameter to True:
```python
Platform(x, y, width, height, EMERALD, is_spike=True)
# Creates spiked hazard platforms
```

## Coin Customization

### Coin Values/Points
Coins are worth automatic points. Modify in `draw_game()`:
```python
coins_text = self.font_medium.render(f"₹ {self.total_coins - len(self.coins)}/{self.total_coins}", True, GOLD)
# Change the symbol or format
```

### Number of Coins
Modify lists like:
```python
coin_positions = [
    (100, 200),
    (200, 300),
    # Add or remove positions
]
```

## Power-up Customization

### Change Power-up Types
In level creation:
```python
self.power_ups.add(PowerUp(x, y, PowerUpType.SHIELD))
# Options: SHIELD, SPEED_BOOST, DOUBLE_JUMP, INVINCIBLE
```

### Adjust Power-up Duration
Find in `Player.update()`:
```python
if self.speed_boost_time > 0:  # Currently 300 frames
# 300 frames = 5 seconds (at 60 FPS)
# Change: 600 = 10 seconds, 150 = 2.5 seconds
```

## Boss Customization

### Boss Health
Find boss creation in `create_boss_level()`:
```python
self.boss = Boss(x, y, self.difficulty)
# Change health in Boss.__init__() line ~320
self.health = int(5 * health_multiplier)  # 5 = base health
```

### Boss Speed
```python
self.vel_x = -4  # Speed of movement (higher = faster)
```

### Attack Interval
```python
attack_interval = 80  # Frames between shots
# Lower = shoots more often
# 60 FPS, so 60 = 1 second between shots
```

## Difficulty Adjustments

### Make Easy Mode Easier
Find difficulty adjustments:
```python
# In Boss.__init__()
if difficulty == Difficulty.EASY:
    self.health = 3  # Reduce from 5
    enemy_speed = 1.5  # Reduce from 2
```

### Make Hard Mode Harder
```python
# In Boss.__init__()
if difficulty == Difficulty.HARD:
    self.health = 7  # Increase from 5
    enemy_speed = 8  # Increase from 6
```

## Level Customization

### Add New Level
Copy a level creation method:
```python
def create_level_9(self):
    # Copy from create_level_1() and modify
    ground = Platform(0, SCREEN_HEIGHT - 50, SCREEN_WIDTH, 50, EMERALD)
    self.platforms.add(ground)
    
    # Add platforms
    # Add enemies
    # Add coins
    # Add power-ups
```

Then update:
1. `init_level()` to call `create_level_9()`
2. `self.levels_count = 9` (around line ~370)

### Randomize Level Layouts
In level methods, use:
```python
x = random.randint(100, 900)
y = random.randint(200, 500)
self.platforms.add(Platform(x, y, 120, 20, EMERALD))
```

## UI Customization

### Font Sizes
Find font definitions:
```python
self.font_large = pygame.font.Font(None, 56)   # Headings
self.font_medium = pygame.font.Font(None, 36)  # Normal text
self.font_small = pygame.font.Font(None, 24)   # Small text
# Change numbers for size (higher = bigger)
```

### Screen Resolution
Find at top:
```python
SCREEN_WIDTH = 1200   # Game width in pixels
SCREEN_HEIGHT = 700   # Game height in pixels
# Higher = bigger window
```

### FPS (Smoothness)
```python
FPS = 60  # Frames per second
# 60 = smooth, 30 = slower but smoother on weak PCs
```

## Sound Customization

### Disable Sound
In `Game.__init__()`:
```python
# After creating player, add:
self.player.sound_manager.enabled = False
```

### Change Sound Frequencies
In `SoundManager` class:
```python
def play_jump(self):
    self.generate_beep(440, 100)  # 440 Hz, 100ms
    # First number = pitch (higher = higher sound)
    # Second number = duration in milliseconds
```

### Sound Frequency Guide
```
Low:   220 Hz (deep)
Mid:   440 Hz (normal)  
High:  880 Hz (high pitch)
Very High: 1200 Hz
```

## Text Customization

### Change Game Title
Find:
```python
pygame.display.set_caption("🏛️ Temple Quest - Indian Mario Adventure 🏛️")
# Change this text
```

### Change Level Names
Find `draw_level_complete()`:
```python
level_name = [
    "Temple Gardens",
    "Temple Steps",
    # Add your own names
]
```

## Advanced Customizations

### Add Health Pickups
In power-ups list, add:
```python
class HealthPickup(pygame.sprite.Sprite):
    # Create new class
    # Add to power_ups group
    # Handle collision in player.update()
```

### Add Moving Platforms
```python
class MovingPlatform(Platform):
    def update(self):
        # Move platform up/down or side-to-side
        self.rect.y += self.vel_y
```

### Add Secret Areas
Create hidden coin sections:
```python
if keys[pygame.K_DOWN]:  # Hidden mechanic
    # Access secret platform
```

## Testing Your Changes

After editing:
```bash
python mario_india_game_enhanced.py
```

If it crashes:
1. Check for syntax errors (look at error message)
2. Verify parentheses and indentation
3. Look for unclosed quotes or brackets

## Backup Original

Before heavy customization:
```bash
cp mario_india_game_enhanced.py mario_india_game_enhanced_backup.py
```

## Popular Mod Ideas

1. **Endless Mode**: Remove level limit, keep spawning enemies
2. **Speedrun Mode**: Timer on screen, leaderboard scores
3. **Inverted Gravity**: Falling up instead of down
4. **Night Mode**: Dark colors, glowing enemies
5. **Time Limit**: Complete levels before time runs out
6. **Collectibles**: Different coin types worth different points
7. **Story Mode**: Text between levels
8. **Tutorial Level**: Level 0 teaching mechanics

## Getting Help

If something breaks:
1. Look at the error message
2. Check line number mentioned
3. Compare with original file
4. Reset from backup

Good luck customizing! 🎨✨
