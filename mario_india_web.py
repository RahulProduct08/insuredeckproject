"""
Temple Quest - Indian Mario Adventure - Web Version
Flask server to run the web-based game locally
"""

from flask import Flask, render_template, jsonify
import os

app = Flask(__name__,
            template_folder='templates',
            static_folder='static',
            static_url_path='/static')

# Configuration
app.config['JSON_SORT_KEYS'] = False

@app.route('/')
def index():
    """Serve the main game page"""
    return render_template('index.html')

@app.route('/api/game-info')
def game_info():
    """Return game information"""
    return jsonify({
        'title': 'Temple Quest - Indian Mario Adventure',
        'version': '2.0 - Web Edition',
        'author': 'Claude Code',
        'description': 'A platformer game with Indian temple/palace theme'
    })

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return render_template('index.html'), 200

if __name__ == '__main__':
    print("=" * 60)
    print("🏛️  TEMPLE QUEST - Web Version 🏛️")
    print("=" * 60)
    print("\n✅ Server starting...")
    print("\n🌐 Open your browser and go to:")
    print("   👉 http://localhost:5000")
    print("   or")
    print("   👉 http://127.0.0.1:5000")
    print("\n📝 Press CTRL+C to stop the server")
    print("=" * 60 + "\n")

    app.run(debug=True, host='localhost', port=5000, use_reloader=False)
