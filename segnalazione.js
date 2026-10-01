// FLAIR — Segnalazione dell'incuria tramite chat (SIMULAZIONE)
// ---------------------------------------------------------------------------------
// Conversazione guidata nella chat dei cittadini: cosa hai visto → dove (mappa a comparsa
// con il segnaposto fisso al centro, stile Pokémon GO) → foto → nota → riepilogo → invio.
// È una simulazione: nessuna segnalazione viene inviata a nessun ente.
//
// Convivenza con chatbot/chat.js (flow Langflow): questo file va caricato PRIMA di chat.js.
// Intercetta solo i messaggi che riguardano una segnalazione (o arrivano mentre la
// segnalazione è in corso); tutti gli altri passano a chat.js. Se chat.js non c'è,
// risponde che l'assistente non è ancora collegato.
(() => {
  "use strict";

  const $ = id => document.getElementById(id);
  const form = $("chat-form"), input = $("prompt"), log = $("chat-log");
  const hero = $("hero"), suggestions = $("suggestions"), main = $("main");
  if (!form || !input || !log) return;

  const FILE_COMUNI = "scripts/puglia_comuni.json";
  const FILE_AIB = "datasets%20estratti/tutti_comuni_puglia_settori_aib.csv";
  const LEAFLET_JS = "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js";
  const LEAFLET_CSS = "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css";
  const ZOOM_MIN_PRECISO = 14;
  const INTENTO = /segnal|sterpagl|incuri|erba alta|incolt|potatur|rifiuti vegetal|bordo strad/i;
  const TIPI = [
    "Erba alta o sterpaglie",
    "Terreno incolto vicino a un bosco",
    "Bordo strada non pulito",
    "Rifiuti vegetali o potature",
    "Altro",
  ];

  // ---------------------------------------------------------------- stile
  const css = document.createElement("style");
  css.textContent = `
  .fr-b{max-width:85%;padding:12px 16px;border-radius:16px;line-height:1.5;font-size:16px;white-space:pre-wrap}
  .fr-bot{align-self:flex-start;background:#22323b;border:1px solid #36474f;color:#e8eef0}
  .fr-me{align-self:flex-end;background:#e8834a;color:#1a262c}
  .fr-sim{display:inline-block;font-size:11px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:#ffd8a8;background:#3a2a12;border-radius:999px;padding:2px 8px;margin-bottom:6px}
  .fr-qr{align-self:flex-start;display:flex;flex-wrap:wrap;gap:8px;max-width:100%}
  .fr-qr button,.fr-btn{min-height:40px;padding:8px 14px;border-radius:999px;border:1px solid #e8834a;background:transparent;color:#f6c29a;font:inherit;font-size:14px;cursor:pointer}
  .fr-qr button:hover,.fr-btn:hover{background:rgba(232,131,74,.14)}
  .fr-qr button.fr-primary,.fr-btn.fr-primary{background:#e8834a;color:#1a262c;font-weight:600}
  .fr-qr button:disabled{opacity:.4;cursor:default}
  .fr-card{display:grid;grid-template-columns:auto 1fr;gap:6px 14px;margin-top:8px;font-size:14px}
  .fr-card dt{color:#8b9ca3}.fr-card dd{margin:0;overflow-wrap:anywhere}
  .fr-photo{display:block;max-width:220px;max-height:160px;border-radius:12px;margin-top:6px;object-fit:cover}
  .fr-112{display:inline-block;margin-top:8px;padding:8px 14px;border-radius:999px;background:#d7392b;color:#fff;font-weight:600;text-decoration:none}
  /* ---- mappa a comparsa ---- */
  .fr-ov{position:fixed;inset:0;z-index:5000;background:rgba(8,14,17,.72);backdrop-filter:blur(3px);display:flex;align-items:center;justify-content:center;padding:16px}
  .fr-ov[hidden]{display:none}
  .fr-dlg{position:relative;width:100%;max-width:720px;height:min(86vh,760px);background:#1a262c;border:1px solid #36474f;border-radius:24px;overflow:hidden;display:flex;flex-direction:column;box-shadow:0 24px 70px rgba(0,0,0,.6);animation:fr-in .22s ease-out}
  @keyframes fr-in{from{transform:translateY(16px) scale(.98);opacity:0}to{transform:none;opacity:1}}
  .fr-top{display:flex;align-items:center;justify-content:space-between;padding:14px 16px 12px 20px;border-bottom:1px solid #2a3a42}
  .fr-top h2{margin:0;font-family:'Fraunces',Georgia,serif;font-weight:500;font-size:22px;color:#e8eef0}
  .fr-top p{margin:2px 0 0;font-size:13px;color:#a3b2b8}
  .fr-x{width:40px;height:40px;border-radius:999px;border:1px solid #36474f;background:#213039;color:#e8eef0;cursor:pointer;font-size:20px;line-height:1}
  .fr-mapwrap{position:relative;flex:1;min-height:0}
  #fr-map{position:absolute;inset:0;background:#0f181c}
  .fr-pin{position:absolute;left:50%;top:50%;z-index:900;pointer-events:none;transform:translate(-50%,-100%);transition:transform .18s ease-out}
  .fr-pin.fr-up{transform:translate(-50%,-118%)}
  .fr-pin svg{display:block;filter:drop-shadow(0 6px 6px rgba(0,0,0,.45))}
  .fr-shadow{position:absolute;left:50%;top:50%;z-index:899;pointer-events:none;width:22px;height:8px;margin:-4px 0 0 -11px;border-radius:50%;background:rgba(0,0,0,.45);transition:transform .18s ease-out}
  .fr-shadow.fr-up{transform:scale(.6)}
  .fr-ring{position:absolute;left:50%;top:50%;z-index:898;pointer-events:none;width:70px;height:26px;margin:-13px 0 0 -35px;border-radius:50%;border:3px solid #e8834a;opacity:.9;animation:fr-ring 1.8s ease-out infinite}
  @keyframes fr-ring{from{transform:scale(.4);opacity:.95}to{transform:scale(1.6);opacity:0}}
  @media (prefers-reduced-motion:reduce){.fr-ring,.fr-dlg{animation:none}.fr-pin,.fr-shadow{transition:none}}
  .fr-me-btn{position:absolute;right:14px;bottom:14px;z-index:950;width:48px;height:48px;border-radius:999px;border:1px solid #36474f;background:#1a262c;color:#e8eef0;display:flex;align-items:center;justify-content:center;cursor:pointer;box-shadow:0 6px 16px rgba(0,0,0,.4)}
  .fr-hint{position:absolute;left:50%;top:14px;transform:translateX(-50%);z-index:950;background:rgba(26,38,44,.92);color:#e8eef0;border:1px solid #36474f;border-radius:999px;padding:6px 14px;font-size:13px;white-space:nowrap;pointer-events:none}
  .fr-sheet{padding:14px 18px 18px;border-top:1px solid #2a3a42;display:flex;flex-direction:column;gap:10px}
  .fr-where{display:flex;align-items:center;gap:12px}
  .fr-where b{display:block;font-size:17px;color:#e8eef0}
  .fr-where span{font-size:13px;color:#a3b2b8;font-variant-numeric:tabular-nums}
  .fr-warn{font-size:13px;color:#ffd8a8}
  .fr-confirm{height:52px;border:none;border-radius:999px;background:#e8834a;color:#1a262c;font:inherit;font-size:16px;font-weight:600;cursor:pointer}
  .fr-confirm:disabled{opacity:.4;cursor:default}
  @media (max-width:600px){.fr-ov{padding:0}.fr-dlg{max-width:none;height:100%;border-radius:0;border:0}}
  `;
  document.head.appendChild(css);

  // ---------------------------------------------------------------- chat
  function enterChatMode() {
    if (log.style.display === "flex") return;
    if (hero) hero.style.display = "none";
    if (suggestions) suggestions.style.display = "none";
    log.style.display = "flex";
    if (main) main.style.justifyContent = "flex-end";
  }
  function scroll() { log.scrollTop = log.scrollHeight; }
  function bubble(content, who = "bot", sim = false) {
    enterChatMode();
    const b = document.createElement("div");
    b.className = "fr-b " + (who === "me" ? "fr-me" : "fr-bot");
    if (sim) { const t = document.createElement("span"); t.className = "fr-sim"; t.textContent = "Simulazione"; b.appendChild(t); b.appendChild(document.createElement("br")); }
    if (typeof content === "string") b.appendChild(document.createTextNode(content)); else b.appendChild(content);
    log.appendChild(b); scroll();
    return b;
  }
  function wait(ms) { return new Promise(r => setTimeout(r, ms)); }
  async function say(text, sim) { await wait(350); return bubble(text, "bot", sim); }

  // Pulsanti di risposta rapida: risolve con {value,label}; dopo la scelta si disattivano
  function choose(options) {
    return new Promise(resolve => {
      const row = document.createElement("div");
      row.className = "fr-qr";
      options.forEach(o => {
        const btn = document.createElement("button");
        btn.type = "button"; btn.textContent = o.label;
        if (o.primary) btn.className = "fr-primary";
        btn.addEventListener("click", () => {
          row.querySelectorAll("button").forEach(x => x.disabled = true);
          resolve(o);
        });
        row.appendChild(btn);
      });
      log.appendChild(row); scroll();
      row.querySelector("button").focus({ preventScroll: true });
    });
  }

  // ---------------------------------------------------------------- dati comuni
  let comuni = null, aib = {};
  function carica() {
    if (carica.p) return carica.p;
    carica.p = Promise.allSettled([
      fetch(FILE_COMUNI).then(r => r.ok ? r.json() : Promise.reject()),
      fetch(FILE_AIB).then(r => r.ok ? r.text() : Promise.reject()),
    ]).then(([g, a]) => {
      if (g.status === "fulfilled") comuni = g.value;
      if (a.status === "fulfilled") {
        const righe = a.value.replace(/^﻿/, "").trim().split(/\r?\n/);
        const h = righe.shift().split(",");
        const ic = h.indexOf("comune"), is = h.indexOf("settore_aib");
        righe.forEach(r => { const c = r.split(","); if (c[ic]) aib[c[ic]] = c[is]; });
      }
    });
    return carica.p;
  }
  function inRing(x, y, ring) {
    let inside = false;
    for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
      const [xi, yi] = ring[i], [xj, yj] = ring[j];
      if ((yi > y) !== (yj > y) && x < (xj - xi) * (y - yi) / (yj - yi) + xi) inside = !inside;
    }
    return inside;
  }
  function trovaComune(lat, lon) {
    if (!comuni) return null;
    for (const f of comuni.features) {
      const g = f.geometry, polys = g.type === "Polygon" ? [g.coordinates] : g.coordinates;
      for (const p of polys)
        if (inRing(lon, lat, p[0]) && !p.slice(1).some(h => inRing(lon, lat, h)))
          return { comune: f.properties.c, provincia: f.properties.p, settore: aib[f.properties.c] || "" };
    }
    return null;
  }

  // ---------------------------------------------------------------- mappa a comparsa
  function caricaLeaflet() {
    if (window.L) return Promise.resolve();
    if (caricaLeaflet.p) return caricaLeaflet.p;
    const l = document.createElement("link"); l.rel = "stylesheet"; l.href = LEAFLET_CSS; document.head.appendChild(l);
    caricaLeaflet.p = new Promise((res, rej) => {
      const s = document.createElement("script"); s.src = LEAFLET_JS; s.onload = res; s.onerror = rej; document.head.appendChild(s);
    });
    return caricaLeaflet.p;
  }

  let ov = null, mappa = null;
  function costruisciDialogo() {
    ov = document.createElement("div");
    ov.className = "fr-ov"; ov.hidden = true;
    ov.innerHTML = `
      <div class="fr-dlg" role="dialog" aria-modal="true" aria-labelledby="fr-t">
        <div class="fr-top">
          <div><h2 id="fr-t">Dove si trova?</h2><p>Sposta la mappa: il segnaposto resta al centro.</p></div>
          <button type="button" class="fr-x" id="fr-close" aria-label="Chiudi senza scegliere">×</button>
        </div>
        <div class="fr-mapwrap">
          <div id="fr-map" aria-label="Mappa: trascina per posizionare il punto al centro"></div>
          <div class="fr-ring" aria-hidden="true"></div>
          <div class="fr-shadow" id="fr-shadow" aria-hidden="true"></div>
          <div class="fr-pin" id="fr-pin" aria-hidden="true">
            <svg width="44" height="58" viewBox="0 0 30 40"><path d="M15 1C7.3 1 1.5 6.9 1.5 14.3 1.5 24.6 15 39 15 39s13.5-14.4 13.5-24.7C28.5 6.9 22.7 1 15 1z" fill="#e8834a" stroke="#1a262c" stroke-width="2"/><circle cx="15" cy="14" r="5.5" fill="#1a262c"/></svg>
          </div>
          <div class="fr-hint" id="fr-hint">Avvicinati per posizionare il punto con precisione</div>
          <button type="button" class="fr-me-btn" id="fr-me" aria-label="Usa la mia posizione">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3"/></svg>
          </button>
        </div>
        <div class="fr-sheet">
          <div class="fr-where"><div><b id="fr-comune">—</b><span id="fr-coord">—</span></div></div>
          <div class="fr-warn" id="fr-warn" hidden></div>
          <button type="button" class="fr-confirm" id="fr-ok" disabled>Conferma posizione</button>
        </div>
      </div>`;
    document.body.appendChild(ov);
  }

  function apriMappa() {
    return new Promise(async resolve => {
      if (!ov) costruisciDialogo();
      ov.hidden = false;
      const prima = document.activeElement;
      const pin = $("fr-pin"), ombra = $("fr-shadow"), ok = $("fr-ok"), warn = $("fr-warn"), hint = $("fr-hint");
      let scelta = null;

      const chiudi = val => {
        ov.hidden = true;
        document.removeEventListener("keydown", tasti, true);
        if (prima && prima.focus) prima.focus({ preventScroll: true });
        resolve(val);
      };
      const tasti = e => { if (e.key === "Escape") { e.preventDefault(); chiudi(null); } };
      document.addEventListener("keydown", tasti, true);
      $("fr-close").onclick = () => chiudi(null);
      ok.onclick = () => { if (scelta) chiudi(scelta); };

      try { await Promise.all([caricaLeaflet(), carica()]); }
      catch (e) {
        warn.hidden = false; warn.textContent = "Non riesco a caricare la mappa. Controlla la connessione e riprova.";
        return;
      }

      if (!mappa) {
        mappa = L.map("fr-map", { zoomControl: false, attributionControl: true }).setView([41.0, 16.6], 8);
        L.control.zoom({ position: "topright" }).addTo(mappa);
        L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", { maxZoom: 19, attribution: "Tiles &copy; Esri" }).addTo(mappa);
        L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}", { maxZoom: 19, opacity: .85 }).addTo(mappa);
        mappa.on("movestart", () => { pin.classList.add("fr-up"); ombra.classList.add("fr-up"); });
        mappa.on("moveend", () => { pin.classList.remove("fr-up"); ombra.classList.remove("fr-up"); aggiorna(); });
        mappa.on("move", () => { const c = mappa.getCenter(); $("fr-coord").textContent = `${c.lat.toFixed(5)}, ${c.lng.toFixed(5)}`; });
        $("fr-me").onclick = () => {
          if (!navigator.geolocation) { warn.hidden = false; warn.textContent = "Il browser non permette di leggere la posizione."; return; }
          warn.hidden = false; warn.textContent = "Cerco la tua posizione…";
          navigator.geolocation.getCurrentPosition(
            p => { warn.hidden = true; mappa.setView([p.coords.latitude, p.coords.longitude], 17); },
            () => { warn.textContent = "Posizione non disponibile: sposta la mappa a mano."; },
            { enableHighAccuracy: true, timeout: 10000 });
        };
      }
      setTimeout(() => { mappa.invalidateSize(); aggiorna(); }, 60);

      function aggiorna() {
        const c = mappa.getCenter(), z = mappa.getZoom();
        const info = trovaComune(c.lat, c.lng);
        $("fr-coord").textContent = `${c.lat.toFixed(5)}, ${c.lng.toFixed(5)}`;
        hint.hidden = z >= ZOOM_MIN_PRECISO;
        warn.hidden = true; scelta = null; ok.disabled = true;
        if (!comuni) { $("fr-comune").textContent = "Punto selezionato"; }
        else if (!info) {
          $("fr-comune").textContent = "Fuori dalla Puglia";
          warn.hidden = false; warn.textContent = "Sposta il segnaposto dentro il territorio pugliese.";
          return;
        } else {
          $("fr-comune").textContent = `${info.comune} (${info.provincia})` + (info.settore ? ` · settore ${info.settore}` : "");
        }
        if (z < ZOOM_MIN_PRECISO) return;
        scelta = { lat: c.lat, lon: c.lng, ...(info || {}) };
        ok.disabled = false;
      }
    });
  }

  // ---------------------------------------------------------------- foto
  function scegliFoto() {
    return new Promise(resolve => {
      const f = document.createElement("input");
      f.type = "file"; f.accept = "image/*"; f.setAttribute("capture", "environment");
      f.onchange = () => resolve(f.files && f.files[0] ? f.files[0] : null);
      f.click();
    });
  }

  // ---------------------------------------------------------------- flusso
  let attesaTesto = null;          // funzione che riceve il prossimo testo scritto (nota)
  let inCorso = false;

  async function avvia(testoUtente) {
    if (inCorso) return;
    inCorso = true;
    try {
      if (testoUtente) bubble(testoUtente, "me");
      await say("Posso aiutarti a segnalare una situazione a rischio vicino a un bosco: erba alta, sterpaglie, terreni incolti.\nPrima una domanda: vedi fumo o fiamme in questo momento?", true);
      const emergenza = await choose([{ value: "si", label: "Sì, vedo fumo o fiamme" }, { value: "no", label: "No, è una situazione a rischio", primary: true }]);
      bubble(emergenza.label, "me");
      if (emergenza.value === "si") {
        const n = document.createElement("div");
        n.appendChild(document.createTextNode("Allora non segnalare qui: chiama subito il 112."));
        n.appendChild(document.createElement("br"));
        const a = document.createElement("a"); a.href = "tel:112"; a.className = "fr-112"; a.textContent = "Chiama il 112";
        n.appendChild(a);
        await wait(300); bubble(n);
        return;
      }

      await say("Che cosa hai visto?");
      const tipo = await choose(TIPI.map(t => ({ value: t, label: t })));
      bubble(tipo.label, "me");

      let luogo = null;
      while (!luogo) {
        await say("Dove si trova? Apri la mappa, sposta il segnaposto sul punto esatto e conferma.");
        const r = await choose([{ value: "mappa", label: "Apri la mappa", primary: true }, { value: "annulla", label: "Annulla segnalazione" }]);
        if (r.value === "annulla") { bubble(r.label, "me"); await say("Va bene, segnalazione annullata."); return; }
        luogo = await apriMappa();
        if (!luogo) await say("Non hai scelto un punto.");
      }
      bubble(`📍 ${luogo.comune ? `${luogo.comune} (${luogo.provincia})` : "Punto sulla mappa"}\n${luogo.lat.toFixed(5)}, ${luogo.lon.toFixed(5)}`, "me");

      let foto = null;
      await say("Vuoi aggiungere una foto? Aiuta a capire la situazione. Resta sul tuo dispositivo.");
      const fr = await choose([{ value: "foto", label: "Scatta o scegli una foto", primary: true }, { value: "no", label: "Salta" }]);
      if (fr.value === "foto") {
        foto = await scegliFoto();
        if (foto) {
          const w = document.createElement("div");
          const img = document.createElement("img"); img.className = "fr-photo"; img.alt = "Foto allegata alla segnalazione"; img.src = URL.createObjectURL(foto);
          w.appendChild(img); bubble(w, "me");
        } else bubble("Nessuna foto", "me");
      } else bubble("Salta", "me");

      await say("Vuoi aggiungere una nota? Scrivila qui sotto (per esempio: da quanto tempo è così, quanto è estesa), oppure salta.");
      input.placeholder = "Scrivi una nota per la segnalazione…";
      input.focus({ preventScroll: true });
      const nota = await new Promise(resolve => {
        attesaTesto = t => resolve(t);
        choose([{ value: "", label: "Salta la nota" }]).then(() => { if (attesaTesto) { attesaTesto = null; resolve(""); } });
      });
      attesaTesto = null;
      input.placeholder = "Es. Qual è il rischio incendi oggi a Cavallino?";
      if (!nota) bubble("Nessuna nota", "me");

      const card = document.createElement("div");
      card.appendChild(document.createTextNode("Ecco il riepilogo. Controlla e invia."));
      const dl = document.createElement("dl"); dl.className = "fr-card";
      const riga = (k, v) => { const dt = document.createElement("dt"); dt.textContent = k; const dd = document.createElement("dd"); dd.textContent = v; dl.append(dt, dd); };
      riga("Tipo", tipo.value);
      riga("Comune", luogo.comune ? `${luogo.comune} (${luogo.provincia})` : "—");
      riga("Settore AIB", luogo.settore || "—");
      riga("Coordinate", `${luogo.lat.toFixed(5)}, ${luogo.lon.toFixed(5)}`);
      riga("Foto", foto ? "allegata" : "nessuna");
      riga("Nota", nota || "—");
      card.appendChild(dl);
      await wait(300); bubble(card, "bot", true);
      const conf = await choose([{ value: "invia", label: "Invia segnalazione", primary: true }, { value: "annulla", label: "Annulla" }]);
      bubble(conf.label, "me");
      if (conf.value !== "invia") { await say("Segnalazione annullata. Se cambi idea, chiedimi di nuovo di segnalare."); return; }

      const codice = "SEG-" + new Date().getFullYear() + "-" + String(Math.floor(1000 + Math.random() * 9000));
      const rec = { codice, data_ora: new Date().toISOString(), tipo: tipo.value, lat: +luogo.lat.toFixed(6), lon: +luogo.lon.toFixed(6),
                    comune: luogo.comune || "", provincia: luogo.provincia || "", settore_aib: luogo.settore || "", foto: !!foto, nota };
      try { const k = "flair_segnalazioni_incuria"; const l = JSON.parse(sessionStorage.getItem(k) || "[]"); l.push(rec); sessionStorage.setItem(k, JSON.stringify(l)); } catch (e) {}
      await say(`Segnalazione registrata. Codice ${codice}.\n\nQuesta è una simulazione: la segnalazione non è stata inviata a nessun ente. In un servizio reale potrebbe arrivare al Comune e alla Protezione Civile, per programmare la pulizia prima dell'estate.\n\nGrazie: prendersi cura del territorio è la prima forma di prevenzione. Se vedi fumo o fiamme, chiama subito il 112.`, true);
    } finally {
      inCorso = false; attesaTesto = null;
      input.placeholder = "Es. Qual è il rischio incendi oggi a Cavallino?";
    }
  }

  // ---------------------------------------------------------------- aggancio alla chat
  const chatVera = () => typeof window.askFlow === "function";   // definita da chatbot/chat.js

  function gestisci(testo) {
    testo = (testo || "").trim();
    if (!testo) return true;
    if (attesaTesto) { const f = attesaTesto; attesaTesto = null; log.querySelectorAll(".fr-qr button").forEach(b => b.disabled = true); bubble(testo, "me"); input.value = ""; f(testo); return true; }
    if (inCorso) { bubble(testo, "me"); input.value = ""; say("Completa prima la segnalazione in corso, usando i pulsanti qui sopra."); return true; }
    if (INTENTO.test(testo)) { input.value = ""; avvia(testo); return true; }
    if (chatVera()) return false;                // lascia la risposta al chatbot Langflow
    bubble(testo, "me"); input.value = "";
    say("L'assistente non è ancora collegato a questa versione del sito, quindi non posso rispondere a questa domanda. Posso però aiutarti a segnalare erba alta, sterpaglie o terreni incolti vicino a un bosco: scrivi «segnala».");
    return true;
  }

  form.addEventListener("submit", e => {
    if (gestisci(input.value)) { e.preventDefault(); e.stopImmediatePropagation(); }
  }, true);
  input.addEventListener("keydown", e => {
    if (e.key !== "Enter" || e.shiftKey) return;
    if (gestisci(input.value)) { e.preventDefault(); e.stopImmediatePropagation(); }
  }, true);
  if (suggestions) suggestions.querySelectorAll("button").forEach(btn => {
    btn.addEventListener("click", e => {
      const t = btn.dataset.prompt || btn.textContent;
      if (btn.hasAttribute("data-segnala")) { e.stopImmediatePropagation(); avvia(t); return; }
      if (gestisci(t)) e.stopImmediatePropagation();
    }, true);
  });
  const segnalaBtn = document.getElementById("btn-segnala");
  if (segnalaBtn) segnalaBtn.addEventListener("click", () => avvia("Voglio segnalare una situazione a rischio"));

  window.FLAIR_SEGNALAZIONE = { avvia };
})();
