/* BenchmarkViv — assets/app.js */
(() => {
  "use strict";

  const DATA_URL = "data/results.json";

  // Chart tracks: 5-track VivIndex core + pharma domain tracks (pharma not in VivIndex weights).
  const BENCHMARKS = [
    { id: "intent-understanding", label: "Intent Understanding" },
    { id: "one-shot-ui", label: "One-Shot UI" },
    { id: "startup-in-a-weekend", label: "Startup in a Weekend" },
    { id: "pharma-drug-interaction", label: "Pharma DDI" },
    { id: "pharma-regulatory-comprehension", label: "Pharma Regulatory" },
    { id: "value-density", label: "Value Density @1K" },
    { id: "reverse-prompt-vision", label: "Reverse-Prompt Vision" },
  ];

  // One saturated, accessible identity per model. These values are used in every chart.
  const MODEL_COLORS = {
    "GPT-5.6 Luna":      "#2563EB",
    "GPT-5.6 Luna Pro":  "#7C3AED",
    "GPT-5.6 Sol":       "#F97316",
    "GPT-5.6 Sol Pro":   "#DC2626",
    "GPT-5.6 Terra":     "#10B981",
    "GPT-5.6 Terra Pro": "#00A6A6",
    "GPT-5.5":           "#E11D74",
    "Fable 5":           "#84A800",
    "Opus 4.8":          "#9333EA",
    "Opus 5":            "#6D28D9",
    "GLM 5.2":           "#EC4899",
    "DeepSeek V4":       "#0891B2",
    "MiniMax M3":        "#D97706",
    "Grok 4.5":          "#4F46E5",
    "Inkling":           "#0EA5E9",
    "Kimi K3":           "#F59E0B",
  };

  const FALLBACK_DATA = { generated: "", source: "fallback", results: [] };

  // VivIndex remains the original four-track composite. Pharma tracks are shown in
  // charts/profiles but do not enter VivIndex weights (methodology stays stable).
  // VivIndex core five: classic capability + the two new measures (value density, reverse-prompt vision).
  // Pharma tracks stay on charts/profiles only. Missing scores renormalize weights (non-vision reverse-prompt = partial coverage).
  const VIVINDEX_WEIGHTS = {
    "intent-understanding": 0.20,
    "one-shot-ui": 0.15,
    "startup-in-a-weekend": 0.25,
    "value-density": 0.20,
    "reverse-prompt-vision": 0.20,
  };
  const VIVINDEX_TRACK_COUNT = Object.keys(VIVINDEX_WEIGHTS).length;

  const state = {
    data: [],
    runSummary: { attempted: 0, scored: 0, excluded: 0 },
    isLive: false,
    sort: { key: "score", dir: -1 },
    filter: { text: "", benchmark: "all" },
    charts: { leaderboard: null, benchmark: null, costValue: null, vivIndex: null, speed: null, latency: null, valueDensity: null, reversePrompt: null, sparklines: [] },
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
      // VivIndex: weighted composite over benchmarks present, renormalized.
      let wSum = 0, wTotal = 0;
      mr.forEach((r) => {
        const w = VIVINDEX_WEIGHTS[r.benchmark];
        if (w != null && r.score != null) { wSum += r.score * w; wTotal += w; }
      });
      const vivIndex = wTotal > 0 ? wSum / wTotal : 0;
      const trackCount = mr.filter((r) => VIVINDEX_WEIGHTS[r.benchmark] != null && r.score != null).length;
      const fullCoverage = trackCount >= VIVINDEX_TRACK_COUNT;
      // Output speed: total completion tokens / total generation time.
      const speedRows = mr.filter((r) => r.completionTokens > 0 && r.latency > 0);
      const tokensPerSec = speedRows.length
        ? speedRows.reduce((a, r) => a + r.completionTokens, 0) / speedRows.reduce((a, r) => a + r.latency, 0)
        : null;
      return {
        model,
        vivIndex,
        trackCount,
        fullCoverage,
        tokensPerSec,
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

  function median(nums) {
    const s = nums.slice().sort((a, b) => a - b);
    if (!s.length) return 0;
    const m = Math.floor(s.length / 2);
    return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
  }

  function modelColor(model, alpha = 1) {
    const hex = MODEL_COLORS[model] || "#94a3b8";
    if (alpha >= 1) return hex;
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  }

  // JSON benchmark ids use underscores; the UI uses hyphens.
  const ID_ALIASES = { "startup_in_a_weekend": "startup-in-a-weekend" };
  function normalizeId(id) {
    const n = String(id).replace(/_/g, "-");
    return ID_ALIASES[n] || n;
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

      const scored = json.results.filter((r) => {
        // An API timeout or other failed call is not a score of zero. Keep it
        // out of all score, latency, and cost aggregates while retaining its
        // existence in the completeness indicator below.
        const status = r.status == null ? "ok" : String(r.status).toLowerCase();
        return ["ok", "success", "completed"].includes(status) && Number.isFinite(Number(r.score));
      });
      state.runSummary = {
        attempted: json.results.length,
        scored: scored.length,
        excluded: json.results.length - scored.length,
      };
      state.data = scored.map((r) => ({
        model: modelMap[r.model_id] || r.model_id || r.model,
        benchmark: normalizeId(r.benchmark_id || r.benchmark),
        score: r.score,
        latency: r.latency,
        tokens: r.total_tokens || r.tokens,
        completionTokens: r.completion_tokens || (r.tokens ? Math.round(r.tokens * 0.55) : null),
        cost: r.estimated_cost_usd || r.cost,
      }));
      state.isLive = true;
      if (status) {
        status.textContent = `● ${state.runSummary.scored}/${state.runSummary.attempted} scored runs`;
        status.classList.remove("fallback");
      }
    } catch (err) {
      console.warn("[BenchmarkViv] fallback data:", err.message);
      state.data = FALLBACK_DATA.results;
      state.runSummary = { attempted: 0, scored: 0, excluded: 0 };
      state.isLive = false;
      if (status) {
        status.textContent = "● Results unavailable";
        status.classList.add("fallback");
      }
    }
  }

  function renderVivIndexChart() {
    const canvas = $("#vivIndexChart");
    if (!canvas || typeof Chart === "undefined") return;
    // Full-coverage models ranked first; partial-coverage models shown
    // separately (hatched) so renormalization can't inflate their rank.
    const aggs = modelAggregates(state.data).sort((a, b) =>
      (b.fullCoverage - a.fullCoverage) || (b.vivIndex - a.vivIndex));
    if (state.charts.vivIndex) state.charts.vivIndex.destroy();
    state.charts.vivIndex = new Chart(canvas, {
      type: "bar",
      data: {
        labels: aggs.map((a) => a.fullCoverage ? a.model : `${a.model} (${a.trackCount}/${VIVINDEX_TRACK_COUNT} VivIndex tracks)`),
        datasets: [{
          label: "VivIndex",
          data: aggs.map((a) => Number(a.vivIndex.toFixed(1))),
          backgroundColor: aggs.map((a) => modelColor(a.model, a.fullCoverage ? 0.78 : 0.28)),
          borderColor: aggs.map((a) => modelColor(a.model)),
          borderWidth: 1.5,
          borderDash: [4, 3],
          borderRadius: 6,
          maxBarThickness: 34,
        }],
      },
      options: {
        indexAxis: "y",
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (ctx) => {
                const a = aggs[ctx.dataIndex];
                const base = ` VivIndex: ${ctx.raw} (weighted: startup 25%, intent 20%, value density 20%, reverse-prompt 20%, UI 15%)`;
                return a.fullCoverage ? base : [base, ` ⚠ Partial VivIndex coverage: ${a.trackCount} of ${VIVINDEX_TRACK_COUNT} core tracks`];
              },
            },
          },
        },
        scales: {
          x: { min: 0, max: 100, grid: { color: "rgba(18,18,26,0.08)" }, ticks: { color: "rgba(18,18,26,0.55)" } },
          y: { grid: { display: false }, ticks: { color: "rgba(18,18,26,0.75)" } },
        },
      },
    });
  }

  // Draws the shaded "most attractive quadrant" (low cost, high score)
  // plus dashed median guides on the score-vs-cost scatter.
  const quadrantPlugin = {
    id: "quadrant",
    beforeDatasetsDraw(chart, _args, opts) {
      if (!opts || opts.xMid == null || opts.yMid == null) return;
      const { ctx, chartArea, scales } = chart;
      const x = scales.x.getPixelForValue(opts.xMid);
      const y = scales.y.getPixelForValue(opts.yMid);
      ctx.save();
      ctx.fillStyle = "rgba(225, 29, 116, 0.08)";
      ctx.fillRect(chartArea.left, chartArea.top, Math.max(0, x - chartArea.left), Math.max(0, y - chartArea.top));
      ctx.strokeStyle = "rgba(18, 18, 26, 0.18)";
      ctx.setLineDash([5, 4]);
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(x, chartArea.top);
      ctx.lineTo(x, chartArea.bottom);
      ctx.moveTo(chartArea.left, y);
      ctx.lineTo(chartArea.right, y);
      ctx.stroke();
      ctx.setLineDash([]);
      ctx.fillStyle = "rgba(18, 18, 26, 0.72)";
      ctx.font = "600 11px Geist, sans-serif";
      ctx.fillText("Most attractive quadrant", chartArea.left + 8, chartArea.top + 16);
      ctx.restore();
    },
  };

  function renderSpeedCharts() {
    const speedCanvas = $("#speedChart");
    const latencyCanvas = $("#latencyChart");
    if (typeof Chart === "undefined") return;
    const aggs = modelAggregates(state.data);

    if (speedCanvas) {
      const rows = aggs.filter((a) => a.tokensPerSec != null).sort((a, b) => b.tokensPerSec - a.tokensPerSec);
      if (state.charts.speed) state.charts.speed.destroy();
      state.charts.speed = new Chart(speedCanvas, {
        type: "bar",
        data: {
          labels: rows.map((a) => a.model),
          datasets: [{
            label: "Output tokens/sec",
            data: rows.map((a) => Number(a.tokensPerSec.toFixed(1))),
            backgroundColor: rows.map((a) => modelColor(a.model, 0.75)),
            borderColor: rows.map((a) => modelColor(a.model)),
            borderWidth: 1.5,
            borderRadius: 6,
            maxBarThickness: 56,
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false }, tooltip: { callbacks: { label: (c) => ` ${c.raw} tok/s (higher is better)` } } },
          scales: {
            y: { beginAtZero: true, title: { display: true, text: "Tokens per second" }, grid: { color: "rgba(18,18,26,0.08)" }, ticks: { color: "rgba(18,18,26,0.55)" } },
            x: { grid: { display: false }, ticks: { color: "rgba(18,18,26,0.75)" } },
          },
        },
      });
    }

    if (latencyCanvas) {
      const rows = aggs.filter((a) => a.avgLatency > 0).sort((a, b) => a.avgLatency - b.avgLatency);
      if (state.charts.latency) state.charts.latency.destroy();
      state.charts.latency = new Chart(latencyCanvas, {
        type: "bar",
        data: {
          labels: rows.map((a) => a.model),
          datasets: [{
            label: "Avg response time (s)",
            data: rows.map((a) => Number(a.avgLatency.toFixed(1))),
            backgroundColor: rows.map((a) => modelColor(a.model, 0.75)),
            borderColor: rows.map((a) => modelColor(a.model)),
            borderWidth: 1.5,
            borderRadius: 6,
            maxBarThickness: 56,
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false }, tooltip: { callbacks: { label: (c) => ` ${c.raw}s avg end-to-end (lower is better)` } } },
          scales: {
            y: { beginAtZero: true, title: { display: true, text: "Seconds (lower is better)" }, grid: { color: "rgba(18,18,26,0.08)" }, ticks: { color: "rgba(18,18,26,0.55)" } },
            x: { grid: { display: false }, ticks: { color: "rgba(18,18,26,0.75)" } },
          },
        },
      });
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
          y: { min: 0, max: 100, grid: { color: "rgba(18,18,26,0.08)" }, ticks: { color: "rgba(18,18,26,0.55)" } },
          x: { grid: { display: false }, ticks: { color: "rgba(18,18,26,0.75)" } },
        },
      },
    });
  }

  function renderBenchmarkChart() {
    const canvas = $("#benchmarkChart");
    if (!canvas || typeof Chart === "undefined") return;
    const models = uniqueModels(state.data);
    if (state.charts.benchmark) state.charts.benchmark.destroy();
    state.charts.benchmark = new Chart(canvas, {
      type: "bar",
      data: {
        labels: BENCHMARKS.map((b) => b.label),
        datasets: models.map((model) => ({
          label: model,
          data: BENCHMARKS.map((b) => {
            const row = state.data.find((r) => r.model === model && r.benchmark === b.id);
            return row ? row.score : null;
          }),
          backgroundColor: modelColor(model, 0.72),
          borderColor: modelColor(model),
          borderWidth: 1,
          borderRadius: 4,
        })),
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: "index", intersect: false },
        plugins: {
          legend: { position: "bottom", labels: { usePointStyle: true, boxWidth: 8, padding: 14 } },
          tooltip: { callbacks: { label: (ctx) => ` ${ctx.dataset.label}: ${ctx.raw ?? "not run"}` } },
        },
        scales: {
          x: { stacked: false, grid: { display: false }, ticks: { color: "rgba(18,18,26,0.78)", maxRotation: 0 } },
          y: { min: 0, max: 100, title: { display: true, text: "Score / 100" }, grid: { color: "rgba(18,18,26,0.09)" }, ticks: { color: "rgba(18,18,26,0.62)" } },
        },
      },
    });
  }

  function renderCostValueChart() {
    const canvas = $("#costValueChart");
    if (!canvas || typeof Chart === "undefined") return;
    const aggs = modelAggregates(state.data);
    const xMid = median(aggs.map((a) => a.avgCost));
    const yMid = median(aggs.map((a) => a.vivIndex));
    if (state.charts.costValue) state.charts.costValue.destroy();
    state.charts.costValue = new Chart(canvas, {
      type: "scatter",
      data: {
        datasets: aggs.map((a) => ({
          label: a.model,
          data: [{ x: Number(a.avgCost.toFixed(4)), y: Number(a.vivIndex.toFixed(1)) }],
          backgroundColor: modelColor(a.model, 0.65),
          borderColor: modelColor(a.model),
          borderWidth: 2,
          pointRadius: 8,
          pointHoverRadius: 10,
        })),
      },
      plugins: [quadrantPlugin],
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          quadrant: { xMid, yMid },
          legend: { position: "bottom", labels: { usePointStyle: true, boxWidth: 8 } },
          tooltip: {
            callbacks: {
              label: (ctx) => [
                ` ${ctx.dataset.label}`,
                ` Avg cost/run: $${ctx.raw.x.toFixed(3)}`,
                ` VivIndex: ${ctx.raw.y.toFixed(1)}`,
              ],
            },
          },
        },
        scales: {
          x: {
            type: "logarithmic",
            title: { display: true, text: "Avg cost per run (USD, log) — left is cheaper", color: "rgba(18,18,26,0.55)" },
            grid: { color: "rgba(18,18,26,0.08)" },
            ticks: { color: "rgba(18,18,26,0.55)" },
          },
          y: {
            min: 40,
            max: 100,
            title: { display: true, text: "VivIndex (weighted composite)", color: "rgba(18,18,26,0.55)" },
            grid: { color: "rgba(18,18,26,0.08)" },
            ticks: { color: "rgba(18,18,26,0.55)" },
          },
        },
      },
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
        <div class="score">${a.vivIndex.toFixed(1)}<small style="font-size:.45em;color:var(--ink-2);font-weight:500"> VivIndex</small></div>
        <dl>
          <div><dt>Latency</dt><dd>${a.avgLatency.toFixed(1)}s</dd></div>
          <div><dt>Cost/run</dt><dd>$${a.avgCost.toFixed(3)}</dd></div>
          <div><dt>Speed</dt><dd>${a.tokensPerSec != null ? a.tokensPerSec.toFixed(0) + " tok/s" : "—"}</dd></div>
        </dl>
        <div class="spark-wrap"><canvas></canvas></div>
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


  function renderValueDensityChart() {
    const canvas = $("#valueDensityChart");
    if (!canvas || typeof Chart === "undefined") return;
    const rows = state.data.filter((r) => r.benchmark === "value-density" && r.score != null && r.tokens > 0);
    if (!rows.length) return;
    const byModel = {};
    rows.forEach((r) => {
      const v = r.tokens ? r.score / (r.tokens / 1000) : 0;
      byModel[r.model] = { score: r.score, tokens: r.tokens, yield: v, cost: r.cost };
    });
    const aggs = Object.entries(byModel).map(([model, m]) => ({ model, ...m }))
      .sort((a, b) => b.yield - a.yield);
    if (state.charts.valueDensity) state.charts.valueDensity.destroy();
    state.charts.valueDensity = new Chart(canvas, {
      type: "bar",
      data: {
        labels: aggs.map((a) => a.model),
        datasets: [{
          label: "Checklist score per 1K tokens",
          data: aggs.map((a) => Number(a.yield.toFixed(2))),
          backgroundColor: aggs.map((a) => modelColor(a.model, 0.75)),
          borderColor: aggs.map((a) => modelColor(a.model)),
          borderWidth: 1.5,
          borderRadius: 6,
          maxBarThickness: 48,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (ctx) => {
                const a = aggs[ctx.dataIndex];
                return [
                  ` Yield: ${ctx.raw} score / 1K tok`,
                  ` Score: ${a.score}`,
                  ` Tokens: ${Math.round(a.tokens)}`,
                  ` Cost: $${(a.cost || 0).toFixed(4)}`,
                ];
              },
            },
          },
        },
        scales: {
          y: { beginAtZero: true, title: { display: true, text: "Score per 1K total tokens" }, grid: { color: "rgba(18,18,26,0.08)" } },
          x: { grid: { display: false } },
        },
      },
    });
  }

  function renderReversePromptChart() {
    const canvas = $("#reversePromptChart");
    if (!canvas || typeof Chart === "undefined") return;
    const rows = state.data.filter((r) => r.benchmark === "reverse-prompt-vision" && r.score != null);
    if (!rows.length) return;
    const aggs = rows.map((r) => ({ model: r.model, score: r.score }))
      .sort((a, b) => b.score - a.score);
    if (state.charts.reversePrompt) state.charts.reversePrompt.destroy();
    state.charts.reversePrompt = new Chart(canvas, {
      type: "bar",
      data: {
        labels: aggs.map((a) => a.model),
        datasets: [{
          label: "Reverse-prompt fidelity",
          data: aggs.map((a) => a.score),
          backgroundColor: aggs.map((a) => modelColor(a.model, 0.75)),
          borderColor: aggs.map((a) => modelColor(a.model)),
          borderWidth: 1.5,
          borderRadius: 6,
          maxBarThickness: 48,
        }],
      },
      options: {
        indexAxis: "y",
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { min: 0, max: 100, grid: { color: "rgba(18,18,26,0.08)" } },
          y: { grid: { display: false } },
        },
      },
    });
  }

  function populateStats() {
    const aggs = modelAggregates(state.data);
    const top = aggs.length ? aggs.reduce((best, a) => (a.vivIndex > best.vivIndex ? a : best)) : null;
    const el = (id, v) => { const e = $(id); if (e) e.textContent = v; };
    el("#statModels", uniqueModels(state.data).length);
    el("#statBenchmarks", BENCHMARKS.length);
    el("#statRuns", `${state.runSummary.scored}/${state.runSummary.attempted}`);
    el("#statTopScore", top ? top.vivIndex.toFixed(1) : "—");
    // Average estimated full-suite cost across models with scored runs.
    const suiteCosts = uniqueModels(state.data).map((model) => {
      const rows = state.data.filter((r) => r.model === model && r.cost != null);
      return rows.reduce((a, r) => a + r.cost, 0);
    }).filter((n) => n > 0);
    const avgSuite = suiteCosts.length ? suiteCosts.reduce((a, b) => a + b, 0) / suiteCosts.length : null;
    el("#statCost", avgSuite != null ? avgSuite.toFixed(2) : "—");
    const leader = $("#statVivLeader");
    if (leader && top) leader.textContent = top.model;
    const dataNote = $("#dataNote span");
    if (dataNote) {
      dataNote.textContent = state.runSummary.excluded
        ? `${state.runSummary.scored} scored runs; ${state.runSummary.excluded} failed/excluded from score aggregates. Pharma tracks are charted; VivIndex uses 4 core tracks.`
        : `${state.runSummary.scored} scored runs across ${BENCHMARKS.length} tracks (${VIVINDEX_TRACK_COUNT}-track VivIndex).`;
    }
  }

  function initMobileNav() {
    const toggle = $("#navToggle");
    const nav = $("#siteNav");
    if (!toggle || !nav) return;

    // Ensure the navbar is the positioning context for the absolute drawer.
    const navbar = toggle.closest(".navbar") || document.querySelector(".navbar");
    if (navbar) navbar.style.zIndex = "400";

    // Scrim so taps outside clearly close the menu and block page scroll clicks.
    let scrim = document.getElementById("navScrim");
    if (!scrim) {
      scrim = document.createElement("button");
      scrim.type = "button";
      scrim.id = "navScrim";
      scrim.className = "nav-scrim";
      scrim.setAttribute("aria-label", "Close menu");
      document.body.appendChild(scrim);
    }

    const setOpen = (open) => {
      nav.classList.toggle("is-open", open);
      scrim.classList.toggle("is-open", open);
      toggle.setAttribute("aria-expanded", String(open));
      document.body.style.overflow = open ? "hidden" : "";
    };

    const isOpen = () => nav.classList.contains("is-open");

    toggle.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      setOpen(!isOpen());
    });

    // Prefer pointerup for mobile reliability without double-firing click on some WebViews.
    toggle.addEventListener("pointerup", (e) => {
      if (e.pointerType === "touch") {
        // click will also fire; avoid double toggle by only handling if default click path failed.
      }
    });

    scrim.addEventListener("click", (e) => {
      e.preventDefault();
      setOpen(false);
    });

    nav.querySelectorAll("a").forEach((a) =>
      a.addEventListener("click", () => setOpen(false))
    );

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && isOpen()) setOpen(false);
    });

    // Close on outside tap, but never when the tap is the toggle (toggle handles itself).
    document.addEventListener(
      "click",
      (e) => {
        if (!isOpen()) return;
        const t = e.target;
        if (nav.contains(t) || toggle.contains(t) || scrim.contains(t)) return;
        setOpen(false);
      },
      true
    );

    window.addEventListener("resize", () => {
      if (window.innerWidth > 900 && isOpen()) setOpen(false);
    });
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
        ctx.fillStyle = `rgba(0, 87, 230, ${p.a * 0.55})`;
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
    renderVivIndexChart();
    renderLeaderboardChart();
    renderBenchmarkChart();
    renderCostValueChart();
    renderSpeedCharts();
    renderValueDensityChart();
    renderReversePromptChart();
    renderComparison();
    populateStats();
    initReveal();
    initGpuBackground();
    initWaapiScores();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();

// ===== Image lightbox (Vision gallery + any .img-zoom) =====
(function initImageLightbox() {
  function ensureLightbox() {
    let box = document.getElementById("imgLightbox");
    if (box) return box;
    box = document.createElement("div");
    box.id = "imgLightbox";
    box.className = "img-lightbox";
    box.hidden = true;
    box.innerHTML =
      '<button type="button" class="img-lightbox-close" aria-label="Close">×</button>' +
      '<img id="imgLightboxImg" alt="" />' +
      '<p id="imgLightboxCap" class="img-lightbox-cap"></p>';
    document.body.appendChild(box);
    return box;
  }

  function openLightbox(src, caption) {
    if (!src) return;
    const box = ensureLightbox();
    const img = box.querySelector("#imgLightboxImg");
    const cap = box.querySelector("#imgLightboxCap");
    img.src = src;
    img.alt = caption || "Enlarged image";
    cap.textContent = caption || "";
    box.hidden = false;
    document.body.classList.add("lightbox-open");
  }

  function closeLightbox() {
    const box = document.getElementById("imgLightbox");
    if (!box) return;
    box.hidden = true;
    const img = box.querySelector("#imgLightboxImg");
    if (img) img.removeAttribute("src");
    document.body.classList.remove("lightbox-open");
  }

  document.addEventListener("click", (e) => {
    const zoom = e.target.closest(".img-zoom");
    if (zoom) {
      e.preventDefault();
      const full = zoom.getAttribute("data-full") || (zoom.querySelector("img") && zoom.querySelector("img").src);
      const caption = zoom.getAttribute("data-caption") || "";
      openLightbox(full, caption);
      return;
    }
    const box = document.getElementById("imgLightbox");
    if (!box || box.hidden) return;
    if (e.target === box || e.target.classList.contains("img-lightbox-close")) {
      closeLightbox();
    }
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeLightbox();
  });
})();

