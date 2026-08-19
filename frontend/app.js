const DEFAULT_STATE = "ESTOU_EM_DUVIDA";
let state = DEFAULT_STATE;

const form = document.getElementById("analysis-form");
const result = document.getElementById("result");
const quickIncident = document.getElementById("incident-quick");
const stateButtons = [...document.querySelectorAll("[data-state]")];

function esc(value) {
  return String(value ?? "").replace(/[&<>\"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;"
  }[char]));
}

function list(title, values) {
  if (!Array.isArray(values) || values.length === 0) return "";
  return `<h3>${esc(title)}</h3><ul>${values.map((item) => `<li>${esc(item)}</li>`).join("")}</ul>`;
}

function selectState(nextState) {
  state = nextState;
  stateButtons.forEach((button) => {
    button.classList.toggle("selected", button.dataset.state === state);
  });
  quickIncident.hidden = state !== "JA_FUI_VITIMA";
  if (state === "JA_FUI_VITIMA") {
    document.getElementById("text").focus();
  }
}

stateButtons.forEach((button) => {
  button.addEventListener("click", () => selectState(button.dataset.state));
});

selectState(DEFAULT_STATE);

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  result.hidden = false;
  result.innerHTML = "<p role=\"status\">Analisando a situação...</p>";

  const body = {
    state,
    text: document.getElementById("text").value,
    url: document.getElementById("url").value.trim() || null,
    situation: document.getElementById("situation").value.trim() || null
  };

  try {
    const response = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    });

    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.detail || "Não foi possível concluir a análise.");

    const risk = esc(String(data.risk_level || "NAO_DETERMINADO").replaceAll("_", " "));
    result.innerHTML = `
      <div class="risk-badge">${risk}</div>
      <h2>Orientação</h2>
      <p>${esc(data.summary)}</p>
      ${list("Sinais encontrados", data.signals)}
      ${list("Evidências", data.evidence)}
      ${list("O que fazer agora", data.safe_actions)}
      ${list("O que não fazer", data.avoid_actions)}
      ${list("Como verificar", data.independent_verification)}
      ${list("Incertezas", data.uncertainties)}
      ${list("Protocolo de incidente", data.incident_protocol)}
    `;
  } catch (error) {
    result.innerHTML = `<p role="alert">${esc(error.message)}</p>`;
  }
});
