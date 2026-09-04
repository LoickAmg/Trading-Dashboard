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
  document.getElementById("quote-box").innerHTML =
    `<strong>${quote.ticker}</strong> : ${quote.price.toFixed(2)} ` +
    `<span class="${changeClass}">(${quote.change_percent.toFixed(2)}%)</span>`;

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
    const pnlClass = p.pnl >= 0 ? "positive" : "negative";
    const tr = document.createElement("tr");
    tr.innerHTML =
      `<td>${p.ticker}</td><td>${p.quantity}</td><td>${p.cost_basis.toFixed(2)}</td>` +
      `<td>${p.current_price.toFixed(2)}</td><td>${p.market_value.toFixed(2)}</td>` +
      `<td class="${pnlClass}">${p.pnl.toFixed(2)}</td>` +
      `<td class="${pnlClass}">${p.pnl_percent.toFixed(1)}%</td>` +
      `<td><button data-ticker="${p.ticker}" class="remove-btn">✕</button></td>`;
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
