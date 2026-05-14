# 🏃 Quick Start Guide - Temple Quest

## One-Minute Setup

```bash
# 1. Install pygame
pip install pygame

# 2. Run the game
python mario_india_game_enhanced.py

# 3. Select difficulty (press 1, 2, or 3)
```

That's it! 🎮

## Game Basics (30 seconds)

| What | How |
|------|-----|
| **Move** | ← → (Arrow keys or A/D) |
| **Jump** | SPACE (or ↑ or W) |
| **Goal** | Collect all coins ₹ to complete level |
| **Health** | 3 hearts ❤️ (touch enemies = -1 health) |
| **Power-ups** | Walk over them for special abilities |

## Power-ups At A Glance

```
🛡️ Shield    → Blocks 1 hit (absorbs damage)
⚡ Speed     → Run faster for 5 seconds  
🔆 2-Jump    → Jump twice in mid-air
✨ Invincible → Can't take damage for 5 seconds
```

## Level Overview

```
Level 1  → 2 enemies, easy platforming
Level 2  → 5 enemies, stepping pattern
Level 3  → 5 enemies, complex layout
Level 4  → Random enemies, varied platforms
Level 5  → Zigzag platforms, many enemies
Level 6  → Complex palace, 8+ enemies
Level 7  → Circular puzzle, lots of coins
Level 8  → FINAL BOSS - Jump on it 5 times to win
```

## Difficulty Differences

```
EASY     → Slower enemies, fewer of them
NORMAL   → Balanced (default experience)
HARD     → Fast enemies, more spawns, harder boss
```

## Pro Tips 🎯

1. **Collect coins first** → Complete the level
2. **Save power-ups for hard sections** → Use strategically
3. **Use Double Jump** → Reach high places easily
4. **Speed Boost to escape** → Run away from enemies
5. **Shield for risky areas** → Protection against hits
6. **Boss fight** → Wait for it at ground level, then jump on it

## Score Breakdown

```
Collecting coins        → Points
Completing levels       → Bonus points
Time spent playing      → Continuous points
Defeating boss          → Major points
Harder difficulty       → More points overall
```

## Common Issues & Fixes

| Problem | Solution |
|---------|----------|
| No sound | Game still works - sound generation may fail |
| Game slow | Close other apps, reduce screen resolution |
| Can't jump | Make sure you're on a platform |
| Falling forever | You died! Game over (3 hit limit) |
| Can't find coins | Check all platforms, use double jump |

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| **1** | Select Easy difficulty |
| **2** | Select Normal difficulty |
| **3** | Select Hard difficulty |
| **SPACE** | Jump / Confirm on menus |
| **ESC** | Close game (standard exit) |

## First Playthrough Tips

1. Start on **NORMAL** difficulty
2. In Level 1, practice **jumping** between platforms
3. Learn when to **collect power-ups** vs. avoid danger
4. Reach Level 2 to experience **more complex platforming**
5. By Level 5+, you'll have **solid skills**
6. Level 8 boss is **beatable** if you dodge and jump on it

## Speedrun Suggestions

- **Fastest Route**: Skip power-ups, rush directly to coins
- **Safest Route**: Collect all power-ups first, then coins
- **Score Route**: Get everything, defeat boss, take time

## Game States

```
1. Difficulty Select    ← Choose 1, 2, or 3
2. Menu                 ← Press SPACE to start
3. Playing              ← Collect coins, avoid enemies
4. Level Complete       ← Next level (press SPACE)
5. Game Over            ← Died (3 health limit)
6. Final Boss           ← Level 8 special fight
7. Game Won             ← Completed all 8 levels!
```

## Controls Quick Reference

```
┌─────────────────────────────────┐
│  ↑     JUMP                     │
│  │   (Space/Up/W)              │
├─────────────────────────────────┤
│ ← MOVE LEFT          MOVE RIGHT → │
│ (A/Left Arrow)      (D/Right Arrow) │
└─────────────────────────────────┘
```

## Scoring Tips

- **Coin collecting** = Main points
- **Time survival** = Passive points
- **Enemy avoiding** = No penalty
- **Boss defeat** = Bonus points
- **Difficulty multiplier** = Hard gives ~2x points

## Advanced Moves

1. **Dash Jump** → Speed boost + Jump = Far distance
2. **Mid-air dodge** → Double jump to avoid projectiles
3. **Power-up combo** → Stack invincible + double jump for safety
4. **Boss kiting** → Stay far, dodge projectiles, jump when ready

## Files You'll See

```
mario_india_game_enhanced.py  ← RUN THIS (main game)
mario_india_game.py           ← Original version
requirements.txt              ← Dependencies
README.md                      ← Full documentation
QUICKSTART.md                  ← This file
```

## Play Again? 🔄

After completing or losing:
- Press **SPACE** to restart
- Choose difficulty again
- New level layout (some randomization in levels 4-7)

---

**Ready to conquer? Run the game and press 1-3 to choose difficulty!** 🏛️✨
