(() => {
    const details = {
        snake: { icon: "🐍", description: "Eat the glowing food, grow your snake, and avoid the walls and your own tail.", instructions: "Use arrow keys or WASD. On phones, use the direction buttons. Each food is 10 points." },
        memory: { icon: "🧠", description: "Flip cards and find all eight matching pairs in as few moves as you can.", instructions: "Select two cards per turn. Your score is higher when you finish in fewer moves." },
        "click-rush": { icon: "⚡", description: "How many targets can you hit before the 15-second timer runs out?", instructions: "Click or tap the glowing target as quickly as you can. Every hit earns one point." },
        frogger: { icon: "🐸", description: "Hop across the traffic lanes and get the frog safely to the other side.", instructions: "Use arrow keys or WASD. On phones, use the direction buttons. Every successful crossing is worth 100 points." },
        "whack-a-mole": { icon: "🔨", description: "Catch the moles whenever they pop up. You have 20 seconds.", instructions: "Tap or click the mole before it moves. Each hit is worth 10 points." },
        pacman: { icon: "👻", description: "Explore a neon maze, gobble every dot, and stay away from the roaming ghosts.", instructions: "Use arrow keys or WASD. On phones, use the direction buttons. Collect dots for 10 points each." }
    };

    const stage = document.getElementById("game-stage");
    const content = document.getElementById("game-content");
    const startButton = document.getElementById("start-game");
    const statusLabel = document.getElementById("stage-status");
    const scoreLabel = document.getElementById("live-score");
    const scoreboard = document.getElementById("score-overlay");
    const topScores = document.getElementById("leaderboard-list");
    let selectedGame = null;
    let timer = null;
    let gameRunning = false;
    let keyboardHandler = null;
    let currentScore = 0;

    document.querySelectorAll("[data-game-card]").forEach((card) => {
        const key = card.dataset.gameCard;
        card.querySelector(".game-card-icon").textContent = details[key].icon;
        card.querySelector(".game-card-copy p").textContent = details[key].description;
        card.querySelector(".game-select").addEventListener("click", () => selectGame(key));
    });

    function selectGame(key) {
        stopGame();
        selectedGame = key;
        document.getElementById("stage-title").textContent = document.querySelector(`[data-game-card="${key}"] h2`).textContent;
        document.getElementById("stage-instructions").textContent = details[key].instructions;
        content.replaceChildren();
        currentScore = 0;
        scoreLabel.textContent = "0";
        statusLabel.textContent = "Ready when you are";
        startButton.hidden = false;
        startButton.textContent = "Start game";
        stage.hidden = false;
        stage.scrollIntoView({ behavior: "smooth", block: "start" });
    }

    function updateScore(value) {
        currentScore = value;
        scoreLabel.textContent = String(value);
    }

    function stopGame() {
        if (timer) {
            clearInterval(timer);
            clearTimeout(timer);
            timer = null;
        }
        if (keyboardHandler) {
            document.removeEventListener("keydown", keyboardHandler);
            keyboardHandler = null;
        }
        gameRunning = false;
    }

    function finishGame(score) {
        if (!gameRunning) return;
        gameRunning = false;
        if (timer) {
            clearInterval(timer);
            clearTimeout(timer);
            timer = null;
        }
        if (keyboardHandler) {
            document.removeEventListener("keydown", keyboardHandler);
            keyboardHandler = null;
        }
        updateScore(score);
        statusLabel.textContent = "Game over — score posted below";
        startButton.hidden = false;
        startButton.textContent = "Play again";
        showScoreboard(score);
    }

    async function showScoreboard(score) {
        document.getElementById("score-title").textContent = `${document.getElementById("stage-title").textContent} scoreboard`;
        document.getElementById("final-score").textContent = String(score);
        document.getElementById("score-save-status").textContent = "Posting your score…";
        topScores.replaceChildren();
        scoreboard.hidden = false;
        document.getElementById("close-score").focus();

        try {
            const response = await fetch("/minigames/scores", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ game: selectedGame, score })
            });
            const result = await response.json();
            if (!response.ok) throw new Error(result.error || "Could not save score.");

            document.getElementById("score-save-status").textContent = "Your score is on the leaderboard!";
            const scores = result.top_scores || [];
            if (!scores.length) {
                const empty = document.createElement("li");
                empty.className = "no-scores";
                empty.textContent = "No scores yet. Be the first!";
                topScores.appendChild(empty);
                return;
            }
            scores.forEach((entry) => {
                const row = document.createElement("li");
                const layout = document.createElement("div");
                const name = document.createElement("span");
                const value = document.createElement("strong");
                layout.className = "leaderboard-row";
                name.textContent = entry.player_name;
                value.textContent = String(entry.score);
                layout.append(name, value);
                row.appendChild(layout);
                topScores.appendChild(row);
            });
        } catch (error) {
            document.getElementById("score-save-status").textContent = error.message || "Could not post the score. Please try again.";
            const message = document.createElement("li");
            message.className = "no-scores";
            message.textContent = "Leaderboard is unavailable right now.";
            topScores.appendChild(message);
        }
    }

    function makeCanvas(helpText) {
        content.innerHTML = `<div><p class="game-help">${helpText}</p><canvas class="game-canvas" width="400" height="400" aria-label="Game play area"></canvas><div class="mobile-controls" aria-label="Direction controls"><button type="button" data-direction="up" aria-label="Up">↑</button><button type="button" data-direction="left" aria-label="Left">←</button><button type="button" data-direction="down" aria-label="Down">↓</button><button type="button" data-direction="right" aria-label="Right">→</button></div></div>`;
        return content.querySelector("canvas");
    }

    function setupDirectionControls(onDirection) {
        const keyMap = { ArrowUp: "up", w: "up", ArrowDown: "down", s: "down", ArrowLeft: "left", a: "left", ArrowRight: "right", d: "right" };
        keyboardHandler = (event) => {
            const direction = keyMap[event.key];
            if (direction && gameRunning) {
                event.preventDefault();
                onDirection(direction);
            }
        };
        document.addEventListener("keydown", keyboardHandler);
        content.querySelectorAll("[data-direction]").forEach((button) => button.addEventListener("click", () => onDirection(button.dataset.direction)));
    }

    function startSnake() {
        const canvas = makeCanvas("Guide the snake with the arrow keys. Eat the pink fruit!");
        const ctx = canvas.getContext("2d");
        const tile = 20;
        let snake = [{ x: 6, y: 10 }, { x: 5, y: 10 }, { x: 4, y: 10 }];
        let direction = { x: 1, y: 0 };
        let nextDirection = direction;
        let food = randomFood();
        let points = 0;

        function randomFood() {
            let spot;
            do { spot = { x: Math.floor(Math.random() * 20), y: Math.floor(Math.random() * 20) }; }
            while (snake.some((part) => part.x === spot.x && part.y === spot.y));
            return spot;
        }
        function draw() {
            ctx.fillStyle = "#0a111b"; ctx.fillRect(0, 0, 400, 400);
            ctx.fillStyle = "#ff69b4"; ctx.beginPath(); ctx.arc(food.x * tile + 10, food.y * tile + 10, 7, 0, Math.PI * 2); ctx.fill();
            snake.forEach((part, index) => { ctx.fillStyle = index === 0 ? "#00ffcc" : "#168f82"; ctx.fillRect(part.x * tile + 2, part.y * tile + 2, tile - 4, tile - 4); });
        }
        function tick() {
            direction = nextDirection;
            const head = { x: snake[0].x + direction.x, y: snake[0].y + direction.y };
            if (head.x < 0 || head.x >= 20 || head.y < 0 || head.y >= 20 || snake.some((part) => part.x === head.x && part.y === head.y)) {
                finishGame(points); return;
            }
            snake.unshift(head);
            if (head.x === food.x && head.y === food.y) { points += 10; updateScore(points); food = randomFood(); }
            else snake.pop();
            draw();
        }
        function setDirection(name) {
            const vector = { up: { x: 0, y: -1 }, down: { x: 0, y: 1 }, left: { x: -1, y: 0 }, right: { x: 1, y: 0 } }[name];
            if (vector.x !== -direction.x || vector.y !== -direction.y) nextDirection = vector;
        }
        draw(); setupDirectionControls(setDirection); timer = setInterval(tick, 125);
    }

    function startMemory() {
        const symbols = ["🎮", "👾", "🕹️", "⭐", "💎", "🚀", "🎲", "🪄"];
        const cards = [...symbols, ...symbols].sort(() => Math.random() - 0.5);
        const grid = document.createElement("div");
        grid.className = "memory-grid";
        content.replaceChildren(grid);
        let first = null; let locked = false; let matched = 0; let moves = 0;
        const buttons = cards.map((symbol, index) => {
            const button = document.createElement("button");
            button.type = "button"; button.className = "memory-card"; button.textContent = "?"; button.setAttribute("aria-label", `Hidden card ${index + 1}`);
            button.addEventListener("click", () => {
                if (locked || button.classList.contains("is-revealed") || button.classList.contains("is-matched")) return;
                button.textContent = symbol; button.classList.add("is-revealed"); button.setAttribute("aria-label", symbol);
                if (!first) { first = { button, symbol }; return; }
                moves += 1; statusLabel.textContent = `Moves: ${moves}`;
                if (first.symbol === symbol) {
                    first.button.classList.add("is-matched"); button.classList.add("is-matched"); matched += 2; first = null;
                    if (matched === cards.length) finishGame(Math.max(100, 1200 - moves * 35));
                } else {
                    locked = true; const previous = first.button; first = null;
                    timer = setTimeout(() => { previous.textContent = "?"; button.textContent = "?"; previous.classList.remove("is-revealed"); button.classList.remove("is-revealed"); previous.setAttribute("aria-label", "Hidden card"); button.setAttribute("aria-label", "Hidden card"); locked = false; timer = null; }, 750);
                }
            });
            grid.appendChild(button); return button;
        });
        statusLabel.textContent = "Moves: 0";
    }

    function startClickRush() {
        content.innerHTML = '<div class="click-arena"><span class="timer-label">Time: <strong id="rush-time">15</strong>s</span><button type="button" class="click-target" aria-label="Tap the target"></button></div>';
        const arena = content.querySelector(".click-arena"); const target = content.querySelector(".click-target");
        let seconds = 15; let points = 0;
        function moveTarget() {
            const maxX = Math.max(0, arena.clientWidth - target.offsetWidth);
            const maxY = Math.max(0, arena.clientHeight - target.offsetHeight);
            target.style.left = `${Math.random() * maxX}px`; target.style.top = `${36 + Math.random() * Math.max(0, maxY - 36)}px`;
        }
        target.addEventListener("click", () => { points += 1; updateScore(points); moveTarget(); });
        moveTarget();
        timer = setInterval(() => { seconds -= 1; document.getElementById("rush-time").textContent = String(seconds); if (seconds <= 0) finishGame(points); }, 1000);
    }

    function startWhack() {
        const grid = document.createElement("div"); grid.className = "mole-grid"; content.replaceChildren(grid);
        const holes = Array.from({ length: 9 }, () => { const hole = document.createElement("button"); hole.type = "button"; hole.className = "mole-hole"; hole.setAttribute("aria-label", "Empty mole hole"); grid.appendChild(hole); return hole; });
        let points = 0; let seconds = 20; let active = -1;
        function popMole() {
            holes.forEach((hole) => { hole.classList.remove("is-active"); hole.textContent = ""; hole.setAttribute("aria-label", "Empty mole hole"); });
            active = Math.floor(Math.random() * holes.length);
            holes[active].classList.add("is-active"); holes[active].textContent = "🐹"; holes[active].setAttribute("aria-label", "Mole! hit it");
        }
        holes.forEach((hole, index) => hole.addEventListener("click", () => {
            if (!gameRunning || index !== active) return;
            points += 10; updateScore(points); popMole();
        }));
        popMole();
        timer = setInterval(() => { seconds -= 1; statusLabel.textContent = `Time left: ${seconds}s`; if (seconds <= 0) finishGame(points); }, 1000);
    }

    function startFrogger() {
        const canvas = makeCanvas("Hop upward through the traffic lanes. Reach the top for 100 points!");
        const ctx = canvas.getContext("2d"); const unit = 40;
        const frog = { x: 5, y: 9 }; let points = 0; let tickCount = 0;
        const lanes = [
            { y: 1, speed: 1, cars: [0, 4, 8] }, { y: 2, speed: -1, cars: [1, 5, 9] },
            { y: 3, speed: 1, cars: [2, 6] }, { y: 5, speed: -1, cars: [0, 4, 8] },
            { y: 6, speed: 1, cars: [1, 5, 9] }, { y: 7, speed: -1, cars: [2, 6] },
            { y: 8, speed: 1, cars: [0, 4, 8] }
        ];
        function draw() {
            for (let row = 0; row < 10; row += 1) {
                ctx.fillStyle = row === 0 || row === 4 || row === 9 ? "#12483d" : "#303744";
                ctx.fillRect(0, row * unit, 400, unit);
                if (row !== 0 && row !== 4 && row !== 9) {
                    ctx.strokeStyle = "rgba(255,255,255,.12)"; ctx.setLineDash([12, 12]); ctx.beginPath(); ctx.moveTo(0, row * unit + 20); ctx.lineTo(400, row * unit + 20); ctx.stroke(); ctx.setLineDash([]);
                }
            }
            lanes.forEach((lane, laneIndex) => lane.cars.forEach((x) => { ctx.fillStyle = laneIndex % 2 ? "#ff69b4" : "#f6c453"; ctx.beginPath(); ctx.roundRect(x * unit + 4, lane.y * unit + 8, 32, 24, 7); ctx.fill(); }));
            ctx.font = "30px sans-serif"; ctx.textAlign = "center"; ctx.textBaseline = "middle"; ctx.fillText("🐸", frog.x * unit + 20, frog.y * unit + 20);
        }
        function checkCollision() {
            const lane = lanes.find((item) => item.y === frog.y);
            if (lane && lane.cars.some((x) => x === frog.x)) { finishGame(points); return true; }
            return false;
        }
        function step() {
            tickCount += 1;
            if (tickCount % 2 === 0) lanes.forEach((lane) => { lane.cars = lane.cars.map((x) => (x + lane.speed + 10) % 10); });
            if (!checkCollision()) draw();
        }
        function moveFrog(direction) {
            if (!gameRunning) return;
            if (direction === "up") frog.y = Math.max(0, frog.y - 1);
            if (direction === "down") frog.y = Math.min(9, frog.y + 1);
            if (direction === "left") frog.x = Math.max(0, frog.x - 1);
            if (direction === "right") frog.x = Math.min(9, frog.x + 1);
            if (frog.y === 0) { points += 100; updateScore(points); frog.x = 5; frog.y = 9; }
            checkCollision(); draw();
        }
        draw(); setupDirectionControls(moveFrog); timer = setInterval(step, 220);
    }

    function startPacman() {
        const canvas = makeCanvas("Collect every dot in the maze and avoid the ghosts!");
        const ctx = canvas.getContext("2d");
        const tile = 25;
        const maze = [
            "###############",
            "#.............#",
            "#.###.###.###.#",
            "#.............#",
            "###.#.###.#.###",
            "#...#.....#...#",
            "#.###.###.###.#",
            "#.............#",
            "#.###.###.###.#",
            "#...#.....#...#",
            "###.#.###.#.###",
            "#.............#",
            "#.###.###.###.#",
            "#.............#",
            "###############"
        ].map((row) => row.split(""));
        const player = { x: 1, y: 1, direction: "right" };
        let queuedDirection = "right";
        const ghosts = [
            { x: 13, y: 13, color: "#ff5a7a" },
            { x: 13, y: 1, color: "#7aa7ff" },
            { x: 1, y: 13, color: "#ff9e5e" }
        ];
        let points = 0;
        let ghostTurn = 0;
        let dotsLeft = maze.reduce((total, row) => total + row.filter((cell) => cell === ".").length, 0);

        function draw() {
            ctx.fillStyle = "#050a15";
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            maze.forEach((row, y) => row.forEach((cell, x) => {
                const left = x * tile;
                const top = y * tile;
                if (cell === "#") {
                    ctx.fillStyle = "#173e94";
                    ctx.fillRect(left + 1, top + 1, tile - 2, tile - 2);
                    ctx.strokeStyle = "#38adff";
                    ctx.lineWidth = 1;
                    ctx.strokeRect(left + 3, top + 3, tile - 6, tile - 6);
                } else if (cell === ".") {
                    ctx.fillStyle = "#ffe9a8";
                    ctx.beginPath();
                    ctx.arc(left + tile / 2, top + tile / 2, 2.4, 0, Math.PI * 2);
                    ctx.fill();
                }
            }));

            ghosts.forEach((ghost) => {
                const centerX = ghost.x * tile + tile / 2;
                const centerY = ghost.y * tile + tile / 2;
                ctx.fillStyle = ghost.color;
                ctx.beginPath();
                ctx.arc(centerX, centerY, tile * 0.39, Math.PI, 0);
                ctx.lineTo(centerX + tile * 0.39, centerY + tile * 0.35);
                ctx.lineTo(centerX + tile * 0.13, centerY + tile * 0.22);
                ctx.lineTo(centerX, centerY + tile * 0.36);
                ctx.lineTo(centerX - tile * 0.13, centerY + tile * 0.22);
                ctx.lineTo(centerX - tile * 0.39, centerY + tile * 0.35);
                ctx.closePath();
                ctx.fill();
                ctx.fillStyle = "#fff";
                ctx.beginPath();
                ctx.arc(centerX - 4, centerY - 2, 3, 0, Math.PI * 2);
                ctx.arc(centerX + 4, centerY - 2, 3, 0, Math.PI * 2);
                ctx.fill();
                ctx.fillStyle = "#172236";
                ctx.beginPath();
                ctx.arc(centerX - 4, centerY - 2, 1.4, 0, Math.PI * 2);
                ctx.arc(centerX + 4, centerY - 2, 1.4, 0, Math.PI * 2);
                ctx.fill();
            });

            const centerX = player.x * tile + tile / 2;
            const centerY = player.y * tile + tile / 2;
            const angles = { right: 0, down: Math.PI / 2, left: Math.PI, up: -Math.PI / 2 };
            ctx.fillStyle = "#ffe35a";
            ctx.beginPath();
            ctx.moveTo(centerX, centerY);
            ctx.arc(centerX, centerY, tile * 0.42, angles[player.direction] + 0.28, angles[player.direction] + Math.PI * 2 - 0.28);
            ctx.closePath();
            ctx.fill();
        }

        function getDestination(actor, direction) {
            const offsets = { up: [0, -1], down: [0, 1], left: [-1, 0], right: [1, 0] };
            const [dx, dy] = offsets[direction];
            return { x: actor.x + dx, y: actor.y + dy };
        }

        function isOpen(position) {
            return maze[position.y]?.[position.x] !== undefined && maze[position.y][position.x] !== "#";
        }

        function moveGhost(ghost) {
            const directions = ["up", "down", "left", "right"];
            const options = directions
                .map((direction) => ({ direction, position: getDestination(ghost, direction) }))
                .filter((option) => isOpen(option.position));
            if (!options.length) return;
            options.sort((a, b) => {
                const distanceA = Math.abs(a.position.x - player.x) + Math.abs(a.position.y - player.y);
                const distanceB = Math.abs(b.position.x - player.x) + Math.abs(b.position.y - player.y);
                return distanceA - distanceB;
            });
            const bestDistance = Math.abs(options[0].position.x - player.x) + Math.abs(options[0].position.y - player.y);
            const bestOptions = options.filter((option) => Math.abs(option.position.x - player.x) + Math.abs(option.position.y - player.y) <= bestDistance + 1);
            const choice = bestOptions[Math.floor(Math.random() * bestOptions.length)];
            ghost.x = choice.position.x;
            ghost.y = choice.position.y;
        }

        function checkCaught() {
            if (ghosts.some((ghost) => ghost.x === player.x && ghost.y === player.y)) {
                finishGame(points);
                return true;
            }
            return false;
        }

        function stepPlayer() {
            if (!gameRunning) return;
            const turn = getDestination(player, queuedDirection);
            if (isOpen(turn)) player.direction = queuedDirection;
            const destination = getDestination(player, player.direction);
            if (!isOpen(destination)) return;
            player.x = destination.x;
            player.y = destination.y;
            if (maze[player.y][player.x] === ".") {
                maze[player.y][player.x] = " ";
                dotsLeft -= 1;
                points += 10;
                updateScore(points);
            }
            if (checkCaught()) return;
            ghostTurn += 1;
            if (ghostTurn % 2 === 0) ghosts.forEach(moveGhost);
            if (checkCaught()) return;
            if (dotsLeft === 0) {
                finishGame(points + 500);
                return;
            }
            draw();
        }

        function queueDirection(direction) {
            queuedDirection = direction;
        }

        canvas.width = 375;
        canvas.height = 375;
        canvas.setAttribute("aria-label", "Pac-Man maze");
        draw();
        setupDirectionControls(queueDirection);
        timer = setInterval(stepPlayer, 150);
    }

    function startGame() {
        if (!selectedGame) return;
        stopGame(); gameRunning = true; updateScore(0); statusLabel.textContent = "Game in progress"; startButton.hidden = true;
        if (selectedGame === "snake") startSnake();
        if (selectedGame === "memory") startMemory();
        if (selectedGame === "click-rush") startClickRush();
        if (selectedGame === "frogger") startFrogger();
        if (selectedGame === "whack-a-mole") startWhack();
        if (selectedGame === "pacman") startPacman();
    }

    function closeScoreboard() { scoreboard.hidden = true; startButton.focus(); }
    startButton.addEventListener("click", startGame);
    document.getElementById("back-to-games").addEventListener("click", () => { stopGame(); stage.hidden = true; document.querySelector(".game-grid").scrollIntoView({ behavior: "smooth" }); });
    document.getElementById("close-score").addEventListener("click", closeScoreboard);
    document.getElementById("close-score-secondary").addEventListener("click", () => { closeScoreboard(); document.getElementById("back-to-games").click(); });
    document.getElementById("play-again").addEventListener("click", () => { closeScoreboard(); startGame(); });
    scoreboard.addEventListener("click", (event) => { if (event.target === scoreboard) closeScoreboard(); });
})();
