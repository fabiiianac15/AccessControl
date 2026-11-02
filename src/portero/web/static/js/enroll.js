// Registro facial: captura muestras de la cámara o de un archivo y deja que el servidor las valide.
(() => {
  "use strict";

  const root = document.getElementById("enroll");
  if (!root) return;
  const personId = root.dataset.person;
  const csrf = root.dataset.csrf;
  const maxSamples = Number(root.dataset.max);
  const minSamples = Number(root.dataset.min);
  let samples = Number(root.dataset.samples);

  const video = document.getElementById("video");
  const status = document.getElementById("status");
  const counter = document.getElementById("counter");
  const progress = document.getElementById("progress");
  const startButton = document.getElementById("start");
  const fileInput = document.getElementById("file");
  const done = document.getElementById("done");
  const canvas = document.createElement("canvas");

  let capturing = false;
  let timer = null;
  let stream = null;

  function paint() {
    counter.textContent = `${samples} de ${minSamples} muestras mínimas`;
    progress.replaceChildren();
    for (let index = 0; index < minSamples; index += 1) {
      const bar = document.createElement("i");
      if (index < samples) bar.className = "on";
      progress.append(bar);
    }
    done.hidden = samples < minSamples;
  }

  async function send(blob) {
    const response = await fetch(`/api/personas/${personId}/muestras`, {
      method: "POST",
      headers: { "X-CSRF-Token": csrf, "Content-Type": blob.type || "image/jpeg" },
      body: blob,
    });
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw new Error(body.detail || "El servidor rechazó la imagen");
    }
    return response.json();
  }

  function stop() {
    capturing = false;
    clearTimeout(timer);
    startButton.textContent = "Iniciar captura";
    if (stream) stream.getTracks().forEach((track) => track.stop());
    stream = null;
    video.srcObject = null;
  }

  async function step() {
    if (!capturing) return;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    let wait = 500;
    if (canvas.width) {
      canvas.getContext("2d").drawImage(video, 0, 0);
      const blob = await new Promise((resolve) => canvas.toBlob(resolve, "image/jpeg", 0.92));
      try {
        const result = await send(blob);
        status.textContent = result.message;
        samples = result.samples;
        paint();
        if (result.accepted) {
          status.textContent = "Muestra guardada. Mueve un poco la cabeza.";
          wait = 900;
        }
        if (samples >= maxSamples || result.code === "full" || samples >= minSamples + 2) {
          status.textContent = "Listo. Las muestras quedaron guardadas.";
          stop();
          return;
        }
        if (result.code === "duplicate" || result.code === "no_consent") {
          stop();
          return;
        }
      } catch (error) {
        status.textContent = error.message;
        stop();
        return;
      }
    }
    timer = setTimeout(step, wait);
  }

  startButton.addEventListener("click", async () => {
    if (capturing) {
      stop();
      return;
    }
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      status.textContent = "Este navegador no permite la cámara aquí (necesita HTTPS o localhost). Sube una foto.";
      return;
    }
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 1280 }, height: { ideal: 720 }, facingMode: "user" },
        audio: false,
      });
    } catch {
      status.textContent = "No hay acceso a la cámara. Revisa el permiso del navegador o sube una foto.";
      return;
    }
    video.srcObject = stream;
    capturing = true;
    startButton.textContent = "Detener";
    status.textContent = "Mira a la cámara";
    timer = setTimeout(step, 700);
  });

  fileInput.addEventListener("change", async () => {
    for (const file of fileInput.files) {
      try {
        const result = await send(file);
        samples = result.samples;
        status.textContent = `${file.name}: ${result.message}`;
        paint();
      } catch (error) {
        status.textContent = `${file.name}: ${error.message}`;
      }
    }
    fileInput.value = "";
  });

  paint();
})();
