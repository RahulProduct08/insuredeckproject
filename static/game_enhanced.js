/**
 * Temple Quest - Enhanced Edition
 * Beautiful Graphics, Music, & Better Gameplay
 */

// Constants
const SCREEN_WIDTH = 1200;
const SCREEN_HEIGHT = 700;
const GRAVITY = 0.6;
const JUMP_STRENGTH = -12;

// Colors (Indian themed)
const COLORS = {
    SAFFRON: '#ff8c00',
    DEEP_BLUE: '#191b70',
    EMERALD: '#32cd32',
    GOLD: '#ffd700',
    DARK_RED: '#8b0000',
    SKY_BLUE: '#87ceeb',
    CREAM: '#f5f5dc',
    PURPLE: '#800080',
    LIGHT_GREEN: '#90ee90',
    ORANGE: '#ff6b35',
    LIGHT_BLUE: '#4ecdc4'
};

// Game States
const GAME_STATE = {
    DIFFICULTY_SELECT: 'difficulty_select',
    MENU: 'menu',
    PLAYING: 'playing',
    LEVEL_COMPLETE: 'level_complete',
    GAME_OVER: 'game_over',
    GAME_WON: 'game_won'
};

const DIFFICULTY = {
    EASY: 'easy',
    NORMAL: 'normal',
    HARD: 'hard'
};

const POWER_UP_TYPE = {
    SHIELD: 'shield',
    SPEED_BOOST: 'speed_boost',
    DOUBLE_JUMP: 'double_jump',
    INVINCIBLE: 'invincible'
};

// Game variables
let canvas, ctx;
let gameState = GAME_STATE.DIFFICULTY_SELECT;
let difficulty = DIFFICULTY.NORMAL;
let score = 0;
let level = 1;
let totalCoins = 0;
const MAX_LEVELS = 8;
let frameCount = 0;

// Game objects
let player, platforms, enemies, coins, powerUps, boss;
let particles = [];
let keys = {};

// Audio system
const audioContext = new (window.AudioContext || window.webkitAudioContext)();
let isMusicPlaying = false;

// Sound effects
const sounds = {
    jump: () => playSound(400, 100, 0.1),
    coin: () => playSound(800, 150, 0.1),
    hit: () => playSound(200, 200, 0.1),
    levelUp: () => playSound(600, 300, 0.15),
    powerUp: () => playSound(1000, 250, 0.15),
    bosshit: () => playSound(150, 300, 0.15)
};

function playSound(frequency, duration, volume) {
    try {
        const now = audioContext.currentTime;
        const osc = audioContext.createOscillator();
        const gain = audioContext.createGain();

        osc.connect(gain);
        gain.connect(audioContext.destination);

        osc.frequency.value = frequency;
        gain.gain.setValueAtTime(volume, now);
        gain.gain.exponentialRampToValueAtTime(0.01, now + duration / 1000);

        osc.start(now);
        osc.stop(now + duration / 1000);
    } catch (e) {}
}

function playBackgroundMusic() {
    if (isMusicPlaying) return;
    isMusicPlaying = true;

    // Simple melody pattern
    const notes = [
        { freq: 523.25, dur: 500 },  // C5
        { freq: 587.33, dur: 500 },  // D5
        { freq: 659.25, dur: 500 },  // E5
        { freq: 523.25, dur: 500 },  // C5
        { freq: 587.33, dur: 500 },  // D5
        { freq: 659.25, dur: 500 },  // E5
        { freq: 783.99, dur: 800 },  // G5
        { freq: 659.25, dur: 800 }   // E5
    ];

    function playMelody(index) {
        if (!isMusicPlaying || gameState !== GAME_STATE.PLAYING) return;

        const note = notes[index % notes.length];
        const now = audioContext.currentTime;

        try {
            const osc = audioContext.createOscillator();
            const gain = audioContext.createGain();

            osc.connect(gain);
            gain.connect(audioContext.destination);

            osc.type = 'sine';
            osc.frequency.value = note.freq;
            gain.gain.setValueAtTime(0.05, now);
            gain.gain.exponentialRampToValueAtTime(0.01, now + note.dur / 1000);

            osc.start(now);
            osc.stop(now + note.dur / 1000);

            setTimeout(() => playMelody(index + 1), note.dur);
        } catch (e) {}
    }

    playMelody(0);
}

// Initialize game
function init() {
    canvas = document.getElementById('gameCanvas');
    ctx = canvas.getContext('2d');

    canvas.width = SCREEN_WIDTH;
    canvas.height = SCREEN_HEIGHT;

    document.addEventListener('keydown', handleKeyDown);
    document.addEventListener('keyup', handleKeyUp);

    document.querySelectorAll('.difficulty-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            difficulty = e.target.dataset.difficulty;
            startGame();
        });
    });

    document.getElementById('game-over-modal').addEventListener('click', restartGame);
    document.getElementById('level-complete-modal').addEventListener('click', nextLevel);
    document.getElementById('game-won-modal').addEventListener('click', restartGame);

    gameState = GAME_STATE.DIFFICULTY_SELECT;
    showModal('menu-modal');

    gameLoop();
}

function handleKeyDown(e) {
    keys[e.key] = true;

    if (gameState === GAME_STATE.DIFFICULTY_SELECT) {
        if (e.key === '1') {
            difficulty = DIFFICULTY.EASY;
            startGame();
        } else if (e.key === '2') {
            difficulty = DIFFICULTY.NORMAL;
            startGame();
        } else if (e.key === '3') {
            difficulty = DIFFICULTY.HARD;
            startGame();
        }
    }

    if ((gameState === GAME_STATE.GAME_OVER || gameState === GAME_STATE.LEVEL_COMPLETE || gameState === GAME_STATE.GAME_WON) && e.key === ' ') {
        if (gameState === GAME_STATE.GAME_OVER || gameState === GAME_STATE.GAME_WON) {
            restartGame();
        } else if (gameState === GAME_STATE.LEVEL_COMPLETE) {
            nextLevel();
        }
        e.preventDefault();
    }

    if (gameState === GAME_STATE.MENU && e.key === ' ') {
        gameState = GAME_STATE.PLAYING;
        hideModal('menu-modal');
        playBackgroundMusic();
        e.preventDefault();
    }

    if (e.key === ' ') {
        e.preventDefault();
    }
}

function handleKeyUp(e) {
    keys[e.key] = false;
}

function showModal(id) {
    document.getElementById(id).classList.add('show');
}

function hideModal(id) {
    document.getElementById(id).classList.remove('show');
}

function startGame() {
    score = 0;
    level = 1;
    totalCoins = 0;
    gameState = GAME_STATE.MENU;
    hideModal('menu-modal');
    initLevel();
}

function initLevel() {
    player = new Player(50, SCREEN_HEIGHT - 150);
    platforms = [];
    enemies = [];
    coins = [];
    powerUps = [];
    boss = null;
    particles = [];

    switch (level) {
        case 1: createLevel1(); break;
        case 2: createLevel2(); break;
        case 3: createLevel3(); break;
        case 4: createLevel4(); break;
        case 5: createLevel5(); break;
        case 6: createLevel6(); break;
        case 7: createLevel7(); break;
        case 8: createBossLevel(); break;
    }

    gameState = GAME_STATE.PLAYING;
    playBackgroundMusic();
}

// Level creation (same as before, but with decorative platforms)
function createLevel1() {
    platforms.push(new Platform(0, SCREEN_HEIGHT - 50, SCREEN_WIDTH, 50, COLORS.EMERALD, true));
    const platformsData = [
        [200, 550, 150, 20],
        [450, 490, 150, 20],
        [700, 550, 150, 20],
        [150, 380, 200, 20],
        [750, 380, 200, 20],
        [400, 280, 150, 20]
    ];
    platformsData.forEach(p => platforms.push(new Platform(...p, COLORS.EMERALD)));

    const enemySpeed = difficulty === DIFFICULTY.EASY ? 2 : (difficulty === DIFFICULTY.NORMAL ? 3 : 4);
    enemies.push(new Enemy(300, SCREEN_HEIGHT - 100, 80, enemySpeed));
    enemies.push(new Enemy(550, SCREEN_HEIGHT - 100, 80, enemySpeed));

    const coinPositions = [[220, 510], [470, 450], [720, 510], [200, 330], [800, 330], [450, 230]];
    coinPositions.forEach(c => {
        coins.push(new Coin(c[0], c[1]));
        totalCoins++;
    });

    powerUps.push(new PowerUp(600, 430, POWER_UP_TYPE.SHIELD));
}

function createLevel2() {
    platforms.push(new Platform(0, SCREEN_HEIGHT - 50, SCREEN_WIDTH, 50, COLORS.EMERALD, true));
    const platformsData = [
        [100, 600, 120, 20],
        [280, 540, 120, 20],
        [460, 480, 120, 20],
        [640, 540, 120, 20],
        [820, 600, 120, 20],
        [200, 350, 100, 20],
        [800, 350, 100, 20],
        [400, 250, 100, 20]
    ];
    platformsData.forEach(p => platforms.push(new Platform(...p, COLORS.EMERALD)));

    const enemySpeed = difficulty === DIFFICULTY.EASY ? 2.5 : (difficulty === DIFFICULTY.NORMAL ? 3.5 : 5);
    for (let i = 0; i < (difficulty === DIFFICULTY.HARD ? 7 : 5); i++) {
        enemies.push(new Enemy(100 + i * 200, 400 + (i % 2) * 100, 100, enemySpeed));
    }

    const coinPositions = [[150, 560], [330, 500], [510, 440], [690, 500], [870, 560], [250, 300], [750, 300], [450, 200]];
    coinPositions.forEach(c => {
        coins.push(new Coin(c[0], c[1]));
        totalCoins++;
    });

    powerUps.push(new PowerUp(500, 380, POWER_UP_TYPE.SPEED_BOOST));
}

function createLevel3() {
    platforms.push(new Platform(0, SCREEN_HEIGHT - 50, SCREEN_WIDTH, 50, COLORS.EMERALD, true));
    const platformsData = [
        [0, 500, 200, 20],
        [300, 450, 150, 20],
        [600, 500, 150, 20],
        [900, 450, 200, 20],
        [200, 320, 200, 20],
        [800, 320, 200, 20],
        [400, 180, 150, 20]
    ];
    platformsData.forEach(p => platforms.push(new Platform(...p, COLORS.EMERALD)));

    const enemySpeed = difficulty === DIFFICULTY.EASY ? 3 : (difficulty === DIFFICULTY.NORMAL ? 4 : 5.5);
    for (let i = 0; i < (difficulty === DIFFICULTY.HARD ? 8 : 5); i++) {
        enemies.push(new Enemy(150 + i * 150, 300 + (i % 2) * 200, 100, enemySpeed));
    }

    const coinPositions = [[100, 450], [350, 400], [650, 450], [950, 400], [300, 270], [850, 270], [475, 130]];
    coinPositions.forEach(c => {
        coins.push(new Coin(c[0], c[1]));
        totalCoins++;
    });

    powerUps.push(new PowerUp(600, 230, POWER_UP_TYPE.DOUBLE_JUMP));
}

function createLevel4() {
    platforms.push(new Platform(0, SCREEN_HEIGHT - 50, SCREEN_WIDTH, 50, COLORS.EMERALD, true));
    const platformsData = [
        [100, 550, 120, 20],
        [300, 480, 120, 20],
        [500, 550, 120, 20],
        [700, 480, 120, 20],
        [900, 550, 120, 20],
        [200, 350, 150, 20],
        [800, 350, 150, 20],
        [450, 220, 120, 20]
    ];
    platformsData.forEach(p => platforms.push(new Platform(...p, COLORS.EMERALD)));

    const enemySpeed = difficulty === DIFFICULTY.EASY ? 3 : (difficulty === DIFFICULTY.NORMAL ? 4.5 : 6);
    for (let i = 0; i < (difficulty === DIFFICULTY.HARD ? 8 : 5); i++) {
        enemies.push(new Enemy(100 + Math.random() * 800, 200 + Math.random() * 300, 100, enemySpeed));
    }

    const coinPositions = [[150, 500], [350, 430], [550, 500], [750, 430], [950, 500], [275, 300], [825, 300], [500, 170]];
    coinPositions.forEach(c => {
        coins.push(new Coin(c[0], c[1]));
        totalCoins++;
    });

    powerUps.push(new PowerUp(700, 380, POWER_UP_TYPE.INVINCIBLE));
}

function createLevel5() {
    platforms.push(new Platform(0, SCREEN_HEIGHT - 50, SCREEN_WIDTH, 50, COLORS.EMERALD, true));
    for (let i = 0; i < 8; i++) {
        const x = 100 + i * 140;
        const y = SCREEN_HEIGHT - 150 - (i % 2) * 80;
        platforms.push(new Platform(x, y, 120, 20, COLORS.EMERALD));
    }

    const enemySpeed = difficulty === DIFFICULTY.EASY ? 3.5 : (difficulty === DIFFICULTY.NORMAL ? 4.5 : 6.5);
    for (let i = 0; i < (difficulty === DIFFICULTY.HARD ? 10 : 6); i++) {
        enemies.push(new Enemy(50 + Math.random() * 1050, 250 + Math.random() * 250, 120, enemySpeed));
    }

    const coinPositions = [[160, 480], [300, 380], [440, 480], [580, 380], [720, 480], [860, 380], [1000, 480], [600, 200]];
    coinPositions.forEach(c => {
        coins.push(new Coin(c[0], c[1]));
        totalCoins++;
    });

    powerUps.push(new PowerUp(300, 320, POWER_UP_TYPE.SHIELD));
    powerUps.push(new PowerUp(900, 320, POWER_UP_TYPE.SPEED_BOOST));
}

function createLevel6() {
    platforms.push(new Platform(0, SCREEN_HEIGHT - 50, SCREEN_WIDTH, 50, COLORS.EMERALD, true));
    const platformsData = [
        [0, 600, 150, 20],
        [200, 550, 150, 20],
        [400, 500, 150, 20],
        [600, 450, 150, 20],
        [800, 500, 150, 20],
        [1000, 550, 150, 20],
        [100, 320, 200, 20],
        [900, 320, 200, 20],
        [450, 180, 150, 20]
    ];
    platformsData.forEach(p => platforms.push(new Platform(...p, COLORS.EMERALD)));

    const enemySpeed = difficulty === DIFFICULTY.EASY ? 4 : (difficulty === DIFFICULTY.NORMAL ? 5 : 7);
    for (let i = 0; i < (difficulty === DIFFICULTY.HARD ? 12 : 8); i++) {
        enemies.push(new Enemy(50 + Math.random() * 1050, 250 + Math.random() * 250, 100, enemySpeed));
    }

    const coinPositions = [[75, 550], [275, 500], [475, 450], [675, 400], [875, 450], [1075, 500], [200, 270], [900, 270], [525, 130]];
    coinPositions.forEach(c => {
        coins.push(new Coin(c[0], c[1]));
        totalCoins++;
    });

    powerUps.push(new PowerUp(400, 410, POWER_UP_TYPE.DOUBLE_JUMP));
    powerUps.push(new PowerUp(800, 410, POWER_UP_TYPE.INVINCIBLE));
}

function createLevel7() {
    platforms.push(new Platform(0, SCREEN_HEIGHT - 50, SCREEN_WIDTH, 50, COLORS.EMERALD, true));
    const centerX = SCREEN_WIDTH / 2;
    const centerY = SCREEN_HEIGHT / 2;

    for (let i = 0; i < 6; i++) {
        const angle = (i * 60) * Math.PI / 180;
        const x = centerX + 300 * Math.cos(angle);
        const y = centerY + 200 * Math.sin(angle);
        platforms.push(new Platform(x - 60, y - 50, 120, 20, COLORS.EMERALD));
    }

    platforms.push(new Platform(centerX - 75, centerY - 10, 150, 20, COLORS.GOLD));

    const enemySpeed = difficulty === DIFFICULTY.EASY ? 4 : (difficulty === DIFFICULTY.NORMAL ? 5.5 : 7.5);
    for (let i = 0; i < (difficulty === DIFFICULTY.HARD ? 15 : 10); i++) {
        enemies.push(new Enemy(50 + Math.random() * 1050, 200 + Math.random() * 350, 120, enemySpeed));
    }

    const coinPositions = [];
    for (let i = 0; i < 6; i++) {
        const angle = (i * 60 + 30) * Math.PI / 180;
        const x = centerX + 250 * Math.cos(angle);
        const y = centerY + 150 * Math.sin(angle);
        coinPositions.push([x, y]);
    }

    coinPositions.forEach(c => {
        coins.push(new Coin(c[0], c[1]));
        totalCoins++;
    });

    powerUps.push(new PowerUp(centerX, centerY - 100, POWER_UP_TYPE.INVINCIBLE));
    powerUps.push(new PowerUp(centerX - 150, centerY, POWER_UP_TYPE.DOUBLE_JUMP));
    powerUps.push(new PowerUp(centerX + 150, centerY, POWER_UP_TYPE.SPEED_BOOST));
}

function createBossLevel() {
    platforms.push(new Platform(0, SCREEN_HEIGHT - 50, SCREEN_WIDTH, 50, COLORS.EMERALD, true));
    platforms.push(new Platform(SCREEN_WIDTH / 2 - 200, SCREEN_HEIGHT - 250, 400, 20, COLORS.DARK_RED));
    platforms.push(new Platform(50, SCREEN_HEIGHT - 150, 150, 20, COLORS.EMERALD));
    platforms.push(new Platform(SCREEN_WIDTH - 200, SCREEN_HEIGHT - 150, 150, 20, COLORS.EMERALD));

    const bossHealth = difficulty === DIFFICULTY.EASY ? 3 : (difficulty === DIFFICULTY.NORMAL ? 5 : 8);
    boss = new Boss(SCREEN_WIDTH / 2 - 40, SCREEN_HEIGHT - 450, bossHealth);

    for (let i = 0; i < 8; i++) {
        coins.push(new Coin(SCREEN_WIDTH / 2 - 150 + i * 40, SCREEN_HEIGHT - 350));
        totalCoins++;
    }

    powerUps.push(new PowerUp(SCREEN_WIDTH / 2 - 100, SCREEN_HEIGHT - 280, POWER_UP_TYPE.SHIELD));
    powerUps.push(new PowerUp(SCREEN_WIDTH / 2 + 100, SCREEN_HEIGHT - 280, POWER_UP_TYPE.INVINCIBLE));
}

function gameLoop() {
    frameCount++;
    update();
    draw();
    requestAnimationFrame(gameLoop);
}

function update() {
    if (gameState !== GAME_STATE.PLAYING) return;

    const moveLeft = keys['ArrowLeft'] || keys['a'] || keys['A'];
    const moveRight = keys['ArrowRight'] || keys['d'] || keys['D'];
    const jump = keys[' '] || keys['ArrowUp'] || keys['w'] || keys['W'];

    player.handleInput(moveLeft, moveRight, jump);
    player.update(platforms, enemies, coins, powerUps);

    enemies.forEach(e => e.update());
    coins.forEach(c => c.update());
    powerUps.forEach(p => p.update());

    // Update particles
    particles = particles.filter(p => {
        p.update();
        return p.life > 0;
    });

    if (boss) {
        boss.update();
        boss.projectiles.forEach(proj => {
            if (player.collidesWith(proj)) {
                player.takeDamage();
                proj.remove = true;
                createExplosion(proj.x, proj.y, COLORS.GOLD, 5);
            }
        });
        boss.projectiles = boss.projectiles.filter(p => !p.remove);

        if (player.collidesWith(boss) && player.velY > 0) {
            boss.takeDamage();
            player.velY = JUMP_STRENGTH;
            score += 100;
            sounds.bosshit();
            createExplosion(boss.x + boss.width / 2, boss.y, COLORS.DARK_RED, 10);
        }

        if (boss.health <= 0) {
            gameState = GAME_STATE.LEVEL_COMPLETE;
            isMusicPlaying = false;
            sounds.levelUp();
            createExplosion(boss.x + boss.width / 2, boss.y, COLORS.GOLD, 20);
            showLevelCompleteModal();
        }
    }

    if (coins.length === 0 && level < MAX_LEVELS && !boss) {
        gameState = GAME_STATE.LEVEL_COMPLETE;
        isMusicPlaying = false;
        sounds.levelUp();
        showLevelCompleteModal();
    }

    if (player.health <= 0) {
        gameState = GAME_STATE.GAME_OVER;
        isMusicPlaying = false;
        showGameOverModal();
    }

    score++;
    updateHUD();
}

function createExplosion(x, y, color, count) {
    for (let i = 0; i < count; i++) {
        const angle = (Math.random() * Math.PI * 2);
        const velocity = 2 + Math.random() * 4;
        particles.push(new Particle(x, y, color, angle, velocity));
    }
}

function draw() {
    // Beautiful gradient background
    const gradient = ctx.createLinearGradient(0, 0, 0, SCREEN_HEIGHT);
    gradient.addColorStop(0, COLORS.SKY_BLUE);
    gradient.addColorStop(1, COLORS.LIGHT_BLUE);
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT);

    // Draw moving clouds
    drawClouds();

    if (gameState === GAME_STATE.PLAYING) {
        // Draw decorative elements
        drawDecorations();

        platforms.forEach(p => p.draw(ctx));
        enemies.forEach(e => e.draw(ctx));
        coins.forEach(c => c.draw(ctx));
        powerUps.forEach(p => p.draw(ctx));

        // Draw particles
        particles.forEach(p => p.draw(ctx));

        player.draw(ctx);

        if (boss) {
            boss.draw(ctx);
            drawBossHealthBar();
        }

        drawPowerUpIndicators();
    }
}

function drawClouds() {
    const cloudOffset = (frameCount / 2) % SCREEN_WIDTH;
    for (let i = 0; i < 3; i++) {
        drawCloud(cloudOffset - SCREEN_WIDTH + i * SCREEN_WIDTH, 100 - i * 50);
    }
}

function drawCloud(x, y) {
    ctx.fillStyle = 'rgba(255, 255, 255, 0.6)';
    ctx.beginPath();
    ctx.arc(x, y, 30, 0, Math.PI * 2);
    ctx.arc(x + 40, y, 35, 0, Math.PI * 2);
    ctx.arc(x + 80, y, 30, 0, Math.PI * 2);
    ctx.fill();
}

function drawDecorations() {
    // Draw temple tops on platforms
    ctx.fillStyle = COLORS.GOLD;
    ctx.globalAlpha = 0.3;

    platforms.forEach(p => {
        if (p.isGround) {
            // Draw temple pattern
            for (let i = 0; i < p.width; i += 40) {
                const x = p.x + i;
                const y = p.y - 5;
                // Small temple shapes
                ctx.fillRect(x, y - 10, 10, 10);
                ctx.fillRect(x + 15, y - 15, 10, 15);
            }
        }
    });

    ctx.globalAlpha = 1;
}

function drawBossHealthBar() {
    const barWidth = 200;
    const barHeight = 25;
    const x = SCREEN_WIDTH / 2 - barWidth / 2;
    const y = 20;

    // Shadow
    ctx.fillStyle = 'rgba(0, 0, 0, 0.3)';
    ctx.fillRect(x - 2, y - 2, barWidth + 4, barHeight + 4);

    // Background
    ctx.fillStyle = COLORS.DARK_RED;
    ctx.fillRect(x, y, barWidth, barHeight);

    // Health bar
    const healthRatio = Math.max(0, boss.health / boss.maxHealth);
    const gradient = ctx.createLinearGradient(x, y, x + barWidth * healthRatio, y);
    gradient.addColorStop(0, COLORS.EMERALD);
    gradient.addColorStop(1, COLORS.ORANGE);
    ctx.fillStyle = gradient;
    ctx.fillRect(x, y, barWidth * healthRatio, barHeight);

    // Border
    ctx.strokeStyle = COLORS.GOLD;
    ctx.lineWidth = 2;
    ctx.strokeRect(x, y, barWidth, barHeight);

    // Text
    ctx.fillStyle = COLORS.GOLD;
    ctx.font = 'bold 12px Arial';
    ctx.textAlign = 'center';
    ctx.fillText('BOSS', SCREEN_WIDTH / 2, y + 17);
}

function drawPowerUpIndicators() {
    let y = 30;
    ctx.font = 'bold 14px Arial';

    if (player.hasShield) {
        ctx.fillStyle = COLORS.LIGHT_GREEN;
        ctx.fillText('🛡️ SHIELD', 60, y);
        y += 25;
    }

    if (player.speedBoostTime > 0) {
        ctx.fillStyle = COLORS.PURPLE;
        ctx.fillText('⚡ SPEED', 60, y);
        y += 25;
    }

    if (player.doubleJumpTime > 0) {
        ctx.fillStyle = COLORS.GOLD;
        ctx.fillText('🔆 2-JUMP', 60, y);
    }
}

function updateHUD() {
    document.getElementById('level').textContent = `${level}/${MAX_LEVELS}`;
    document.getElementById('score').textContent = score;
    document.getElementById('coins').textContent = `${totalCoins - coins.length}/${totalCoins}`;
    document.getElementById('health').textContent = '❤️'.repeat(player.health);
}

function showGameOverModal() {
    document.getElementById('go-level').textContent = level;
    document.getElementById('go-score').textContent = score;
    showModal('game-over-modal');
}

function showLevelCompleteModal() {
    document.getElementById('lc-level').textContent = level;
    document.getElementById('lc-score').textContent = score;
    showModal('level-complete-modal');
}

function nextLevel() {
    hideModal('level-complete-modal');
    level++;
    if (level <= MAX_LEVELS) {
        initLevel();
    } else {
        gameState = GAME_STATE.GAME_WON;
        document.getElementById('gw-score').textContent = score;
        document.getElementById('gw-difficulty').textContent = difficulty.toUpperCase();
        showModal('game-won-modal');
    }
}

function restartGame() {
    hideModal('game-over-modal');
    hideModal('game-won-modal');
    score = 0;
    level = 1;
    totalCoins = 0;
    isMusicPlaying = false;
    gameState = GAME_STATE.DIFFICULTY_SELECT;
    showModal('menu-modal');
}

// Enhanced Entity Classes with Better Graphics

class Particle {
    constructor(x, y, color, angle, velocity) {
        this.x = x;
        this.y = y;
        this.color = color;
        this.velX = Math.cos(angle) * velocity;
        this.velY = Math.sin(angle) * velocity;
        this.life = 30;
        this.maxLife = 30;
        this.size = 4;
    }

    update() {
        this.x += this.velX;
        this.y += this.velY;
        this.velY += GRAVITY * 0.5;
        this.life--;
    }

    draw(ctx) {
        ctx.fillStyle = this.color;
        ctx.globalAlpha = this.life / this.maxLife;
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        ctx.fill();
        ctx.globalAlpha = 1;
    }
}

class Player {
    constructor(x, y) {
        this.x = x;
        this.y = y;
        this.width = 40;
        this.height = 50;
        this.velX = 0;
        this.velY = 0;
        this.baseSpeed = 6;
        this.health = 3;
        this.onGround = false;
        this.facingRight = true;
        this.invulnerable = 0;
        this.jumpAvailable = true;

        this.hasShield = false;
        this.speedBoostTime = 0;
        this.doubleJumpTime = 0;
        this.invincibleTime = 0;
        this.doubleJumpAvailable = false;
    }

    handleInput(moveLeft, moveRight, jump) {
        const speed = this.speedBoostTime > 0 ? this.baseSpeed * 1.5 : this.baseSpeed;

        this.velX = 0;
        if (moveLeft) {
            this.velX = -speed;
            this.facingRight = false;
        } else if (moveRight) {
            this.velX = speed;
            this.facingRight = true;
        }

        if (jump) {
            if (this.onGround && this.jumpAvailable) {
                this.velY = JUMP_STRENGTH;
                this.onGround = false;
                this.jumpAvailable = false;
                sounds.jump();
                createExplosion(this.x + this.width / 2, this.y + this.height, COLORS.SAFFRON, 3);
            } else if (this.doubleJumpAvailable && this.doubleJumpTime > 0) {
                this.velY = JUMP_STRENGTH;
                this.doubleJumpAvailable = false;
                sounds.jump();
                createExplosion(this.x + this.width / 2, this.y + this.height, COLORS.GOLD, 3);
            }
        }
    }

    update(platforms, enemies, coins, powerUps) {
        this.speedBoostTime = Math.max(0, this.speedBoostTime - 1);
        this.doubleJumpTime = Math.max(0, this.doubleJumpTime - 1);
        this.invincibleTime = Math.max(0, this.invincibleTime - 1);
        this.invulnerable = Math.max(0, this.invulnerable - 1);

        this.velY += GRAVITY;
        this.velY = Math.min(this.velY, 15);

        this.x += this.velX;
        if (this.x < 0) this.x = 0;
        if (this.x + this.width > SCREEN_WIDTH) this.x = SCREEN_WIDTH - this.width;

        this.y += this.velY;
        this.onGround = false;

        platforms.forEach(p => {
            if (this.collidesWith(p)) {
                if (this.velY > 0) {
                    this.y = p.y - this.height;
                    this.velY = 0;
                    this.onGround = true;
                    this.jumpAvailable = true;
                    this.doubleJumpAvailable = this.doubleJumpTime > 0;
                } else if (this.velY < 0) {
                    this.y = p.y + p.height;
                    this.velY = 0;
                }
            }
        });

        enemies.forEach(e => {
            if (this.collidesWith(e) && this.invulnerable <= 0 && this.invincibleTime <= 0) {
                this.takeDamage();
                createExplosion(this.x + this.width / 2, this.y + this.height / 2, COLORS.DARK_RED, 5);
            }
        });

        powerUps = powerUps.filter(p => {
            if (this.collidesWith(p)) {
                this.applyPowerUp(p.type);
                sounds.powerUp();
                createExplosion(p.x, p.y, p.getColor(), 8);
                return false;
            }
            return true;
        });

        coins = coins.filter(c => {
            if (this.collidesWith(c)) {
                sounds.coin();
                score += 10;
                createExplosion(c.x, c.y, COLORS.GOLD, 5);
                return false;
            }
            return true;
        });

        if (this.y > SCREEN_HEIGHT) {
            this.health = 0;
        }
    }

    takeDamage() {
        if (this.hasShield) {
            this.hasShield = false;
        } else {
            this.health--;
        }
        this.invulnerable = 120;
    }

    applyPowerUp(type) {
        switch (type) {
            case POWER_UP_TYPE.SHIELD:
                this.hasShield = true;
                break;
            case POWER_UP_TYPE.SPEED_BOOST:
                this.speedBoostTime = 300;
                break;
            case POWER_UP_TYPE.DOUBLE_JUMP:
                this.doubleJumpTime = 300;
                this.doubleJumpAvailable = true;
                break;
            case POWER_UP_TYPE.INVINCIBLE:
                this.invincibleTime = 300;
                break;
        }
    }

    collidesWith(obj) {
        return this.x < obj.x + obj.width &&
               this.x + this.width > obj.x &&
               this.y < obj.y + obj.height &&
               this.y + this.height > obj.y;
    }

    draw(ctx) {
        if (this.invulnerable % 10 < 5 || this.invincibleTime > 0) {
            // Draw enhanced player character
            ctx.save();
            ctx.translate(this.x + this.width / 2, this.y + this.height / 2);
            if (!this.facingRight) ctx.scale(-1, 1);
            ctx.translate(-this.width / 2, -this.height / 2);

            // Body
            ctx.fillStyle = COLORS.SAFFRON;
            ctx.fillRect(5, 15, 30, 25);

            // Head
            ctx.fillStyle = COLORS.ORANGE;
            ctx.beginPath();
            ctx.arc(20, 10, 8, 0, Math.PI * 2);
            ctx.fill();

            // Turban/Crown
            ctx.fillStyle = COLORS.GOLD;
            ctx.beginPath();
            ctx.moveTo(12, 5);
            ctx.lineTo(20, -5);
            ctx.lineTo(28, 5);
            ctx.fill();

            // Eyes
            ctx.fillStyle = COLORS.DEEP_BLUE;
            ctx.beginPath();
            ctx.arc(16, 8, 2, 0, Math.PI * 2);
            ctx.fill();
            ctx.beginPath();
            ctx.arc(24, 8, 2, 0, Math.PI * 2);
            ctx.fill();

            // Mouth
            ctx.strokeStyle = COLORS.DEEP_BLUE;
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.arc(20, 12, 2, 0, Math.PI);
            ctx.stroke();

            ctx.restore();

            // Shield effect
            if (this.hasShield) {
                ctx.strokeStyle = COLORS.LIGHT_GREEN;
                ctx.lineWidth = 3;
                ctx.beginPath();
                ctx.arc(this.x + this.width / 2, this.y + this.height / 2, 30, 0, Math.PI * 2);
                ctx.stroke();
            }

            // Speed aura
            if (this.speedBoostTime > 0) {
                ctx.strokeStyle = COLORS.PURPLE;
                ctx.lineWidth = 2;
                ctx.globalAlpha = 0.6;
                ctx.beginPath();
                ctx.arc(this.x + this.width / 2, this.y + this.height / 2, 28, 0, Math.PI * 2);
                ctx.stroke();
                ctx.globalAlpha = 1;
            }

            // Invincible aura
            if (this.invincibleTime > 0) {
                ctx.strokeStyle = COLORS.GOLD;
                ctx.lineWidth = 3;
                ctx.globalAlpha = 0.8;
                ctx.beginPath();
                ctx.arc(this.x + this.width / 2, this.y + this.height / 2, 32, 0, Math.PI * 2);
                ctx.stroke();
                ctx.globalAlpha = 1;
            }
        }
    }
}

class Enemy {
    constructor(x, y, patrolRange, speed) {
        this.x = x;
        this.y = y;
        this.width = 35;
        this.height = 35;
        this.velX = -speed;
        this.startX = x;
        this.patrolRange = patrolRange;
        this.speed = speed;
        this.animFrame = 0;
    }

    update() {
        this.x += this.velX;
        this.animFrame++;

        if (this.x < this.startX - this.patrolRange) {
            this.velX = this.speed;
        } else if (this.x > this.startX + this.patrolRange) {
            this.velX = -this.speed;
        }
    }

    draw(ctx) {
        ctx.save();
        ctx.translate(this.x + this.width / 2, this.y + this.height / 2);
        if (this.velX > 0) ctx.scale(-1, 1);
        ctx.translate(-this.width / 2, -this.height / 2);

        // Body
        ctx.fillStyle = COLORS.DARK_RED;
        ctx.fillRect(3, 10, 29, 20);

        // Head
        ctx.fillStyle = COLORS.DARK_RED;
        ctx.beginPath();
        ctx.arc(17.5, 8, 7, 0, Math.PI * 2);
        ctx.fill();

        // Eyes
        ctx.fillStyle = COLORS.GOLD;
        ctx.beginPath();
        ctx.arc(13, 6, 2.5, 0, Math.PI * 2);
        ctx.fill();
        ctx.beginPath();
        ctx.arc(22, 6, 2.5, 0, Math.PI * 2);
        ctx.fill();

        // Horns
        ctx.strokeStyle = COLORS.GOLD;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(12, 2);
        ctx.lineTo(10, -5);
        ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(23, 2);
        ctx.lineTo(25, -5);
        ctx.stroke();

        // Evil mouth
        ctx.strokeStyle = COLORS.GOLD;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(15, 10);
        ctx.lineTo(20, 10);
        ctx.stroke();

        ctx.restore();
    }
}

class Coin {
    constructor(x, y) {
        this.x = x;
        this.y = y;
        this.width = 20;
        this.height = 20;
        this.rotation = 0;
        this.bobOffset = 0;
    }

    update() {
        this.rotation = (this.rotation + 6) % 360;
        this.bobOffset = Math.sin(this.rotation * Math.PI / 180) * 3;
    }

    draw(ctx) {
        ctx.save();
        ctx.translate(this.x + this.width / 2, this.y + this.width / 2 + this.bobOffset);
        ctx.rotate(this.rotation * Math.PI / 180);

        // Outer ring
        ctx.fillStyle = COLORS.GOLD;
        ctx.beginPath();
        ctx.arc(0, 0, 10, 0, Math.PI * 2);
        ctx.fill();

        // Inner circle
        ctx.fillStyle = COLORS.SAFFRON;
        ctx.beginPath();
        ctx.arc(0, 0, 7, 0, Math.PI * 2);
        ctx.fill();

        // Rupee symbol
        ctx.strokeStyle = COLORS.DEEP_BLUE;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.arc(0, 0, 5, 0, Math.PI);
        ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(-2, 0);
        ctx.lineTo(2, 0);
        ctx.stroke();

        ctx.restore();
    }
}

class PowerUp {
    constructor(x, y, type) {
        this.x = x;
        this.y = y;
        this.width = 25;
        this.height = 25;
        this.type = type;
        this.rotation = 0;
        this.bobOffset = 0;
    }

    update() {
        this.rotation = (this.rotation + 8) % 360;
        this.bobOffset = Math.sin((this.rotation * Math.PI / 180) + frameCount / 30) * 5;
    }

    getColor() {
        switch (this.type) {
            case POWER_UP_TYPE.SHIELD: return COLORS.LIGHT_GREEN;
            case POWER_UP_TYPE.SPEED_BOOST: return COLORS.PURPLE;
            case POWER_UP_TYPE.DOUBLE_JUMP: return COLORS.GOLD;
            case POWER_UP_TYPE.INVINCIBLE: return COLORS.SAFFRON;
            default: return COLORS.GOLD;
        }
    }

    draw(ctx) {
        ctx.save();
        ctx.translate(this.x + this.width / 2, this.y + this.height / 2 + this.bobOffset);
        ctx.rotate(this.rotation * Math.PI / 180);

        const size = 12;
        ctx.fillStyle = this.getColor();
        ctx.strokeStyle = COLORS.DEEP_BLUE;
        ctx.lineWidth = 1;

        // Draw star
        ctx.beginPath();
        for (let i = 0; i < 5; i++) {
            const angle = (i * 4) * Math.PI / 180;
            const x = Math.cos(angle) * size;
            const y = Math.sin(angle) * size;
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        }
        ctx.closePath();
        ctx.fill();
        ctx.stroke();

        ctx.restore();
    }
}

class Platform {
    constructor(x, y, width, height, color, isGround = false) {
        this.x = x;
        this.y = y;
        this.width = width;
        this.height = height;
        this.color = color;
        this.isGround = isGround;
    }

    draw(ctx) {
        // Main platform
        ctx.fillStyle = this.color;
        ctx.fillRect(this.x, this.y, this.width, this.height);

        // Border
        ctx.strokeStyle = COLORS.DEEP_BLUE;
        ctx.lineWidth = 2;
        ctx.strokeRect(this.x, this.y, this.width, this.height);

        // Decorative pattern
        ctx.fillStyle = COLORS.SAFFRON;
        ctx.globalAlpha = 0.5;
        for (let i = 0; i < this.width; i += 25) {
            ctx.beginPath();
            ctx.arc(this.x + i, this.y + 5, 3, 0, Math.PI * 2);
            ctx.fill();
        }
        ctx.globalAlpha = 1;

        // Top shine
        ctx.fillStyle = 'rgba(255, 255, 255, 0.2)';
        ctx.fillRect(this.x, this.y, this.width, 3);
    }
}

class Boss {
    constructor(x, y, health) {
        this.x = x;
        this.y = y;
        this.width = 80;
        this.height = 80;
        this.health = health;
        this.maxHealth = health;
        this.velX = -4;
        this.attackTimer = 0;
        this.projectiles = [];
        this.invulnerable = 0;
        this.animFrame = 0;
    }

    update() {
        this.x += this.velX;
        this.animFrame++;

        if (this.x < 100 || this.x > SCREEN_WIDTH - 100) {
            this.velX *= -1;
        }

        this.attackTimer++;
        if (this.attackTimer > 60) {
            this.shoot();
            this.attackTimer = 0;
        }

        this.invulnerable = Math.max(0, this.invulnerable - 1);
        this.projectiles.forEach(p => p.update());
    }

    shoot() {
        this.projectiles.push(new Projectile(this.x + this.width / 2, this.y + this.height / 2, -5, 0));
        this.projectiles.push(new Projectile(this.x + this.width / 2, this.y + this.height / 2, 5, 0));
    }

    takeDamage() {
        if (this.invulnerable <= 0) {
            this.health--;
            this.invulnerable = 30;
        }
    }

    draw(ctx) {
        if (this.invulnerable % 10 < 5) {
            ctx.save();
            ctx.translate(this.x + this.width / 2, this.y + this.height / 2);

            // Body
            ctx.fillStyle = COLORS.DARK_RED;
            ctx.fillRect(-40, -30, 80, 60);

            // Head
            ctx.fillStyle = COLORS.DARK_RED;
            ctx.beginPath();
            ctx.arc(0, -35, 15, 0, Math.PI * 2);
            ctx.fill();

            // Crown
            ctx.fillStyle = COLORS.GOLD;
            for (let i = 0; i < 5; i++) {
                const x = -25 + i * 12.5;
                ctx.fillRect(x, -50, 8, 15);
            }

            // Eyes
            ctx.fillStyle = COLORS.GOLD;
            ctx.beginPath();
            ctx.arc(-7, -38, 3, 0, Math.PI * 2);
            ctx.fill();
            ctx.beginPath();
            ctx.arc(7, -38, 3, 0, Math.PI * 2);
            ctx.fill();

            // Menacing mouth
            ctx.strokeStyle = COLORS.GOLD;
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(-5, -32);
            ctx.lineTo(5, -32);
            ctx.stroke();

            // Arms
            ctx.strokeStyle = COLORS.DARK_RED;
            ctx.lineWidth = 8;
            ctx.beginPath();
            ctx.arc(-40, -15, 5, 0, Math.PI * 2);
            ctx.stroke();
            ctx.beginPath();
            ctx.arc(40, -15, 5, 0, Math.PI * 2);
            ctx.stroke();

            ctx.restore();
        }

        // Draw projectiles
        this.projectiles.forEach(p => p.draw(ctx));
    }
}

class Projectile {
    constructor(x, y, velX, velY) {
        this.x = x;
        this.y = y;
        this.width = 10;
        this.height = 10;
        this.velX = velX;
        this.velY = velY;
        this.remove = false;
    }

    update() {
        this.x += this.velX;
        this.y += this.velY;

        if (this.x < 0 || this.x > SCREEN_WIDTH) {
            this.remove = true;
        }
    }

    draw(ctx) {
        ctx.fillStyle = COLORS.GOLD;
        ctx.shadowColor = COLORS.SAFFRON;
        ctx.shadowBlur = 10;
        ctx.beginPath();
        ctx.arc(this.x, this.y, 5, 0, Math.PI * 2);
        ctx.fill();
        ctx.shadowBlur = 0;
    }
}

document.addEventListener('DOMContentLoaded', init);
