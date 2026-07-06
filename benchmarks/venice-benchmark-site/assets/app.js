/* BenchmarkViv — assets/app.js */
(() => {
  "use strict";

  const DATA_URL = "data/results.json";

  const BENCHMARKS = [
    { id: "intent-understanding", label: "Intent Understanding" },
    { id: "one-shot-ui", label: "One-Shot UI" },
    { id: "long-horizon-agent", label: "Long-Horizon Agent" },
    { id: "brick-breaker-realism", label: "Brick Breaker" },
  ];

  const MODEL_COLORS = {
    "GPT-5.5": "#10a37f",
    "Fable 5": "#d97757",
    "Opus 4.8": "#8b5cf6",
    "GLM 5.2": "#3b82f6",
    "DeepSeek V4": "#0ea5e9",
    "MiniMax M3": "#f43f5e",
  };

  const FALLBACK_DATA = {
    generated: "2026-07-05T00:00:00Z",
    source: "fallback",
    results: [
      { model: "GPT-5.5", benchmark: "intent-understanding", score: 88.0, latency: 16.6, tokens: 2988, cost: 0.055 },
      { model: "GPT-5.5", benchmark: "one-shot-ui", score: 89.0, latency: 16.4, tokens: 3771, cost: 0.079 },
      { model: "GPT-5.5", benchmark: "long-horizon-agent", score: 100.0, latency: 27.3, tokens: 3788, cost: 0.079 },
      { model: "GPT-5.5", benchmark: "brick-breaker-realism", score: 0.0, latency: 34.2, tokens: 3801, cost: 0.079 },
      { model: "Fable 5", benchmark: "intent-understanding", score: 82.0, latency: 16.7, tokens: 3603, cost: 0.042 },
      { model: "Fable 5", benchmark: "one-shot-ui", score: 89.0, latency: 21.7, tokens: 4813, cost: 0.071 },
      { model: "Fable 5", benchmark: "long-horizon-agent", score: 100.0, latency: 31.4, tokens: 4826, cost: 0.071 },
      { model: "Fable 5", benchmark: "brick-breaker-realism", score: 45.0, latency: 24.7, tokens: 4868, cost: 0.072 },
      { model: "Opus 4.8", benchmark: "intent-understanding", score: 82.0, latency: 13.2, tokens: 3528, cost: 0.099 },
      { model: "Opus 4.8", benchmark: "one-shot-ui", score: 89.0, latency: 20.0, tokens: 4821, cost: 0.195 },
      { model: "Opus 4.8", benchmark: "long-horizon-agent", score: 100.0, latency: 28.6, tokens: 4834, cost: 0.195 },
      { model: "Opus 4.8", benchmark: "brick-breaker-realism", score: 55.0, latency: 24.8, tokens: 4876, cost: 0.196 },
      { model: "GLM 5.2", benchmark: "intent-understanding", score: 70.0, latency: 9.6, tokens: 2279, cost: 0.003 },
      { model: "GLM 5.2", benchmark: "one-shot-ui", score: 82.0, latency: 18.6, tokens: 3748, cost: 0.008 },
      { model: "GLM 5.2", benchmark: "long-horizon-agent", score: 100.0, latency: 32.4, tokens: 3764, cost: 0.008 },
      { model: "GLM 5.2", benchmark: "brick-breaker-realism", score: 85.0, latency: 20.7, tokens: 3776, cost: 0.008 },
      { model: "DeepSeek V4", benchmark: "intent-understanding", score: 86.0, latency: 12.0, tokens: 2600, cost: 0.008 },
      { model: "DeepSeek V4", benchmark: "one-shot-ui", score: 85.0, latency: 18.0, tokens: 4100, cost: 0.015 },
      { model: "DeepSeek V4", benchmark: "long-horizon-agent", score: 96.0, latency: 30.0, tokens: 4200, cost: 0.016 },
      { model: "DeepSeek V4", benchmark: "brick-breaker-realism", score: 78.0, latency: 22.0, tokens: 4000, cost: 0.015 },
      { model: "MiniMax M3", benchmark: "intent-understanding", score: 78.0, latency: 8.0, tokens: 2100, cost: 0.004 },
      { model: "MiniMax M3", benchmark: "one-shot-ui", score: 80.0, latency: 14.0, tokens: 3500, cost: 0.007 },
      { model: "MiniMax M3", benchmark: "long-horizon-agent", score: 90.0, latency: 24.0, tokens: 3600, cost: 0.007 },
      { model: "MiniMax M3", benchmark: "brick-breaker-realism", score: 65.0, latency: 16.0, tokens: 3400, cost: 0.007 },
    ],
  };

  const state = {
    data: [],
    isLive: false,
    sort: { key: "score", dir: -1 },
    filter: { text: "", benchmark: "all" },
    charts: { leaderboard: null, costValue: null, sparklines: [] },
  };

  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  const fmtScore = (n) => (n == null ? "—" : n.toFixed(1));
  const fmtLatency = (n) => (n == null ? "—" : `${n.toFixed(1)}s`);
  const fmtTokens = (n) => (n == null ? "—" : Math.round(n).toLocaleString("en-US"));
  const fmtCost = (n) => (n == null ? "—" : `$${n.toFixed(3)}`);

  function benchmarkLabel(id) {
    const b = BENCHMARKS.find((b) => b.id === id);
    return b ? b.label : id;
  }

  function uniqueModels(rows) {
    return [...new Set(rows.map((r) => r.model))];
  }

  function avg(nums) {
    return nums.length ? nums.reduce((a, b) => a + b, 0) / nums.length : 0;
  }

  function modelAggregates(rows) {
    return uniqueModels(rows).map((model) => {
      const mr = rows.filter((r) => r.model === model);
      return {
        model,
        avgScore: avg(mr.map((r) => r.score)),
        avgLatency: avg(mr.map((r) => r.latency)),
        avgTokens: avg(mr.map((r) => r.tokens)),
        avgCost: avg(mr.map((r) => r.cost)),
        scores: BENCHMARKS.map((b) => {
          const row = mr.find((r) => r.benchmark === b.id);
          return row ? row.score : 0;
        }),
      };
    });
  }

  function modelColor(model, alpha = 1) {
    const hex = MODEL_COLORS[model] || "#94a3b8";
    if (alpha >= 1) return hex;
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  }

  function normalizeId(id) {
    return String(id).replace(/_/g, "-");
  }

  async function loadData() {
    const status = $("#dataStatus");
    try {
      const res = await fetch(DATA_URL, { cache: "no-store" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      if (!Array.isArray(json.results) || json.results.length === 0) throw new Error("No results");

      const modelMap = Object.fromEntries((json.models || []).map((m) => [m.id, m.display]));
      const benchMap = Object.fromEntries((json.benchmarks || []).map((b) => [b.id, b.name]));

      state.data = json.results.map((r) => ({
        model: modelMap[r.model_id] || r.model_id || r.model,
        benchmark: normalizeId(r.benchmark_id || r.benchmark),
        score: r.score,
        latency: r.latency,
        tokens: r.total_tokens || r.tokens,
        cost: r.estimated_cost_usd || r.cost,
      }));
      state.isLive = true;
      if (status) {
        status.textContent = "● Live data";
        status.classList.remove("fallback");
      }
    } catch (err) {
      console.warn("[BenchmarkViv] fallback data:", err.message);
      state.data = FALLBACK_DATA.results;
      state.isLive = false;
      if (status) {
        status.textContent = "● Sample data";
        status.classList.add("fallback");
      }
    }
  }

  function renderLeaderboardChart() {
    const canvas = $("#leaderboardChart");
    if (!canvas || typeof Chart === "undefined") return;
    const aggs = modelAggregates(state.data).sort((a, b) => b.avgScore - a.avgScore);
    if (state.charts.leaderboard) state.charts.leaderboard.destroy();
    state.charts.leaderboard = new Chart(canvas, {
      type: "bar",
      data: {
        labels: aggs.map((a) => a.model),
        datasets: [{
          label: "Average score",
          data: aggs.map((a) => Number(a.avgScore.toFixed(2))),
          backgroundColor: aggs.map((a) => modelColor(a.model, 0.75)),
          borderColor: aggs.map((a) => modelColor(a.model)),
          borderWidth: 1.5,
          borderRadius: 6,
          maxBarThickness: 56,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          y: { min: 0, max: 100, grid: { color: "rgba(26,26,46,0.06)" } },
          x: { grid: { display: false } },
        },
      },
    });
  }

  function renderCostValueChart() {
    const canvas = $("#costValueChart");
    if (!canvas || typeof Chart === "undefined") return;
    const aggs = modelAggregates(state.data);
    const maxCost = Math.max(...aggs.map((a) => a.avgCost), 0.01);
    if (state.charts.costValue) state.charts.costValue.destroy();
    state.charts.costValue = new Chart(canvas, {
      type: "bubble",
      data: {
        datasets: aggs.map((a) => ({
          label: a.model,
          data: [{
            x: Number(a.avgCost.toFixed(4)),
            y: Number(a.avgScore.toFixed(2)),
            r: 6 + Math.min((a.avgCost / maxCost) * 28, 28),
          }],
          backgroundColor: modelColor(a.model, 0.55),
          borderColor: modelColor(a.model),
          borderWidth: 1.5,
        })),
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: "bottom", labels: { usePointStyle: true, boxWidth: 8 } },
          tooltip: {
            callbacks: {
              label: (ctx) => [
                ` ${ctx.dataset.label}`,
                ` Avg cost/run: $${ctx.raw.x.toFixed(3)}`,
                ` Avg score: ${ctx.raw.y.toFixed(1)}`,
              ],
            },
          },
        },
        scales: {
          x: {
            type: "logarithmic",
            title: { display: true, text: "Avg cost per run (USD, log)" },
            grid: { color: "rgba(26,26,46,0.06)" },
          },
          y: {
            min: 60,
            max: 100,
            title: { display: true, text: "Average score" },
            grid: { color: "rgba(26,26,46,0.06)" },
          },
        },
      },
    });
  }

  function renderTable() {
    const tbody = $("#leaderboardBody");
    if (!tbody) return;

    let rows = state.data.filter((r) => {
      if (state.filter.benchmark !== "all" && r.benchmark !== state.filter.benchmark) return false;
      if (state.filter.text) {
        const hay = `${r.model} ${benchmarkLabel(r.benchmark)}`.toLowerCase();
        if (!hay.includes(state.filter.text.toLowerCase())) return false;
      }
      return true;
    });

    const { key, dir } = state.sort;
    rows = rows.slice().sort((a, b) => {
      let av = a[key], bv = b[key];
      if (key === "rank") av = -a.score, bv = -b.score;
      if (typeof av === "string") return av.localeCompare(bv) * dir;
      return (av - bv) * dir;
    });

    $$("th[data-sort]").forEach((th) => {
      th.classList.remove("sorted-asc", "sorted-desc");
      if (th.dataset.sort === key) th.classList.add(dir === 1 ? "sorted-asc" : "sorted-desc");
    });

    tbody.innerHTML = rows.map((r, i) => `
      <tr>
        <td class="rank">${i + 1}</td>
        <td class="model-name"><span class="model-dot" style="background:${modelColor(r.model)}"></span>${r.model}</td>
        <td>${benchmarkLabel(r.benchmark)}</td>
        <td>
          <strong>${fmtScore(r.score)}</strong>
          <div class="score-bar u-score-animate" style="--score:${Math.max(0, Math.min(100, r.score))}%"></div>
        </td>
        <td>${fmtLatency(r.latency)}</td>
        <td>${fmtTokens(r.tokens)}</td>
        <td>${fmtCost(r.cost)}</td>
      </tr>
    `).join("");

    if (rows.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;padding:2rem;color:var(--ink-2)">No results match your filters.</td></tr>`;
    }
  }

  function initTableControls() {
    $$("th[data-sort]").forEach((th) => {
      th.addEventListener("click", () => {
        const key = th.dataset.sort;
        if (state.sort.key === key) state.sort.dir *= -1;
        else { state.sort.key = key; state.sort.dir = key === "model" || key === "benchmark" ? 1 : -1; }
        renderTable();
      });
    });

    const search = $("#tableSearch");
    if (search) search.addEventListener("input", () => { state.filter.text = search.value; renderTable(); });

    $$("#benchmarkFilters .filter-chip").forEach((chip) => {
      chip.addEventListener("click", () => {
        $$("#benchmarkFilters .filter-chip").forEach((c) => c.classList.remove("is-active"));
        chip.classList.add("is-active");
        state.filter.benchmark = chip.dataset.filter;
        renderTable();
      });
    });
  }

  function renderComparison() {
    const container = $("#modelComparison");
    if (!container) return;
    state.charts.sparklines.forEach((c) => c.destroy());
    state.charts.sparklines = [];
    const aggs = modelAggregates(state.data).sort((a, b) => b.avgScore - a.avgScore);

    container.innerHTML = aggs.map((a, i) => `
      <article class="compare-card reveal">
        <header>
          <span class="badge">#${i + 1}</span>
          <h3>${a.model}</h3>
        </header>
        <div class="score">${a.avgScore.toFixed(1)}</div>
        <dl>
          <div><dt>Latency</dt><dd>${a.avgLatency.toFixed(1)}s</dd></div>
          <div><dt>Cost/run</dt><dd>$${a.avgCost.toFixed(3)}</dd></div>
          <div><dt>Tokens</dt><dd>${Math.round(a.avgTokens).toLocaleString()}</dd></div>
        </dl>
        <canvas height="60"></canvas>
      </article>
    `).join("");

    aggs.forEach((a, i) => {
      const canvas = container.children[i].querySelector("canvas");
      if (!canvas || typeof Chart === "undefined") return;
      state.charts.sparklines.push(new Chart(canvas, {
        type: "line",
        data: {
          labels: BENCHMARKS.map((b) => b.label),
          datasets: [{
            data: a.scores,
            borderColor: modelColor(a.model),
            backgroundColor: modelColor(a.model, 0.12),
            fill: true,
            tension: 0.4,
            pointRadius: 2,
            borderWidth: 2,
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: { x: { display: false }, y: { display: false, min: 0, max: 100 } },
        },
      }));
    });
  }

  function populateStats() {
    const aggs = modelAggregates(state.data);
    const top = aggs.length ? Math.max(...aggs.map((a) => a.avgScore)) : 0;
    const el = (id, v) => { const e = $(id); if (e) e.textContent = v; };
    el("#statModels", uniqueModels(state.data).length);
    el("#statBenchmarks", BENCHMARKS.length);
    el("#statRuns", state.data.length);
    el("#statTopScore", top ? top.toFixed(1) : "—");
  }

  function initMobileNav() {
    const toggle = $("#navToggle");
    const nav = $("#siteNav");
    if (!toggle || !nav) return;
    toggle.style.display = "block";
    toggle.addEventListener("click", () => {
      const open = nav.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", String(open));
    });
    nav.querySelectorAll("a").forEach((a) => a.addEventListener("click", () => {
      nav.classList.remove("is-open");
      toggle.setAttribute("aria-expanded", "false");
    }));
  }

  function initReveal() {
    const targets = $$(".reveal");
    if (!targets.length) return;
    const io = new IntersectionObserver((entries) => {
      entries.forEach((e) => { if (e.isIntersecting) { e.target.classList.add("is-revealed"); io.unobserve(e.target); } });
    }, { threshold: 0.12, rootMargin: "0px 0px -40px 0px" });
    targets.forEach((t) => io.observe(t));
  }

  function initGpuBackground() {
    const canvas = $("#gpuCanvas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    let w, h, particles;
    function resize() {
      w = canvas.width = window.innerWidth;
      h = canvas.height = window.innerHeight;
      particles = Array.from({ length: 36 }, () => ({
        x: Math.random() * w,
        y: Math.random() * h,
        vx: (Math.random() - 0.5) * 0.35,
        vy: (Math.random() - 0.5) * 0.35 - 0.15,
        r: Math.random() * 2.5 + 1,
        a: Math.random() * 0.4 + 0.1,
      }));
    }
    let frame = 0;
    function draw() {
      if (!ctx) return;
      ctx.clearRect(0, 0, w, h);
      for (const p of particles) {
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < -20) p.x = w + 20;
        if (p.x > w + 20) p.x = -20;
        if (p.y < -20) p.y = h + 20;
        if (p.y > h + 20) p.y = -20;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(0, 212, 170, ${p.a})`;
        ctx.fill();
      }
      frame = requestAnimationFrame(draw);
    }
    resize();
    draw();
    window.addEventListener("resize", resize);
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)");
    reduced.addEventListener?.("change", () => { if (reduced.matches && frame) cancelAnimationFrame(frame); else if (!frame) draw(); });
  }

  function initWaapiScores() {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const io = new IntersectionObserver((entries) => {
      entries.forEach((e) => {
        if (e.isIntersecting) {
          const bar = e.target;
          requestAnimationFrame(() => bar.classList.add("is-scored"));
          io.unobserve(bar);
        }
      });
    }, { threshold: 0.5 });
    $$(".score-bar").forEach((b) => io.observe(b));
  }

  async function init() {
    initMobileNav();
    await loadData();
    renderLeaderboardChart();
    renderCostValueChart();
    initTableControls();
    renderTable();
    renderComparison();
    populateStats();
    initReveal();
    initGpuBackground();
    initWaapiScores();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
