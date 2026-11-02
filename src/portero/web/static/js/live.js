// Tablero: agrega a la minuta los eventos nuevos sin recargar la página.
(() => {
  "use strict";

  const body = document.getElementById("live-events");
  if (!body) return;
  let last = Number(body.dataset.last || 0);

  function row(event) {
    const tr = document.createElement("tr");
    tr.className = "is-new";
    const cell = (text, className) => {
      const td = document.createElement("td");
      td.textContent = text;
      if (className) td.className = className;
      return td;
    };
    const status = document.createElement("td");
    const tag = document.createElement("span");
    tag.className = `tag ${event.outcome === "granted" ? "tag-granted" : "tag-denied"}`;
    tag.textContent = event.outcome === "granted" ? "Concedido" : "Denegado";
    status.append(tag);
    tr.append(
      cell(event.time, "time"),
      cell(event.person || "Desconocido"),
      cell(event.zone || "", "hide-sm"),
      status,
      cell(event.reason, "muted small hide-sm"),
    );
    return tr;
  }

  async function poll() {
    if (document.hidden) return;
    try {
      const response = await fetch(`/api/eventos/recientes?desde=${last}`);
      if (!response.ok) return;
      const events = await response.json();
      for (const event of events.reverse()) {
        body.prepend(row(event));
        last = Math.max(last, event.id);
      }
      while (body.children.length > 14) body.lastElementChild.remove();
    } catch {
      // Un corte momentáneo no debe romper el tablero: el siguiente ciclo reintenta.
    }
  }

  setInterval(poll, 4000);
})();
