// Frontend statique (vanilla JS) : interroge l'API FastAPI locale et dessine
// un graphique simple sur <canvas> (pas de dépendance externe). Rafraîchit
// périodiquement pour simuler un suivi "live" (les données réelles Stooq
// sont quotidiennes, pas du vrai temps réel — voir README).

const REFRESH_MS = 15000;

async function fetchJson(url, options) {
  const res = await fetch(url, options);
  if (!res.ok) throw new Error(`${url} -> HTTP ${res.status}`);
  return res.json();
}

function drawPriceChart(canvas, candles) {
  const ctx = canvas.getContext("2d");
  const width = (canvas.width = canvas.clientWidth);
  const height = canvas.height;
  ctx.clearRect(0, 0, width, height);
  if (candles.length < 2) return;

  const closes = candles.map((c) => c.close);
  const min = Math.min(...closes);
  const max = Math.max(...closes);
  const range = max - min || 1;
  const stepX = width / (closes.length - 1);

  ctx.strokeStyle = "#38bdf8";
  ctx.lineWidth = 2;
  ctx.beginPath();
  closes.forEach((price, i) => {
    const x = i * stepX;
    const y = height - ((price - min) / range) * (height - 20) - 10;
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();
}

async function loadTicker(ticker) {
  const [quote, history, indicators] = await Promise.all([
    fetchJson(`/api/quote/${encodeURIComponent(ticker)}`),
    fetchJson(`/api/history/${encodeURIComponent(ticker)}?days=90`),
    fetchJson(`/api/indicators/${encodeURIComponent(ticker)}?days=90`),
  ]);

  const changeClass = quote.change_percent >= 0 ? "positive" : "negative";
  const quoteBox = document.getElementById("quote-box");
  quoteBox.innerHTML = "";
  const strong = document.createElement("strong");
  strong.textContent = quote.ticker;
  const span = document.createElement("span");
  span.className = changeClass;
  span.textContent = `(${quote.change_percent.toFixed(2)}%)`;
  quoteBox.append(strong, ` : ${quote.price.toFixed(2)} `, span);

  drawPriceChart(document.getElementById("price-chart"), history);

  const fmt = (v) => (v === null || v === undefined ? "—" : v.toFixed(2));
  document.getElementById("indicators-box").innerHTML =
    `SMA20: ${fmt(indicators.sma_20)} · SMA50: ${fmt(indicators.sma_50)} · ` +
    `RSI14: ${fmt(indicators.rsi_14)} · Volatilité: ${fmt(indicators.volatility_pct)}%`;
}

async function loadPortfolio() {
  const data = await fetchJson("/api/portfolio");
  const tbody = document.querySelector("#portfolio-table tbody");
  tbody.innerHTML = "";
  for (const p of data.positions) {
    // `p.ticker` vient d'une valeur saisie par l'utilisateur, persistée puis
    // renvoyée telle quelle par l'API : on la place en `textContent`, jamais
    // en `innerHTML`, pour ne pas rouvrir un XSS stocké (ex: un ticker du
    // type `<img src=x onerror=...>`).
    const pnlClass = p.pnl >= 0 ? "positive" : "negative";
    const tr = document.createElement("tr");

    const cell = (text, className) => {
      const td = document.createElement("td");
      if (className) td.className = className;
      td.textContent = text;
      return td;
    };

    const removeBtn = document.createElement("button");
    removeBtn.className = "remove-btn";
    removeBtn.dataset.ticker = p.ticker;
    removeBtn.textContent = "✕";
    const actionCell = document.createElement("td");
    actionCell.appendChild(removeBtn);

    tr.append(
      cell(p.ticker),
      cell(String(p.quantity)),
      cell(p.cost_basis.toFixed(2)),
      cell(p.current_price.toFixed(2)),
      cell(p.market_value.toFixed(2)),
      cell(p.pnl.toFixed(2), pnlClass),
      cell(`${p.pnl_percent.toFixed(1)}%`, pnlClass),
      actionCell
    );
    tbody.appendChild(tr);
  }
  document.getElementById("portfolio-totals").textContent =
    `Total : ${data.total_market_value.toFixed(2)} — P&L : ${data.total_pnl.toFixed(2)}`;

  document.querySelectorAll(".remove-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      await fetch(`/api/portfolio/holdings/${encodeURIComponent(btn.dataset.ticker)}`, {
        method: "DELETE",
      });
      loadPortfolio();
    });
  });
}

document.getElementById("load-ticker").addEventListener("click", () => {
  const ticker = document.getElementById("ticker-input").value.trim();
  if (ticker) loadTicker(ticker).catch((err) => console.error(err));
});

document.getElementById("add-holding").addEventListener("click", async () => {
  const ticker = document.getElementById("holding-ticker").value.trim();
  const quantity = parseFloat(document.getElementById("holding-qty").value);
  const cost_basis = parseFloat(document.getElementById("holding-cost").value);
  if (!ticker || !Number.isFinite(quantity) || !Number.isFinite(cost_basis)) return;

  await fetchJson("/api/portfolio/holdings", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ticker, quantity, cost_basis }),
  });
  loadPortfolio();
});

loadTicker(document.getElementById("ticker-input").value.trim()).catch((err) =>
  console.error(err)
);
loadPortfolio().catch((err) => console.error(err));

setInterval(() => {
  const ticker = document.getElementById("ticker-input").value.trim();
  if (ticker) loadTicker(ticker).catch((err) => console.error(err));
  loadPortfolio().catch((err) => console.error(err));
}, REFRESH_MS);
