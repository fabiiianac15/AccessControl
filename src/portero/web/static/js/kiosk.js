// Cliente del kiosco: envía cuadros al servidor y muestra lo que este decide.
// Aquí no hay lógica de acceso. Solo video, mensajes y el teclado de PIN.
(() => {
  "use strict";

  const STORAGE_KEY = "portero.kiosk.token";
  const FRAME_INTERVAL_MS = 260;
  const PIN_LENGTH = 6;
  const PIN_IDLE_MS = 20000;

  const $ = (id) => document.getElementById(id);
  const stage = $("stage");
  const setup = $("setup");
  const video = $("video");
  const title = $("title");
  const subtitle = $("subtitle");
  const steps = $("steps");
  const padWrap = $("pad-wrap");
  const dots = $("dots");
  const pinToggle = $("pin-toggle");

  const canvas = document.createElement("canvas");
  let token = null;
  let pin = "";
  let pinOpen = false;
  let pinTimer = null;
  let sending = false;
  let holdUntil = 0;

  function readToken() {
    const match = location.hash.match(/token=([\w-]+)/);
    try {
      if (match) {
        localStorage.setItem(STORAGE_KEY, match[1]);
        history.replaceState(null, "", location.pathname);
        return match[1];
      }
      return localStorage.getItem(STORAGE_KEY);
    } catch {
      return match ? match[1] : null;
    }
  }

  function showSetup(heading, text) {
    stage.hidden = true;
    setup.hidden = false;
    $("setup-title").textContent = heading;
    $("setup-text").textContent = text;
  }

  function api(path, options = {}) {
    return fetch(path, {
      ...options,
      headers: { ...(options.headers || {}), Authorization: `Bearer ${token}` },
    });
  }

  function setPhase(phase, direction = "") {
    document.body.dataset.phase = phase;
    document.body.dataset.direction = direction;
  }

  function setMessage(main, secondary = "") {
    if (title.textContent !== main) title.textContent = main;
    subtitle.textContent = secondary;
  }

  function renderSteps(current, total) {
    steps.replaceChildren();
    for (let index = 1; index <= (total || 0); index += 1) {
      const dot = document.createElement("i");
      if (index <= current) dot.className = "on";
      steps.append(dot);
    }
  }

  function render(state) {
    if (state.phase === "result") {
      setPhase(state.granted ? "granted" : "denied");
      renderSteps(0, 0);
      const heading = state.granted
        ? `Hola, ${state.name}`
        : state.name ? `${state.name}, acceso denegado` : "Acceso denegado";
      let detail = state.granted ? "Puedes pasar" : state.message;
      if (state.granted && state.door === "failed") {
        detail = "La puerta no respondió. Avisa a administración";
      }
      setMessage(heading, detail);
      holdUntil = performance.now() + 3500;
      closePin();
      return;
    }
    if (state.phase === "challenge") {
      setPhase("challenge", state.direction === "center" ? "" : state.direction);
      setMessage(state.message);
      renderSteps(state.step - 1, state.total);
      return;
    }
    if (state.phase === "pin_locked") {
      setPhase("denied");
      setMessage("PIN bloqueado", `Intenta de nuevo en ${state.retry_in} segundos`);
      holdUntil = performance.now() + 3500;
      closePin();
      return;
    }
    setPhase("guide");
    renderSteps(0, 0);
    setMessage(state.message);
  }

  function captureBlob() {
    const width = video.videoWidth;
    const height = video.videoHeight;
    if (!width) return Promise.resolve(null);
    const scale = Math.min(1, 640 / Math.max(width, height));
    canvas.width = Math.round(width * scale);
    canvas.height = Math.round(height * scale);
    canvas.getContext("2d").drawImage(video, 0, 0, canvas.width, canvas.height);
    return new Promise((resolve) => canvas.toBlob(resolve, "image/jpeg", 0.85));
  }

  async function tick() {
    const now = performance.now();
    if (sending || pinOpen || now < holdUntil || document.hidden) return;
    sending = true;
    try {
      const blob = await captureBlob();
      if (!blob) return;
      const response = await api("/api/kiosk/v1/frame", {
        method: "POST",
        headers: { "Content-Type": "image/jpeg" },
        body: blob,
      });
      if (response.status === 401) {
        try { localStorage.removeItem(STORAGE_KEY); } catch { /* sin almacenamiento */ }
        showSetup("Kiosco desvinculado", "Pide a administración un nuevo enlace.");
        return;
      }
      if (!response.ok) throw new Error(String(response.status));
      render(await response.json());
    } catch {
      setPhase("guide");
      setMessage("Sin conexión con el servidor", "Reintentando");
    } finally {
      sending = false;
    }
  }

  function renderDots() {
    dots.replaceChildren();
    for (let index = 0; index < PIN_LENGTH; index += 1) {
      const dot = document.createElement("i");
      if (index < pin.length) dot.className = "on";
      dots.append(dot);
    }
  }

  function armPinTimer() {
    clearTimeout(pinTimer);
    pinTimer = setTimeout(closePin, PIN_IDLE_MS);
  }

  function openPin() {
    pinOpen = true;
    pin = "";
    renderDots();
    padWrap.hidden = false;
    armPinTimer();
  }

  function closePin() {
    pinOpen = false;
    pin = "";
    padWrap.hidden = true;
    clearTimeout(pinTimer);
  }

  async function submitPin() {
    const value = pin;
    closePin();
    setPhase("guide");
    setMessage("Un momento");
    try {
      const response = await api("/api/kiosk/v1/pin", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pin: value }),
      });
      if (!response.ok) throw new Error(String(response.status));
      render(await response.json());
    } catch {
      setPhase("denied");
      setMessage("No se pudo verificar", "Sin conexión con el servidor");
      holdUntil = performance.now() + 3000;
    }
  }

  function pressKey(key) {
    armPinTimer();
    if (key === "back") {
      pin = pin.slice(0, -1);
    } else if (key === "close") {
      closePin();
      return;
    } else if (pin.length < PIN_LENGTH) {
      pin += key;
    }
    renderDots();
    if (pin.length === PIN_LENGTH) submitPin();
  }

  function startClock() {
    const clock = $("clock");
    const format = new Intl.DateTimeFormat("es-CO", { hour: "2-digit", minute: "2-digit" });
    const update = () => { clock.textContent = format.format(new Date()); };
    update();
    setInterval(update, 10000);
  }

  async function start() {
    token = readToken();
    if (!token) {
      showSetup("Kiosco sin vincular", "Abre el enlace que genera el panel en Puertas.");
      return;
    }
    let config;
    try {
      const response = await api("/api/kiosk/v1/config");
      if (response.status === 401) {
        showSetup("Kiosco desvinculado", "Pide a administración un nuevo enlace.");
        return;
      }
      config = await response.json();
    } catch {
      showSetup("Sin conexión", "No se pudo contactar al servidor. Recarga en un momento.");
      return;
    }
    $("kiosk-name").textContent = config.name;
    $("zone-name").textContent = config.zone;
    pinToggle.hidden = !config.allow_pin;
    startClock();

    pinToggle.addEventListener("click", openPin);
    document.querySelectorAll("[data-key]").forEach((button) => {
      button.addEventListener("click", () => pressKey(button.dataset.key));
    });

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setMessage("Este navegador no puede usar la cámara aquí", "Se necesita HTTPS o localhost");
      return;
    }
    try {
      video.srcObject = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 960 }, height: { ideal: 720 }, facingMode: "user" },
        audio: false,
      });
    } catch {
      setMessage("No hay acceso a la cámara", config.allow_pin ? "Puedes entrar con tu PIN" : "");
      return;
    }
    setInterval(tick, FRAME_INTERVAL_MS);
    setMessage("Mira a la cámara");
  }

  start();
})();
