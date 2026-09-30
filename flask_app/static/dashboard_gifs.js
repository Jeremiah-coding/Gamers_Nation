(() => {
    const durationCache = new Map();
    const FADE_MS = 2100;
    const QUOTE_MIN_DISPLAY_MS = 6000;
    const QUOTES = [
        { text: "A Lesson Without Pain Is Meaningless.", author: "Edward Elric" },
        { text: "If You Don’t Take Risks, You Can’t Create A Future.", author: "Monkey D. Luffy" },
        { text: "Believe In The Me That Believes In You!", author: "Kamina" },
        { text: "Set Your Heart Ablaze.", author: "Kyojuro Rengoku" },
        { text: "If You Feel Yourself Hitting Up Against Your Limit, Remember For What Cause You Clench Your Fists.", author: "All Might" },
        { text: "The World Isn’t Perfect. But It’s There For Us, Doing The Best It Can.", author: "Roy Mustang" },
        { text: "When Do You Think People Die? When They Are Forgotten.", author: "Dr. Hiriluk" },
        { text: "No Matter How Deep The Night, It Always Turns To Day, Eventually.", author: "Brook" },
        { text: "A Person Grows Up When He’s Able To Overcome Hardships.", author: "Jiraiya" },
        { text: "Knowing You’re Different Is Only The Beginning.", author: "Miss Kobayashi" },
        { text: "It’s Okay To Lose Your Way. Just Don’t Lose Yourself.", author: "Roronoa Zoro" },
        { text: "Sometimes You Must Hurt In Order To Know, Fall In Order To Grow.", author: "Pain" },
        { text: "The Moment You Think Of Giving Up, Think Of The Reason Why You Held On So Long.", author: "Natsu Dragneel" },
        { text: "Push Through The Pain. Giving Up Hurts More.", author: "Vegeta" },
        { text: "Whatever You Lose, You’ll Find It Again. But What You Throw Away You’ll Never Get Back.", author: "Kenshin Himura" },
        { text: "I Want To Live!", author: "Nico Robin" },
        { text: "Nobody In This World Is Born Alone!", author: "Jaguar D. Sol" },
        { text: "You CAN Do It!", author: "Weiss Schnee" }
    ];

    function chooseGif(urls, currentUrl) {
        let choices = urls.filter((url) => url !== currentUrl);
        if (!choices.length) choices = urls;
        return choices[Math.floor(Math.random() * choices.length)];
    }

    function parseGifDuration(buffer) {
        const bytes = new Uint8Array(buffer);
        const view = new DataView(buffer);
        if (bytes.length < 13 || String.fromCharCode(...bytes.slice(0, 3)) !== "GIF") return 6;

        let offset = 13;
        const screenFlags = bytes[10];
        if (screenFlags & 0x80) offset += 3 * (2 ** ((screenFlags & 0x07) + 1));
        let durationMs = 0;
        let frameCount = 0;

        while (offset < bytes.length) {
            const marker = bytes[offset++];
            if (marker === 0x3b) break;

            if (marker === 0x21) {
                const label = bytes[offset++];
                if (label === 0xf9) {
                    const blockSize = bytes[offset++];
                    if (blockSize >= 4 && offset + blockSize <= bytes.length) {
                        const delay = view.getUint16(offset + 1, true) * 10;
                        durationMs += delay;
                        frameCount += 1;
                    }
                    offset += blockSize;
                    if (bytes[offset] === 0) offset += 1;
                } else {
                    while (offset < bytes.length) {
                        const blockSize = bytes[offset++];
                        if (blockSize === 0) break;
                        offset += blockSize;
                    }
                }
                continue;
            }

            if (marker === 0x2c) {
                if (offset + 9 > bytes.length) break;
                const imageFlags = bytes[offset + 8];
                offset += 9;
                if (imageFlags & 0x80) offset += 3 * (2 ** ((imageFlags & 0x07) + 1));
                offset += 1;
                while (offset < bytes.length) {
                    const blockSize = bytes[offset++];
                    if (blockSize === 0) break;
                    offset += blockSize;
                }
                continue;
            }

            break;
        }

        if (!frameCount || !durationMs) return 6;
        return Math.max(1.5, Math.min(durationMs / 1000, 120));
    }

    function getGifDuration(url) {
        if (!durationCache.has(url)) {
            const duration = fetch(url, { cache: "force-cache" })
                .then((response) => {
                    if (!response.ok) throw new Error("Unable to read GIF metadata");
                    return response.arrayBuffer();
                })
                .then(parseGifDuration)
                .catch(() => 6);
            durationCache.set(url, duration);
        }
        return durationCache.get(url);
    }

    function loadImage(image, url) {
        return new Promise((resolve) => {
            const finish = () => resolve(image.naturalWidth > 0);
            image.onload = finish;
            image.onerror = () => resolve(false);
            image.src = url;
            if (image.complete) finish();
        });
    }

    function startRotator(stage) {
        const image = stage.querySelector(".dashboard-rotating-gif");
        const urls = (stage.dataset.gifs || "").split(",").filter(Boolean);
        if (!image || !urls.length) {
            stage.hidden = true;
            return;
        }

        let currentUrl = "";
        let timer = null;
        let active = true;
        const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
        const fadeMs = prefersReducedMotion ? 300 : FADE_MS;

        async function showNext(firstImage = false) {
            if (!active) return;
            const nextUrl = chooseGif(urls, currentUrl);
            currentUrl = nextUrl;

            if (!firstImage) {
                image.classList.remove("is-visible");
                await new Promise((resolve) => window.setTimeout(resolve, fadeMs));
                if (!active) return;
            }

            image.dataset.currentUrl = nextUrl;
            const loaded = await loadImage(image, nextUrl);
            if (!active) return;
            if (!loaded) {
                timer = window.setTimeout(() => showNext(false), 250);
                return;
            }

            image.classList.add("is-visible");
            const duration = await getGifDuration(nextUrl);
            if (!active) return;
            timer = window.setTimeout(() => showNext(false), duration * 1000);
        }

        showNext(true);
        window.addEventListener("pagehide", () => {
            active = false;
            if (timer) window.clearTimeout(timer);
        }, { once: true });
    }

    const leftStage = document.querySelector(".left-pic-container.dashboard-gif-stage");
    const rightStage = document.querySelector(".dashboard-quote-stage");
    const leftImage = leftStage?.querySelector(".dashboard-rotating-gif");
    const quote = rightStage?.querySelector(".dashboard-quote");
    if (!leftStage || !rightStage || !leftImage || !quote) {
        document.querySelectorAll(".dashboard-gif-stage").forEach((stage) => startRotator(stage));
        return;
    }

    const quoteText = quote.querySelector(".dashboard-quote-text");
    const quoteAuthor = quote.querySelector(".dashboard-quote-author");
    const urls = (leftStage.dataset.gifs || "").split(",").filter(Boolean);
    if (!urls.length) {
        leftStage.hidden = true;
        rightStage.hidden = true;
        return;
    }

    let currentUrl = "";
    let currentQuoteIndex = -1;
    let timer = null;
    let active = true;
    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const fadeMs = prefersReducedMotion ? 300 : FADE_MS;

    async function showNext(firstImage = false) {
        if (!active) return;
        const nextUrl = chooseGif(urls, currentUrl);
        currentUrl = nextUrl;
        let nextQuoteIndex = Math.floor(Math.random() * QUOTES.length);
        if (QUOTES.length > 1 && nextQuoteIndex === currentQuoteIndex) {
            nextQuoteIndex = (nextQuoteIndex + 1 + Math.floor(Math.random() * (QUOTES.length - 1))) % QUOTES.length;
        }
        currentQuoteIndex = nextQuoteIndex;
        const nextQuote = QUOTES[nextQuoteIndex];

        if (!firstImage) {
            leftImage.classList.remove("is-visible");
            quote.classList.remove("is-visible");
            await new Promise((resolve) => window.setTimeout(resolve, fadeMs));
            if (!active) return;
        }

        quoteText.textContent = `“${nextQuote.text}”`;
        quoteAuthor.textContent = `— ${nextQuote.author}`;
        leftImage.dataset.currentUrl = nextUrl;
        const loaded = await loadImage(leftImage, nextUrl);
        if (!active) return;
        if (!loaded) {
            timer = window.setTimeout(() => showNext(false), 250);
            return;
        }

        leftImage.classList.add("is-visible");
        quote.classList.add("is-visible");
        const duration = await getGifDuration(nextUrl);
        if (!active) return;
        timer = window.setTimeout(() => showNext(false), Math.max(duration * 1000, QUOTE_MIN_DISPLAY_MS));
    }

    showNext(true);
    window.addEventListener("pagehide", () => {
        active = false;
        if (timer) window.clearTimeout(timer);
    }, { once: true });
})();
