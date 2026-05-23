(function () {
    const STORAGE_KEY = "gn_music_state_v1";
    const DEFAULT_STATE = {
        trackIndex: 0,
        currentTime: 0,
        isPaused: false,
        isShuffle: false,
        isRepeat: false,
        lastUpdated: 0
    };

    const PLAYLIST = [
        { id: "9DhpmtyzQd8", title: "Akihibara", artist: "Venny" },
        { id: "kkvJhbmqMmg", title: "FineLine (Instrumental)", artist: "Harry Styles" },
        { id: "Out8v0sS5ZM", title: "Calm", artist: "Vex King" },
        { id: "Jha6Rqq_88w", title: "My Dark Fantasy (Slowed)", artist: "Rexlity" },
        { id: "RZVlwTEdlEA", title: "Firefly City", artist: "Yuforia" }
    ];

    let player = null;
    let state = loadState();
    let initialized = false;
    let updateTimer = null;
    let currentTrackIndex = normalizeTrackIndex(state.trackIndex);
    let isSwitchingTrack = false;
    let optionsRef = null;

    function loadState() {
        try {
            const raw = localStorage.getItem(STORAGE_KEY);
            if (!raw) {
                return { ...DEFAULT_STATE };
            }
            const parsed = JSON.parse(raw);
            return {
                ...DEFAULT_STATE,
                ...parsed,
                trackIndex: normalizeTrackIndex(parsed.trackIndex),
                currentTime: Number(parsed.currentTime) || 0
            };
        } catch (err) {
            return { ...DEFAULT_STATE };
        }
    }

    function saveState() {
        try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
        } catch (err) {
            // Ignore storage issues gracefully.
        }
    }

    function normalizeTrackIndex(index) {
        const i = Number(index);
        if (Number.isNaN(i) || i < 0 || i >= PLAYLIST.length) {
            return 0;
        }
        return i;
    }

    function shouldStopForPath(pathname) {
        const isVideogameDetail = /^\/videogames\/\d+$/.test(pathname);
        const isStudy = pathname === "/study";
        const isTwitchApi = pathname === "/oauth/callback" || pathname === "/videogames/igdb/login";
        return isVideogameDetail || isStudy || isTwitchApi;
    }

    function loadYouTubeApi() {
        return new Promise((resolve) => {
            if (window.YT && window.YT.Player) {
                resolve();
                return;
            }

            const existing = document.getElementById("yt-iframe-api-global");
            if (!existing) {
                const script = document.createElement("script");
                script.id = "yt-iframe-api-global";
                script.src = "https://www.youtube.com/iframe_api";
                document.head.appendChild(script);
            }

            const checkReady = () => {
                if (window.YT && window.YT.Player) {
                    resolve();
                } else {
                    setTimeout(checkReady, 120);
                }
            };
            checkReady();
        });
    }

    function ensurePlayerMount() {
        let mount = document.getElementById("global-music-player");
        if (!mount) {
            mount = document.createElement("div");
            mount.id = "global-music-player";
            mount.style.position = "fixed";
            mount.style.width = "1px";
            mount.style.height = "1px";
            mount.style.opacity = "0";
            mount.style.pointerEvents = "none";
            mount.style.left = "-9999px";
            mount.style.top = "-9999px";
            document.body.appendChild(mount);
        }
        return mount;
    }

    function showToast(track) {
        if (!optionsRef || !optionsRef.toastSelector) {
            return;
        }

        const toast = document.querySelector(optionsRef.toastSelector);
        if (!toast) {
            return;
        }

        const titleEl = toast.querySelector(".music-toast-title");
        const artistEl = toast.querySelector(".music-toast-artist");
        if (titleEl) {
            titleEl.textContent = track.title;
        }
        if (artistEl) {
            artistEl.textContent = track.artist;
        }

        toast.classList.remove("is-visible");
        void toast.offsetWidth;
        toast.classList.add("is-visible");

        setTimeout(() => {
            toast.classList.remove("is-visible");
        }, 5600);
    }

    function setNowPlaying(track) {
        if (!optionsRef) {
            return;
        }
        if (optionsRef.titleSelector) {
            const titleNode = document.querySelector(optionsRef.titleSelector);
            if (titleNode) {
                titleNode.textContent = track.title;
            }
        }
        if (optionsRef.artistSelector) {
            const artistNode = document.querySelector(optionsRef.artistSelector);
            if (artistNode) {
                artistNode.textContent = track.artist;
            }
        }
    }

    function syncUiState() {
        if (!optionsRef) {
            return;
        }

        if (optionsRef.selectSelector) {
            const select = document.querySelector(optionsRef.selectSelector);
            if (select) {
                select.value = String(currentTrackIndex);
            }
        }

        if (optionsRef.pauseSelector) {
            const pauseBtn = document.querySelector(optionsRef.pauseSelector);
            if (pauseBtn) {
                pauseBtn.textContent = state.isPaused ? "Play" : "Pause";
            }
        }

        if (optionsRef.shuffleSelector) {
            const shuffleBtn = document.querySelector(optionsRef.shuffleSelector);
            if (shuffleBtn) {
                shuffleBtn.classList.toggle("is-active", state.isShuffle);
            }
        }

        if (optionsRef.repeatSelector) {
            const repeatBtn = document.querySelector(optionsRef.repeatSelector);
            if (repeatBtn) {
                repeatBtn.classList.toggle("is-active", state.isRepeat);
            }
        }
    }

    function playCurrentTrack(forceRestart) {
        if (!player || typeof player.loadVideoById !== "function") {
            return;
        }

        const track = PLAYLIST[currentTrackIndex];
        const startSeconds = forceRestart ? 0 : Math.floor(Math.max(0, state.currentTime || 0));
        isSwitchingTrack = true;
        player.loadVideoById({
            videoId: track.id,
            startSeconds: startSeconds
        });
        state.currentTime = startSeconds;
        state.isPaused = false;
        state.trackIndex = currentTrackIndex;
        state.lastUpdated = Date.now();
        saveState();
        setNowPlaying(track);
        showToast(track);
        syncUiState();
    }

    function jumpToTrack(index, forceRestart) {
        currentTrackIndex = normalizeTrackIndex(index);
        playCurrentTrack(Boolean(forceRestart));
    }

    function pickNextTrackIndex() {
        if (state.isShuffle) {
            if (PLAYLIST.length <= 1) {
                return currentTrackIndex;
            }
            let next = currentTrackIndex;
            while (next === currentTrackIndex) {
                next = Math.floor(Math.random() * PLAYLIST.length);
            }
            return next;
        }
        return (currentTrackIndex + 1) % PLAYLIST.length;
    }

    function handleTrackEnd() {
        if (state.isRepeat) {
            jumpToTrack(currentTrackIndex, true);
            return;
        }
        jumpToTrack(pickNextTrackIndex(), true);
    }

    function bindUiHandlers() {
        if (!optionsRef) {
            return;
        }

        if (optionsRef.selectSelector) {
            const select = document.querySelector(optionsRef.selectSelector);
            if (select && !select.dataset.musicBound) {
                select.dataset.musicBound = "1";
                select.innerHTML = "";
                PLAYLIST.forEach((track, idx) => {
                    const option = document.createElement("option");
                    option.value = String(idx);
                    option.textContent = `${track.title} - ${track.artist}`;
                    select.appendChild(option);
                });
                select.addEventListener("change", () => {
                    const chosen = Number(select.value);
                    jumpToTrack(chosen, true);
                });
            }
        }

        if (optionsRef.pauseSelector) {
            const pauseBtn = document.querySelector(optionsRef.pauseSelector);
            if (pauseBtn && !pauseBtn.dataset.musicBound) {
                pauseBtn.dataset.musicBound = "1";
                pauseBtn.addEventListener("click", () => {
                    if (!player || typeof player.pauseVideo !== "function") {
                        return;
                    }
                    if (state.isPaused) {
                        player.playVideo();
                        state.isPaused = false;
                    } else {
                        player.pauseVideo();
                        state.isPaused = true;
                    }
                    state.lastUpdated = Date.now();
                    saveState();
                    syncUiState();
                });
            }
        }

        if (optionsRef.restartSelector) {
            const restartBtn = document.querySelector(optionsRef.restartSelector);
            if (restartBtn && !restartBtn.dataset.musicBound) {
                restartBtn.dataset.musicBound = "1";
                restartBtn.addEventListener("click", () => {
                    jumpToTrack(currentTrackIndex, true);
                });
            }
        }

        if (optionsRef.shuffleSelector) {
            const shuffleBtn = document.querySelector(optionsRef.shuffleSelector);
            if (shuffleBtn && !shuffleBtn.dataset.musicBound) {
                shuffleBtn.dataset.musicBound = "1";
                shuffleBtn.addEventListener("click", () => {
                    state.isShuffle = !state.isShuffle;
                    saveState();
                    syncUiState();
                });
            }
        }

        if (optionsRef.repeatSelector) {
            const repeatBtn = document.querySelector(optionsRef.repeatSelector);
            if (repeatBtn && !repeatBtn.dataset.musicBound) {
                repeatBtn.dataset.musicBound = "1";
                repeatBtn.addEventListener("click", () => {
                    state.isRepeat = !state.isRepeat;
                    saveState();
                    syncUiState();
                });
            }
        }
    }

    function pauseForContext() {
        if (!player || typeof player.pauseVideo !== "function") {
            return;
        }
        state.currentTime = Number(player.getCurrentTime ? player.getCurrentTime() : state.currentTime) || 0;
        state.isPaused = true;
        state.lastUpdated = Date.now();
        saveState();
        player.pauseVideo();
        syncUiState();
    }

    function startProgressSync() {
        if (updateTimer) {
            clearInterval(updateTimer);
        }
        updateTimer = setInterval(() => {
            if (!player || typeof player.getPlayerState !== "function") {
                return;
            }
            const stateCode = player.getPlayerState();
            if (stateCode === 1) {
                state.currentTime = Number(player.getCurrentTime()) || state.currentTime;
                state.trackIndex = currentTrackIndex;
                state.isPaused = false;
                state.lastUpdated = Date.now();
                saveState();
            }
        }, 1000);
    }

    function initPlayer(stopOnLoad) {
        const mount = ensurePlayerMount();

        player = new window.YT.Player(mount, {
            videoId: PLAYLIST[currentTrackIndex].id,
            playerVars: {
                autoplay: stopOnLoad ? 0 : 1,
                controls: 0,
                rel: 0,
                modestbranding: 1,
                playsinline: 1
            },
            events: {
                onReady: function (event) {
                    setNowPlaying(PLAYLIST[currentTrackIndex]);
                    syncUiState();
                    bindUiHandlers();
                    startProgressSync();

                    if (stopOnLoad) {
                        pauseForContext();
                        return;
                    }

                    if (state.currentTime > 0) {
                        event.target.seekTo(Math.floor(state.currentTime), true);
                    }

                    if (!state.isPaused) {
                        event.target.playVideo();
                        showToast(PLAYLIST[currentTrackIndex]);
                    }
                },
                onStateChange: function (event) {
                    if (event.data === 0) {
                        handleTrackEnd();
                        return;
                    }

                    if (event.data === 1) {
                        if (isSwitchingTrack) {
                            isSwitchingTrack = false;
                        }
                        state.isPaused = false;
                        state.trackIndex = currentTrackIndex;
                        state.lastUpdated = Date.now();
                        saveState();
                        syncUiState();
                    }

                    if (event.data === 2) {
                        state.isPaused = true;
                        state.currentTime = Number(player.getCurrentTime ? player.getCurrentTime() : state.currentTime) || 0;
                        state.lastUpdated = Date.now();
                        saveState();
                        syncUiState();
                    }
                }
            }
        });
    }

    function init(options) {
        if (initialized) {
            return;
        }
        initialized = true;

        optionsRef = options || {};
        const pathname = window.location.pathname || "";
        const stopOnLoad = Boolean(optionsRef.stopOnLoad) || shouldStopForPath(pathname);

        currentTrackIndex = normalizeTrackIndex(state.trackIndex);
        bindUiHandlers();
        syncUiState();
        setNowPlaying(PLAYLIST[currentTrackIndex]);

        loadYouTubeApi().then(() => {
            initPlayer(stopOnLoad);
        });

        window.addEventListener("beforeunload", () => {
            if (player && typeof player.getCurrentTime === "function") {
                state.currentTime = Number(player.getCurrentTime()) || state.currentTime;
                state.trackIndex = currentTrackIndex;
                state.lastUpdated = Date.now();
                saveState();
            }
        });
    }

    window.GNMusic = {
        init: init
    };
})();
