// FLAIR — collegamento tra index.html e il flow Langflow
// Chiama POST {LANGFLOW_URL}/api/v1/run/{FLOW_ID} e mostra la risposta in #chat-log.

const CONFIG = {
  // In locale: Langflow avviato con chatbot/lang-compose.yml
  // In produzione: l'URL del TUO proxy (vedi README), mai Langflow diretto con la chiave nel browser
  LANGFLOW_URL: "http://localhost:7860",
  FLOW_ID: "4cc9bdc6-a477-4283-9452-7b729a868017",   // Langflow → flow → Share → API access
  API_KEY: "",                         // SOLO per sviluppo locale; lasciare vuoto se usi il proxy
};

const form = document.getElementById("chat-form");
const input = document.getElementById("prompt");
const log = document.getElementById("chat-log");
const hero = document.getElementById("hero");
const suggestions = document.getElementById("suggestions");
const sendBtn = document.getElementById("send-btn");

// Una sessione per scheda: Langflow usa session_id per la memoria della conversazione
const SESSION_ID = (crypto.randomUUID && crypto.randomUUID()) || String(Date.now());

function addBubble(text, who) {
  const b = document.createElement("div");
  const mine = who === "user";
  b.style.cssText = [
    "max-width:85%", "padding:12px 16px", "border-radius:16px",
    "white-space:pre-wrap", "line-height:1.5", "font-size:16px",
    mine ? "align-self:flex-end;background:#e8834a;color:#1a262c"
         : "align-self:flex-start;background:#22323b;border:1px solid #36474f;color:#e8eef0",
  ].join(";");
  b.textContent = text;              // textContent: niente HTML iniettato dalla risposta
  log.appendChild(b);
  log.scrollTop = log.scrollHeight;
  return b;
}

function enterChatMode() {
  if (log.style.display === "flex") return;
  hero.style.display = "none";
  suggestions.style.display = "none";
  log.style.display = "flex";
  document.getElementById("main").style.justifyContent = "flex-end";
}

async function askFlow(message) {
  const headers = { "Content-Type": "application/json" };
  if (CONFIG.API_KEY) headers["x-api-key"] = CONFIG.API_KEY;

  const res = await fetch(`${CONFIG.LANGFLOW_URL}/api/v1/run/${CONFIG.FLOW_ID}?stream=false`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      input_value: message,
      input_type: "chat",
      output_type: "chat",
      session_id: SESSION_ID,
    }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
  const data = await res.json();
  // Percorso documentato da Langflow per il testo della chat
  return data?.outputs?.[0]?.outputs?.[0]?.results?.message?.text
      ?? "(Risposta vuota dal flow)";
}

async function send(message) {
  message = message.trim();
  if (!message) return;
  enterChatMode();
  addBubble(message, "user");
  input.value = "";
  sendBtn.disabled = true;
  const pending = addBubble("…", "bot");
  try {
    pending.textContent = await askFlow(message);
  } catch (err) {
    console.error(err);
    pending.textContent = "Non riesco a contattare l'assistente. In caso di emergenza chiama il 112.";
  } finally {
    sendBtn.disabled = false;
    input.focus();
  }
}

form.addEventListener("submit", (e) => { e.preventDefault(); send(input.value); });

// Invio con Enter, a capo con Shift+Enter
input.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(input.value); }
});

// I pulsanti di suggerimento inviano il loro testo
suggestions.querySelectorAll("button").forEach((btn) =>
  btn.addEventListener("click", () => send(btn.textContent))
);
