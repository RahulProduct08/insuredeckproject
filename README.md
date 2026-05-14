# 🏛️ Temple Quest - Indian Mario Adventure

A full-featured Mario-style platformer game with authentic Indian temple and palace aesthetics, featuring difficulty levels, power-ups, boss fights, and 8 unique levels.

## 🎮 Features

### ✨ Core Gameplay
- **8 Challenging Levels** with progressively complex layouts
- **Boss Battle** - Defeat the Temple Guardian on the final level
- **Platforming** - Jump and navigate across ancient temple platforms
- **Enemies** - Avoid patrolling temple demons
- **Coin Collection** - Collect all coins (₹) to complete levels
- **3-Level Health System** - Lose health when hit by enemies

### 🎯 Difficulty Modes
- **EASY**: Slower enemies, fewer obstacles
- **NORMAL**: Balanced challenge (default)
- **HARD**: Fast enemies, more adversaries, tougher boss

### ⭐ Power-ups System
Four unique power-ups scattered throughout levels:

1. **🛡️ Shield** - Absorbs one hit, then breaks (protects once)
2. **⚡ Speed Boost** - Run 1.5x faster for 5 seconds
3. **🔆 Double Jump** - Jump twice in mid-air for 5 seconds
4. **✨ Invincible** - Temporary invulnerability for 5 seconds

### 🏛️ Indian-Themed Design
- **Color Palette**: Saffron, Deep Blue, Emerald Green, Gold
- **Architecture**: Ancient temples, palaces, marble platforms
- **Enemies**: Red temple demons with golden eyes
- **UI**: Indian cultural elements, rupee symbols (₹)
- **Scoring**: Earn points by collecting coins and defeating enemies

### 📊 Level Progression

| Level | Name | Description |
|-------|------|-------------|
| 1 | Temple Gardens | Learn mechanics, 2 enemies, simple platforming |
| 2 | Temple Steps | Staircase pattern, 5 enemies |
| 3 | Sacred Hall | Complex layout, 5 enemies |
| 4 | Spice Market | Varied platforms, enemies spawn randomly |
| 5 | Mountain Path | Zigzag platforms, many enemies |
| 6 | Golden Palace | Large complex layout, many enemies |
| 7 | Ancient Temple | Circular puzzle pattern, multiple power-ups |
| 8 | Final Guardian | Epic boss battle with projectile attacks |

## 🎮 Controls

| Key | Action |
|-----|--------|
| **← / A** | Move Left |
| **→ / D** | Move Right |
| **SPACE / ↑ / W** | Jump |
| **1** | Easy Difficulty (from menu) |
| **2** | Normal Difficulty (from menu) |
| **3** | Hard Difficulty (from menu) |

## 🚀 Installation & Setup

### Requirements
- Python 3.7+
- Pygame 2.1.0+

### Installation Steps

```bash
# Navigate to the game directory
cd "path/to/Test Claude"

# Install dependencies
pip install -r requirements.txt

# Run the game
python mario_india_game_enhanced.py
```

## 🎯 How to Play

### Starting the Game
1. Run the script
2. Select difficulty (1=Easy, 2=Normal, 3=Hard)
3. Press SPACE to start

### Gameplay
- **Collect Coins**: Find all coins on each level to complete it
- **Avoid Enemies**: Contact with enemies costs health
- **Use Power-ups**: Walk over power-ups to gain temporary abilities
- **Defeat Boss**: On Level 8, jump on the boss multiple times to defeat it
- **Progress**: Complete all 8 levels to win!

### Tips & Tricks
- Power-ups stack! You can have multiple active effects
- The Shield power-up is great for risky sections
- Double Jump helps you reach higher platforms
- Speed Boost is useful for escaping enemies
- Boss fights: Jump on the boss when it's at ground level for damage

## 📈 Scoring System

- **Level Completion**: Bonus points per level
- **Coins Collected**: Points for collecting currency (₹)
- **Enemy Evasion**: Score increases over time while playing
- **Boss Defeats**: Major points for hitting the boss
- **Difficulty Bonus**: Harder difficulties give more points

## 🎨 Visual Elements

### UI Indicators (Top of Screen)
- **Level Counter**: Shows current level and total levels
- **Score**: Total accumulated score
- **Coins**: Coins collected / Total coins on level
- **Health**: Heart icons showing remaining health
- **Power-up Status**: Shows active power-ups

### Visual Effects
- **Blinking**: When invulnerable, player blinks
- **Auras**: Glowing rings show active power-up effects
- **Animations**: Coins and power-ups bob and rotate
- **Boss Health Bar**: Visual bar showing boss health

## 🔊 Audio Features

The game includes:
- **Jump Sound**: Simple beep when jumping
- **Coin Pickup**: Cheerful beep when collecting coins
- **Hit Sound**: Lower tone when taking damage
- **Boss Hit**: Deep sound when damaging the boss
- **Power-up Pickup**: Ascending tone for power-ups
- **Level Complete**: Victory fanfare tone

*Sound can be toggled through the SoundManager class*

## 📁 File Structure

```
mario_india_game_enhanced.py  # Main enhanced game file
mario_india_game.py           # Original version
requirements.txt              # Python dependencies
README.md                      # This file
```

## 🎨 Customization

### Modify Colors
Edit the color constants at the top:
```python
SAFFRON = (255, 140, 0)      # Main color
DEEP_BLUE = (25, 25, 112)    # Secondary
EMERALD = (50, 205, 50)      # Platforms
```

### Add More Levels
Create a new `create_level_X()` method in the Game class:
```python
def create_level_X(self):
    # Add platforms
    # Add enemies
    # Add coins
    # Add power-ups
```

### Adjust Difficulty
Modify the difficulty adjustment in enemy creation:
```python
enemy_speed = X if self.difficulty == Difficulty.EASY else Y
```

## 🐛 Troubleshooting

### Game doesn't start
- Ensure pygame is installed: `pip install pygame`
- Check Python version is 3.7+

### Sound issues
- Sound generation may fail on some systems
- Game continues playing without sound if this happens
- You can disable sound by setting `self.enabled = False` in SoundManager

### Performance issues
- Reduce FPS in constants if needed
- Close other applications
- Update your graphics drivers

## 🎓 Learning Resources

This game demonstrates:
- Object-oriented programming with Python
- Sprite management and collision detection
- Game state management
- User input handling
- Drawing and animation
- Sound synthesis with pygame

## 📝 Future Enhancements

- Custom level editor
- Multiplayer mode
- Leaderboard system
- More power-up types
- Animated sprites
- Background music
- Level themes
- Tutorial levels

## 📄 License

This is an educational project. Free to use and modify.

## 🙏 Credits

Created with ❤️ for Indian gaming enthusiasts. Inspired by classic platformers but with authentic Indian cultural elements.

---

**Enjoy conquering the temples! 🏛️✨**
