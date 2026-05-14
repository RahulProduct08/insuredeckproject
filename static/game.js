/**
 * Temple Quest - Indian Mario Adventure
 * Web Version using HTML5 Canvas
 */

// Constants
const SCREEN_WIDTH = 1200;
const SCREEN_HEIGHT = 700;
const GRAVITY = 0.5;
const JUMP_STRENGTH = -15;

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
    LIGHT_GREEN: '#90ee90'
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

// Game objects
let player, platforms, enemies, coins, powerUps, boss;
let keys = {};

// Initialize game
function init() {
    canvas = document.getElementById('gameCanvas');
    ctx = canvas.getContext('2d');

    // Set actual canvas resolution
    canvas.width = SCREEN_WIDTH;
    canvas.height = SCREEN_HEIGHT;

    // Event listeners
    document.addEventListener('keydown', handleKeyDown);
    document.addEventListener('keyup', handleKeyUp);

    // Button listeners
    document.querySelectorAll('.difficulty-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            difficulty = e.target.dataset.difficulty;
            startGame();
        });
    });

    // Modal click handlers
    document.getElementById('game-over-modal').addEventListener('click', restartGame);
    document.getElementById('level-complete-modal').addEventListener('click', nextLevel);
    document.getElementById('game-won-modal').addEventListener('click', restartGame);

    gameState = GAME_STATE.DIFFICULTY_SELECT;
    showModal('menu-modal');

    gameLoop();
}

// Keyboard handlers
function handleKeyDown(e) {
    keys[e.key] = true;

    // Difficulty selection
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

    // Menu navigation
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
        e.preventDefault();
    }

    if (e.key === ' ') {
        e.preventDefault();
    }
}

function handleKeyUp(e) {
    keys[e.key] = false;
}

// Show/Hide modals
function showModal(id) {
    document.getElementById(id).classList.add('show');
}

function hideModal(id) {
    document.getElementById(id).classList.remove('show');
}

// Game functions
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
}

// Level creation functions
function createLevel1() {
    // Ground
    platforms.push(new Platform(0, SCREEN_HEIGHT - 50, SCREEN_WIDTH, 50, COLORS.EMERALD));

    // Platforms
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
    const enemyData = [
        [300, SCREEN_HEIGHT - 100, 80],
        [550, SCREEN_HEIGHT - 100, 80]
    ];

    enemyData.forEach(e => enemies.push(new Enemy(e[0], e[1], e[2], enemySpeed)));

    const coinPositions = [
        [220, 510], [470, 450], [720, 510],
        [200, 330], [800, 330], [450, 230]
    ];

    coinPositions.forEach(c => {
        coins.push(new Coin(c[0], c[1]));
        totalCoins++;
    });

    powerUps.push(new PowerUp(600, 430, POWER_UP_TYPE.SHIELD));
}

function createLevel2() {
    platforms.push(new Platform(0, SCREEN_HEIGHT - 50, SCREEN_WIDTH, 50, COLORS.EMERALD));

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

    const coinPositions = [
        [150, 560], [330, 500], [510, 440], [690, 500], [870, 560],
        [250, 300], [750, 300], [450, 200]
    ];

    coinPositions.forEach(c => {
        coins.push(new Coin(c[0], c[1]));
        totalCoins++;
    });

    powerUps.push(new PowerUp(500, 380, POWER_UP_TYPE.SPEED_BOOST));
}

function createLevel3() {
    platforms.push(new Platform(0, SCREEN_HEIGHT - 50, SCREEN_WIDTH, 50, COLORS.EMERALD));

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

    const coinPositions = [
        [100, 450], [350, 400], [650, 450], [950, 400],
        [300, 270], [850, 270], [475, 130]
    ];

    coinPositions.forEach(c => {
        coins.push(new Coin(c[0], c[1]));
        totalCoins++;
    });

    powerUps.push(new PowerUp(600, 230, POWER_UP_TYPE.DOUBLE_JUMP));
}

function createLevel4() {
    platforms.push(new Platform(0, SCREEN_HEIGHT - 50, SCREEN_WIDTH, 50, COLORS.EMERALD));

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
        const x = 100 + Math.random() * 800;
        const y = 200 + Math.random() * 300;
        enemies.push(new Enemy(x, y, 100, enemySpeed));
    }

    const coinPositions = [
        [150, 500], [350, 430], [550, 500], [750, 430], [950, 500],
        [275, 300], [825, 300], [500, 170]
    ];

    coinPositions.forEach(c => {
        coins.push(new Coin(c[0], c[1]));
        totalCoins++;
    });

    powerUps.push(new PowerUp(700, 380, POWER_UP_TYPE.INVINCIBLE));
}

function createLevel5() {
    platforms.push(new Platform(0, SCREEN_HEIGHT - 50, SCREEN_WIDTH, 50, COLORS.EMERALD));

    for (let i = 0; i < 8; i++) {
        const x = 100 + i * 140;
        const y = SCREEN_HEIGHT - 150 - (i % 2) * 80;
        platforms.push(new Platform(x, y, 120, 20, COLORS.EMERALD));
    }

    const enemySpeed = difficulty === DIFFICULTY.EASY ? 3.5 : (difficulty === DIFFICULTY.NORMAL ? 4.5 : 6.5);

    for (let i = 0; i < (difficulty === DIFFICULTY.HARD ? 10 : 6); i++) {
        const x = 50 + Math.random() * 1050;
        const y = 250 + Math.random() * 250;
        enemies.push(new Enemy(x, y, 120, enemySpeed));
    }

    const coinPositions = [
        [160, 480], [300, 380], [440, 480], [580, 380],
        [720, 480], [860, 380], [1000, 480], [600, 200]
    ];

    coinPositions.forEach(c => {
        coins.push(new Coin(c[0], c[1]));
        totalCoins++;
    });

    powerUps.push(new PowerUp(300, 320, POWER_UP_TYPE.SHIELD));
    powerUps.push(new PowerUp(900, 320, POWER_UP_TYPE.SPEED_BOOST));
}

function createLevel6() {
    platforms.push(new Platform(0, SCREEN_HEIGHT - 50, SCREEN_WIDTH, 50, COLORS.EMERALD));

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
        const x = 50 + Math.random() * 1050;
        const y = 250 + Math.random() * 250;
        enemies.push(new Enemy(x, y, 100, enemySpeed));
    }

    const coinPositions = [
        [75, 550], [275, 500], [475, 450], [675, 400], [875, 450],
        [1075, 500], [200, 270], [900, 270], [525, 130]
    ];

    coinPositions.forEach(c => {
        coins.push(new Coin(c[0], c[1]));
        totalCoins++;
    });

    powerUps.push(new PowerUp(400, 410, POWER_UP_TYPE.DOUBLE_JUMP));
    powerUps.push(new PowerUp(800, 410, POWER_UP_TYPE.INVINCIBLE));
}

function createLevel7() {
    platforms.push(new Platform(0, SCREEN_HEIGHT - 50, SCREEN_WIDTH, 50, COLORS.EMERALD));

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
        const x = 50 + Math.random() * 1050;
        const y = 200 + Math.random() * 350;
        enemies.push(new Enemy(x, y, 120, enemySpeed));
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
    platforms.push(new Platform(0, SCREEN_HEIGHT - 50, SCREEN_WIDTH, 50, COLORS.EMERALD));
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

// Game loop
function gameLoop() {
    update();
    draw();
    requestAnimationFrame(gameLoop);
}

function update() {
    if (gameState !== GAME_STATE.PLAYING) return;

    // Handle player input
    const moveLeft = keys['ArrowLeft'] || keys['a'] || keys['A'];
    const moveRight = keys['ArrowRight'] || keys['d'] || keys['D'];
    const jump = keys[' '] || keys['ArrowUp'] || keys['w'] || keys['W'];

    player.handleInput(moveLeft, moveRight, jump);
    player.update(platforms, enemies, coins, powerUps);

    // Update enemies
    enemies.forEach(e => e.update());

    // Update coins
    coins.forEach(c => c.update());

    // Update power-ups
    powerUps.forEach(p => p.update());

    // Update boss
    if (boss) {
        boss.update();
        boss.projectiles.forEach(proj => {
            if (player.collidesWith(proj)) {
                player.takeDamage();
                proj.remove = true;
            }
        });
        boss.projectiles = boss.projectiles.filter(p => !p.remove);

        if (player.collidesWith(boss) && player.velY > 0) {
            boss.takeDamage();
            player.velY = JUMP_STRENGTH;
            score += 100;
        }

        if (boss.health <= 0) {
            gameState = GAME_STATE.LEVEL_COMPLETE;
            showLevelCompleteModal();
        }
    }

    // Check level completion
    if (coins.length === 0 && level < MAX_LEVELS && !boss) {
        gameState = GAME_STATE.LEVEL_COMPLETE;
        showLevelCompleteModal();
    }

    // Check game over
    if (player.health <= 0) {
        gameState = GAME_STATE.GAME_OVER;
        showGameOverModal();
    }

    // Scoring
    score++;

    updateHUD();
}

function draw() {
    // Clear canvas
    ctx.fillStyle = COLORS.SKY_BLUE;
    ctx.fillRect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT);

    if (gameState === GAME_STATE.PLAYING) {
        // Draw platforms
        platforms.forEach(p => p.draw(ctx));

        // Draw enemies
        enemies.forEach(e => e.draw(ctx));

        // Draw coins
        coins.forEach(c => c.draw(ctx));

        // Draw power-ups
        powerUps.forEach(p => p.draw(ctx));

        // Draw player
        player.draw(ctx);

        // Draw boss
        if (boss) {
            boss.draw(ctx);
            drawBossHealthBar();
        }

        // Draw power-up indicators
        drawPowerUpIndicators();
    }
}

function drawBossHealthBar() {
    const barWidth = 200;
    const barHeight = 20;
    const x = SCREEN_WIDTH / 2 - barWidth / 2;
    const y = 30;

    ctx.fillStyle = COLORS.DARK_RED;
    ctx.fillRect(x, y, barWidth, barHeight);

    const healthRatio = Math.max(0, boss.health / boss.maxHealth);
    ctx.fillStyle = COLORS.EMERALD;
    ctx.fillRect(x, y, barWidth * healthRatio, barHeight);

    ctx.strokeStyle = COLORS.DEEP_BLUE;
    ctx.lineWidth = 2;
    ctx.strokeRect(x, y, barWidth, barHeight);
}

function drawPowerUpIndicators() {
    let y = 30;

    if (player.hasShield) {
        ctx.fillStyle = COLORS.LIGHT_GREEN;
        ctx.font = 'bold 16px Arial';
        ctx.fillText('🛡️ SHIELD', 20, y);
        y += 30;
    }

    if (player.speedBoostTime > 0) {
        ctx.fillStyle = COLORS.PURPLE;
        ctx.font = 'bold 16px Arial';
        ctx.fillText('⚡ SPEED', 20, y);
        y += 30;
    }

    if (player.doubleJumpTime > 0) {
        ctx.fillStyle = COLORS.GOLD;
        ctx.font = 'bold 16px Arial';
        ctx.fillText('🔆 2-JUMP', 20, y);
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
    gameState = GAME_STATE.DIFFICULTY_SELECT;
    showModal('menu-modal');
}

// Entity Classes

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

        // Power-ups
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
            } else if (this.doubleJumpAvailable && this.doubleJumpTime > 0) {
                this.velY = JUMP_STRENGTH;
                this.doubleJumpAvailable = false;
            }
        }
    }

    update(platforms, enemies, coins, powerUps) {
        // Update timers
        this.speedBoostTime = Math.max(0, this.speedBoostTime - 1);
        this.doubleJumpTime = Math.max(0, this.doubleJumpTime - 1);
        this.invincibleTime = Math.max(0, this.invincibleTime - 1);
        this.invulnerable = Math.max(0, this.invulnerable - 1);

        // Gravity
        this.velY += GRAVITY;
        this.velY = Math.min(this.velY, 15);

        // Horizontal movement
        this.x += this.velX;
        if (this.x < 0) this.x = 0;
        if (this.x + this.width > SCREEN_WIDTH) this.x = SCREEN_WIDTH - this.width;

        // Vertical movement
        this.y += this.velY;
        this.onGround = false;

        // Platform collision
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

        // Enemy collision
        enemies.forEach(e => {
            if (this.collidesWith(e) && this.invulnerable <= 0 && this.invincibleTime <= 0) {
                this.takeDamage();
            }
        });

        // Power-up collection
        powerUps = powerUps.filter(p => {
            if (this.collidesWith(p)) {
                this.applyPowerUp(p.type);
                return false;
            }
            return true;
        });

        // Coin collection
        coins = coins.filter(c => {
            if (this.collidesWith(c)) {
                return false;
            }
            return true;
        });

        // Death by falling
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
            // Player body
            ctx.fillStyle = COLORS.SAFFRON;
            ctx.fillRect(this.x, this.y, this.width, this.height);

            // Turban
            ctx.fillStyle = COLORS.GOLD;
            ctx.beginPath();
            ctx.moveTo(this.x + 5, this.y + 5);
            ctx.lineTo(this.x + 15, this.y - 5);
            ctx.lineTo(this.x + 25, this.y + 5);
            ctx.fill();

            // Eyes
            ctx.fillStyle = COLORS.DEEP_BLUE;
            const eyeY = this.y + 12;
            if (this.facingRight) {
                ctx.beginPath();
                ctx.arc(this.x + 10, eyeY, 3, 0, Math.PI * 2);
                ctx.fill();
                ctx.beginPath();
                ctx.arc(this.x + 22, eyeY, 3, 0, Math.PI * 2);
                ctx.fill();
            } else {
                ctx.beginPath();
                ctx.arc(this.x + 30, eyeY, 3, 0, Math.PI * 2);
                ctx.fill();
                ctx.beginPath();
                ctx.arc(this.x + 18, eyeY, 3, 0, Math.PI * 2);
                ctx.fill();
            }

            // Shield effect
            if (this.hasShield) {
                ctx.strokeStyle = COLORS.LIGHT_GREEN;
                ctx.lineWidth = 3;
                ctx.beginPath();
                ctx.arc(this.x + this.width / 2, this.y + this.height / 2, 25, 0, Math.PI * 2);
                ctx.stroke();
            }

            // Speed boost aura
            if (this.speedBoostTime > 0) {
                ctx.strokeStyle = COLORS.PURPLE;
                ctx.lineWidth = 2;
                ctx.beginPath();
                ctx.arc(this.x + this.width / 2, this.y + this.height / 2, 28, 0, Math.PI * 2);
                ctx.stroke();
            }

            // Invincible aura
            if (this.invincibleTime > 0) {
                ctx.strokeStyle = COLORS.GOLD;
                ctx.lineWidth = 3;
                ctx.beginPath();
                ctx.arc(this.x + this.width / 2, this.y + this.height / 2, 30, 0, Math.PI * 2);
                ctx.stroke();
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
    }

    update() {
        this.x += this.velX;

        if (this.x < this.startX - this.patrolRange) {
            this.velX = this.speed;
        } else if (this.x > this.startX + this.patrolRange) {
            this.velX = -this.speed;
        }
    }

    draw(ctx) {
        ctx.fillStyle = COLORS.DARK_RED;
        ctx.fillRect(this.x, this.y, this.width, this.height);

        // Eyes
        ctx.fillStyle = COLORS.GOLD;
        ctx.beginPath();
        ctx.arc(this.x + 8, this.y + 8, 3, 0, Math.PI * 2);
        ctx.fill();
        ctx.beginPath();
        ctx.arc(this.x + 27, this.y + 8, 3, 0, Math.PI * 2);
        ctx.fill();
    }
}

class Coin {
    constructor(x, y) {
        this.x = x;
        this.y = y;
        this.width = 20;
        this.height = 20;
        this.rotation = 0;
    }

    update() {
        this.rotation = (this.rotation + 5) % 360;
        this.y += Math.sin(this.rotation * Math.PI / 180) * 0.1;
    }

    draw(ctx) {
        ctx.fillStyle = COLORS.GOLD;
        ctx.beginPath();
        ctx.arc(this.x + this.width / 2, this.y + this.height / 2, 10, 0, Math.PI * 2);
        ctx.fill();

        ctx.fillStyle = COLORS.SAFFRON;
        ctx.beginPath();
        ctx.arc(this.x + this.width / 2, this.y + this.height / 2, 7, 0, Math.PI * 2);
        ctx.fill();
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
    }

    update() {
        this.rotation = (this.rotation + 5) % 360;
        this.y += Math.sin(this.rotation * Math.PI / 180) * 0.3;
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
        const size = 12;
        const centerX = this.x + this.width / 2;
        const centerY = this.y + this.height / 2;

        ctx.fillStyle = this.getColor();
        ctx.beginPath();
        for (let i = 0; i < 5; i++) {
            const angle = (i * 4 + this.rotation) * Math.PI / 180;
            const px = centerX + size * Math.cos(angle);
            const py = centerY + size * Math.sin(angle);
            if (i === 0) ctx.moveTo(px, py);
            else ctx.lineTo(px, py);
        }
        ctx.closePath();
        ctx.fill();
    }
}

class Platform {
    constructor(x, y, width, height, color) {
        this.x = x;
        this.y = y;
        this.width = width;
        this.height = height;
        this.color = color;
    }

    draw(ctx) {
        ctx.fillStyle = this.color;
        ctx.fillRect(this.x, this.y, this.width, this.height);

        if (this.width > 50) {
            ctx.fillStyle = COLORS.SAFFRON;
            for (let i = 0; i < this.width; i += 30) {
                ctx.beginPath();
                ctx.arc(this.x + i, this.y + 5, 3, 0, Math.PI * 2);
                ctx.fill();
            }
        }
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
    }

    update() {
        this.x += this.velX;
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
            ctx.fillStyle = COLORS.DARK_RED;
            ctx.fillRect(this.x, this.y, this.width, this.height);

            // Crown
            ctx.fillStyle = COLORS.GOLD;
            ctx.beginPath();
            ctx.moveTo(this.x + 25, this.y + 5);
            ctx.lineTo(this.x + 15, this.y - 15);
            ctx.lineTo(this.x + 40, this.y + 5);
            ctx.lineTo(this.x + 55, this.y - 15);
            ctx.lineTo(this.x + 55, this.y + 5);
            ctx.fill();

            // Eyes
            ctx.fillStyle = COLORS.GOLD;
            ctx.beginPath();
            ctx.arc(this.x + 20, this.y + 25, 4, 0, Math.PI * 2);
            ctx.fill();
            ctx.beginPath();
            ctx.arc(this.x + 60, this.y + 25, 4, 0, Math.PI * 2);
            ctx.fill();
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
        ctx.beginPath();
        ctx.arc(this.x, this.y, 5, 0, Math.PI * 2);
        ctx.fill();
    }
}

// Start game when page loads
document.addEventListener('DOMContentLoaded', init);
