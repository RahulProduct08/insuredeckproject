# 🏛️ Temple Quest - Indian Mario Adventure

## 🎮 Welcome! Start Here!

You have received a **complete game with BOTH desktop and web versions!**

---

## 📦 What You Got

### **Two Complete Game Versions:**

#### 🖥️ **VERSION 1: Desktop Game (Pygame)**
- **File:** `mario_india_game_enhanced.py`
- **How to run:** `python mario_india_game_enhanced.py`
- **Platform:** Standalone Windows/Mac/Linux app
- **Best for:** Smooth gameplay, all features
- **Setup guide:** See `README.md`

#### 🌐 **VERSION 2: Web Game (Browser)**
- **File:** `mario_india_web.py`
- **How to run:** `python mario_india_web.py`
- **Platform:** Any modern web browser
- **Best for:** Easy sharing, no installation
- **Access:** http://localhost:5000
- **Setup guide:** See `WEB_SETUP.md`

---

## ⚡ Quick Start (Choose One)

### Option A: Play in Browser (Easiest) 🌐

```bash
# 1. Install Flask
pip install Flask

# 2. Run web server
python mario_india_web.py

# 3. Open browser to:
http://localhost:5000
```

**That's it! Game loads in your browser instantly.** ✨

### Option B: Play Desktop App (Classic) 🖥️

```bash
# 1. Install Pygame
pip install pygame

# 2. Run the game
python mario_india_game_enhanced.py

# 3. Game window opens on your desktop
```

---

## 📂 Complete File List

```
Your Game Folder Contains:
├── Desktop Versions:
│   ├── mario_india_game_enhanced.py     ← Better desktop version (8 levels!)
│   └── mario_india_game.py              ← Original desktop version
│
├── Web Version:
│   ├── mario_india_web.py               ← Web server (RUN THIS)
│   ├── templates/
│   │   └── index.html                   ← Game page
│   └── static/
│       ├── game.js                      ← Game logic
│       └── style.css                    ← Styling
│
├── Documentation:
│   ├── START_HERE.md                    ← This file 👈
│   ├── README.md                        ← Full documentation
│   ├── QUICKSTART.md                    ← Quick reference
│   ├── CUSTOMIZE.md                     ← How to modify game
│   └── WEB_SETUP.md                     ← Web version details
│
└── Dependencies:
    └── requirements.txt                 ← Python packages needed
```

---

## 🎮 Game Features

### 8 Levels
1. **Temple Gardens** - Learn the basics
2. **Temple Steps** - Staircase challenge
3. **Sacred Hall** - Complex layout
4. **Spice Market** - Varied platforms
5. **Mountain Path** - Zigzag jumps
6. **Golden Palace** - Large and complex
7. **Ancient Temple** - Circular puzzle
8. **Final Guardian** - Epic boss battle

### 3 Difficulty Modes
- **EASY** - Slower enemies, learning mode
- **NORMAL** - Balanced challenge (recommended)
- **HARD** - Speed demons and chaos!

### 4 Power-ups
- 🛡️ **Shield** - Block one hit
- ⚡ **Speed Boost** - Run faster
- 🔆 **Double Jump** - Jump in mid-air
- ✨ **Invincible** - Can't take damage

### 8 Levels + Boss Fight
- Unique layouts for each level
- Increasing difficulty
- Epic boss battle on final level
- Score tracking system

---

## 🎯 Choose Your Version

### **I want to play RIGHT NOW** 🚀
→ Use **Web Version**
- No installation needed
- Opens in browser instantly
- Works on phone/tablet too
- Read: `WEB_SETUP.md`

### **I want best graphics & performance** 💪
→ Use **Desktop Version**
- Smooth gameplay
- Full features
- Offline play
- Read: `README.md`

### **I want to learn to code** 📚
→ Use **Both!**
- Compare implementations
- Customize the game
- Learn game development
- Read: `CUSTOMIZE.md`

---

## 🚀 Installation (All-in-One)

### Step 1: Install Dependencies (Do This Once)

```bash
# Open terminal/command prompt
# Navigate to your game folder:
cd "path/to/Test Claude"

# Install everything needed:
pip install -r requirements.txt
```

This installs:
- Flask (for web version)
- Pygame (for desktop version)

### Step 2a: Run Web Version

```bash
python mario_india_web.py
```

Then open browser: **http://localhost:5000**

### Step 2b: Run Desktop Version

```bash
python mario_india_game_enhanced.py
```

Game window opens on your desktop!

---

## 💻 System Requirements

### Minimum
- **OS:** Windows, Mac, or Linux
- **Python:** 3.7 or higher
- **Browser:** Any modern browser (Chrome, Firefox, Safari, Edge)
- **RAM:** 512 MB
- **Disk:** 50 MB

### Recommended
- **Python:** 3.9+
- **Browser:** Chrome or Firefox (latest)
- **RAM:** 2 GB+
- **Display:** 1200x700 resolution

---

## 📖 Documentation Guide

| Document | Purpose | Read If... |
|----------|---------|-----------|
| **START_HERE.md** | Overview (you are here!) | You're new to the game |
| **README.md** | Full features & guide | You want complete info |
| **QUICKSTART.md** | 30-second cheat sheet | You want to jump in fast |
| **WEB_SETUP.md** | Web version details | You're playing in browser |
| **CUSTOMIZE.md** | How to modify game | You want to change things |

---

## 🎮 Controls

### Keyboard
| Key | Action |
|-----|--------|
| **← / A** | Move left |
| **→ / D** | Move right |
| **SPACE** / **↑** / **W** | Jump |
| **1 / 2 / 3** | Select difficulty |

### Mouse
- Click buttons in menus
- Click game canvas to focus

---

## 🎯 First 5 Minutes

1. ✅ Install dependencies: `pip install -r requirements.txt`
2. ✅ Start web server: `python mario_india_web.py`
3. ✅ Open browser: `http://localhost:5000`
4. ✅ Select difficulty: Press 1, 2, or 3
5. ✅ Play! Collect coins and progress through levels

---

## 🆘 Quick Troubleshooting

### "Command not found: python"
- Install Python from python.org
- Add to PATH if on Windows

### "ModuleNotFoundError: No module named 'flask'"
- Run: `pip install Flask`

### "Address already in use"
- Change port in `mario_india_web.py` (search for 5000)
- Or use a different port

### Game is slow
- Close other programs
- Try different browser
- Check your internet connection (web version)

### Can't move the player
- Click on the game to focus it
- Check keyboard layout

See `WEB_SETUP.md` for more troubleshooting!

---

## 🎓 Learn More

### Game Development
- **Game loop:** Runs 60 times per second
- **Collision detection:** Checks if objects touch
- **State management:** Tracks game progress
- **Sprite system:** Manages characters and objects

### Web Development (Web Version)
- **HTML5 Canvas:** 2D drawing API
- **JavaScript:** Browser-based game logic
- **Flask:** Python web framework
- **Event listeners:** Keyboard/mouse handling

### Desktop Development (Desktop Version)
- **Pygame:** Python game library
- **Sprite groups:** Organize game objects
- **Collision detection:** Advanced physics
- **Drawing:** Optimized graphics

---

## 💡 Tips & Tricks

### General
- **Shield is valuable** - Save it for hard sections
- **Speed boost is escape** - Use to run from enemies
- **Double jump helps** - Reach high platforms easily
- **Invincible is rare** - Save for boss fight!

### Gameplay
- Collect all coins to complete level
- Enemies patrol in areas - learn patterns
- Power-ups spawn in specific locations
- Boss has 5 health hits on Normal difficulty

### Scoring
- More coins = more points
- Longer survival = more points
- Harder difficulty = more multiplier
- Defeat boss = bonus points

---

## 🎉 What's Included

✅ 8 complete levels  
✅ Unique enemy AI  
✅ 4 power-up types  
✅ Boss battle system  
✅ Difficulty selection  
✅ Score tracking  
✅ Health system  
✅ Indian temple theme  
✅ Responsive design  
✅ Sound effects  
✅ Full documentation  
✅ Customization guide  
✅ Both desktop & web versions  

---

## 🚀 Next Steps

### Play Now
1. Run: `python mario_india_web.py`
2. Open: http://localhost:5000
3. Enjoy! 🎮

### Want to Customize?
- Read: `CUSTOMIZE.md`
- Modify colors, difficulty, levels
- Add new features

### Want Full Details?
- Read: `README.md`
- Complete game documentation
- All features explained

### Want Quick Reference?
- Read: `QUICKSTART.md`
- Controls and tips
- Fast cheat sheet

---

## 📞 Support

### Having Issues?
1. Check `WEB_SETUP.md` for web issues
2. Check `README.md` for desktop issues
3. Check terminal/console for error messages
4. Try reinstalling: `pip install -r requirements.txt`

### Want to Report a Bug?
- Check if issue is in documentation
- Test both versions
- Note the error message
- Note your OS and Python version

---

## 🎊 You're All Set!

You now have a **complete, fully-featured platformer game** with:
- ✨ Beautiful Indian temple theme
- 🎮 Smooth gameplay mechanics
- 🌐 Web and desktop versions
- 📱 Mobile-responsive design
- 📚 Complete documentation

**Choose your version and start playing!**

---

## 🏃 TL;DR (Super Quick)

```bash
pip install -r requirements.txt
python mario_india_web.py
# Then open: http://localhost:5000
```

**Done! Start playing!** 🏛️✨

---

**Made with ❤️ for Indian gaming!**

🏛️ Temple Quest - Indian Mario Adventure 🏛️
