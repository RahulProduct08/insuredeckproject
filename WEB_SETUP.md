# 🌐 Temple Quest Web Version - Setup Guide

## Overview

You now have **TWO versions** of Temple Quest:

### 🎮 Version 1: Desktop (Pygame)
- Runs as a standalone application
- More features and optimization
- Run: `python mario_india_game_enhanced.py`

### 🌐 Version 2: Web Browser (Flask + HTML5 Canvas)
- Play in any modern web browser
- Access via localhost
- Run: `python mario_india_web.py`

---

## 🚀 Quick Start - Web Version

### Step 1: Install Dependencies

```bash
# Navigate to the game folder
cd "path/to/Test Claude"

# Install Flask and Pygame
pip install -r requirements.txt
```

### Step 2: Run the Web Server

```bash
python mario_india_web.py
```

You'll see:
```
============================================================
🏛️  TEMPLE QUEST - Web Version 🏛️
============================================================

✅ Server starting...

🌐 Open your browser and go to:
   👉 http://localhost:5000
   or
   👉 http://127.0.0.1:5000

📝 Press CTRL+C to stop the server
============================================================
```

### Step 3: Open in Browser

Copy one of these URLs into your browser:
- **http://localhost:5000**
- **http://127.0.0.1:5000**

The game will load instantly! 🎮

---

## 🎮 How to Play (Web Version)

### Controls
| Key | Action |
|-----|--------|
| **← →** or **A D** | Move |
| **SPACE** or **↑ W** | Jump |
| **1, 2, 3** | Select Difficulty |

### Gameplay
1. **Select Difficulty** - Easy, Normal, or Hard
2. **Collect Coins** - Find all coins ₹ to complete level
3. **Avoid Enemies** - Red demons hurt you
4. **Collect Power-ups** - Stars give special abilities
5. **Progress** - Complete 8 levels to win!

### Difficulty Modes
- **1 - EASY** - Slower enemies, easier gameplay
- **2 - NORMAL** - Balanced (recommended)
- **3 - HARD** - Challenging enemies and levels

---

## 📁 File Structure

```
Web Version Files:
├── mario_india_web.py          # Flask server (RUN THIS)
├── templates/
│   └── index.html              # Game HTML page
├── static/
│   ├── game.js                 # Game logic
│   └── style.css               # Styling
├── requirements.txt            # Python dependencies
└── WEB_SETUP.md               # This file
```

---

## ⚙️ Technical Details

### What is Flask?
Flask is a lightweight Python web framework that serves files and handles HTTP requests. In this case, it simply serves your game to your browser.

### Port 5000
The web server runs on port 5000 by default. If port 5000 is busy, you can change it:

```python
# In mario_india_web.py, last line:
app.run(debug=True, host='localhost', port=8000, use_reloader=False)
```

Change `port=5000` to any other number (8000, 3000, etc.)

### Canvas vs Pygame
- **Pygame version**: Uses Python's Pygame library, more features
- **Canvas version**: Uses HTML5 Canvas (JavaScript), pure web tech
- Both have the same gameplay and Indian theme!

---

## 🐛 Troubleshooting

### "Address already in use" Error
The port 5000 is being used by another application.

**Solution:**
1. Change the port in `mario_india_web.py` (see above)
2. Or find what's using port 5000 and stop it

### Game doesn't load
1. Make sure Flask is installed: `pip install Flask`
2. Check that you're visiting `http://localhost:5000` (not `https://`)
3. Check the terminal for error messages

### Game is slow
1. Close other browser tabs
2. Try a different browser (Chrome usually fastest)
3. Reduce screen resolution if needed

### Controls not working
1. Click on the game canvas first to focus it
2. Make sure you're using the correct keys (← → for movement)
3. Keyboard layout: Try WASD if arrow keys don't work

### Can't see the game
1. Make sure the server is running (terminal shows "Running on...")
2. Refresh the page (F5 or Ctrl+R)
3. Clear browser cache (Ctrl+Shift+Delete)

---

## 🔧 Customization

### Change Port
Edit `mario_india_web.py`:
```python
app.run(debug=True, host='localhost', port=8000, use_reloader=False)
```

### Change Colors
Edit `static/game.js`, find `COLORS` object:
```javascript
const COLORS = {
    SAFFRON: '#ff8c00',      // Modify hex codes
    DEEP_BLUE: '#191b70',
    // ... etc
};
```

### Change Game Title
Edit `templates/index.html`:
```html
<title>Your Title Here</title>
```

### Make it Public (Advanced)
Change in `mario_india_web.py`:
```python
# Instead of:
app.run(host='localhost', ...)

# Use:
app.run(host='0.0.0.0', ...)
```

Then access from other computers using your IP address (find with `ipconfig`).

---

## 🌐 Accessing from Other Devices

### Same Computer
- http://localhost:5000
- http://127.0.0.1:5000

### Other Computer on Same Network
1. Find your IP: Run `ipconfig` in terminal, look for "IPv4 Address"
2. Example: `192.168.1.100`
3. Other devices use: `http://192.168.1.100:5000`

### From Internet (Advanced)
- Requires port forwarding on your router
- Not recommended for security
- Better to use cloud hosting (Heroku, Replit, etc.)

---

## 📱 Mobile/Tablet

The web version is responsive and works on mobile devices!

1. Find your computer's IP address
2. Open `http://[your-ip]:5000` on your phone/tablet
3. Game adjusts to screen size automatically

**Note:** Mobile controls may be tricky. Consider adding touch/mobile controls:
```javascript
// In game.js, add touch event listeners
document.addEventListener('touchstart', handleTouch);
document.addEventListener('touchmove', handleTouch);
```

---

## 🎯 Comparing Desktop vs Web

| Feature | Desktop | Web |
|---------|---------|-----|
| Performance | Faster | Good |
| Features | All | All core features |
| Access | Local computer only | Any browser |
| Install | Needs Pygame | Just Flask |
| Multiplayer | Not built-in | Could be added |
| Sound | Full sound effects | Beep tones only |

---

## 🚀 Deployment (Advanced)

### Deploy to Heroku (Free)
```bash
# 1. Install Heroku CLI
# 2. Create Procfile:
echo "web: python mario_india_web.py" > Procfile

# 3. Create requirements.txt (already done)
# 4. Deploy
heroku create your-app-name
git push heroku main
```

### Deploy to Replit
1. Upload files to Replit
2. Run `python mario_india_web.py`
3. Click "Open in new tab"
4. Share the link!

### Deploy to PythonAnywhere
1. Upload files
2. Create web app
3. Set path to `mario_india_web.py`
4. Reload
5. Access your public URL

---

## 📝 Common Issues & Fixes

| Issue | Fix |
|-------|-----|
| "ModuleNotFoundError: No module named 'flask'" | `pip install Flask` |
| "Address already in use" | Change port in mario_india_web.py |
| Game won't load | Make sure server is running, refresh page |
| Game is slow | Close other programs, try different browser |
| Can't move player | Click on game canvas to focus it |
| Controls reversed | Check keyboard layout |

---

## ✨ Features Available in Web Version

✅ 8 Levels with unique layouts  
✅ 3 Difficulty modes  
✅ 4 Power-up types  
✅ Enemy AI and patrolling  
✅ Coin collection system  
✅ Boss battle  
✅ Score tracking  
✅ Health system  
✅ Level progression  
✅ Indian temple theme  
✅ Beautiful UI  
✅ Sound effects (beep tones)  

❌ Not in web version (yet):
- 3D graphics
- Advanced shader effects
- Multiplayer
- Save/load system

---

## 🎓 Learning Resources

### Understanding the Code

**Files to explore:**
1. `mario_india_web.py` - Flask server setup
2. `templates/index.html` - HTML structure
3. `static/style.css` - Game styling
4. `static/game.js` - Core game logic

### Web Game Development
- HTML5 Canvas: Good for 2D games
- JavaScript: Game logic runs in browser
- Flask: Python web framework for serving files
- Event listeners: Handle keyboard/mouse input

---

## 🔐 Security Notes

- This is a **local development server**
- Not meant for production use
- No user authentication or data storage
- Safe to run on your own computer

---

## 📞 Support

### Getting Help
1. Check the troubleshooting section above
2. Look at terminal/console error messages
3. Try restarting the server
4. Clear browser cache and reload

### Common Error Messages
- **"OSError: [Errno 10048]"** → Port in use, change port
- **"ModuleNotFoundError"** → Missing dependency, run pip install
- **"Connection refused"** → Server not running, run mario_india_web.py

---

## 🎉 You're All Set!

You now have:
- ✅ Desktop version (mario_india_game_enhanced.py)
- ✅ Web version (mario_india_web.py)
- ✅ Mobile-friendly responsive design
- ✅ 8 levels to complete
- ✅ Full customization options

**Choose your version and start playing!** 🏛️✨

---

## Quick Command Reference

```bash
# Install dependencies
pip install -r requirements.txt

# Run web version
python mario_india_web.py

# Then open browser to:
http://localhost:5000

# Stop server
Ctrl+C (in terminal)

# Check if Flask is installed
pip list | grep Flask

# Update Flask
pip install --upgrade Flask
```

---

**Enjoy Temple Quest! 🏛️🎮✨**
