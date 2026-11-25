(function () {
  var B = window.BENCH, main = document.getElementById('main');
  var esc = function (s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); };
  var money = function (v) { return v == null ? 'n/a' : '$' + (v < 0.01 ? v.toFixed(4) : v.toFixed(2)); };
  var num = function (v) { return v == null ? 'n/a' : Number(v).toLocaleString('en-US'); };

  var TABS = {
    alpaca: {
      title: 'Alpaca walking',
      lede: 'Can the model build one beautiful animated component from a single prompt? Each card below is the model\'s own HTML, running live.',
      how: 'One prompt, one attempt, full output budget. The page is rendered in headless Chrome at 1280x720 and captured at three moments of the walk. Two judge models that are not contestants (' + B.judges.join(', ') + ') score alpaca likeness, motion, beauty and scene from 0 to 10; the score is the average, out of 100. "Motion" under each card is the measured pixel change between frames, so a still image cannot score well by looking pretty.'
    },
    design: {
      title: 'Front-end design',
      lede: 'One prompt for a complete landing page: "Dune Line", an overnight desert train to a neon city. Click any card to open the real page.',
      how: 'One prompt, one attempt, full output budget. Required: nav, hero, three features, a four-departure timetable, three pricing tiers, a testimonial and a footer. A full-page screenshot at 1280px is scored by the same two judges on typography, layout, colour, completeness and originality.'
    },
    recreate: {
      title: 'Image recreation',
      lede: 'The model looks at the original image and writes a prompt to recreate it. The same image model then paints that prompt. Closer to the original is better.',
      how: 'The original was made once with ' + B.image_model + '. Each contestant sees only the image and writes a prompt of at most 250 words. That prompt goes to ' + B.image_model + ' unchanged, one attempt. The two judges compare original and recreation on subjects, layout, colour, style and overall likeness. Image models are random, so small gaps between neighbours are noise.'
    },
    speed: {
      title: 'Tokens per second',
      lede: 'How fast does text actually arrive? Same 500-word writing task for every model, streamed, three runs.',
      how: 'Tokens per second = billed output tokens (including hidden reasoning tokens) divided by total wall-clock seconds from request to last token. The figure is the median of three runs; the range shows the slowest and fastest run. Time to first word is how long you wait before visible text starts. Measured from one machine on one evening, so treat it as a snapshot.'
    },
    value: {
      title: 'Value per token',
      lede: 'How much correct work does each output token buy? Twelve questions with exact answers, checked by code, no judge.',
      how: 'Twelve short questions (arithmetic, counting, dates, number theory) whose answers were computed in Python. Value per token = correct answers per 1,000 billed output tokens, reasoning tokens included. A model that thinks for 8,000 tokens to get the same answers as one that uses 800 scores a tenth as much. Correct per $1 is correct answers divided by what that one call cost at the live Venice price (input plus output tokens), so it folds in the price of a token as well as the number of them. The value index combines the two: each axis is scaled so the best model on it scores 100, and the index is their geometric mean, so a model has to be both parsimonious and cheap to rank well. The table is still ranked by correct answers per 1,000 tokens.'
    }
  };

  function who(m, extra) {
    return '<div class="who"><img src="' + m.icon + '" alt="' + esc(m.lab) + ' logo"><div><div class="n">' + esc(m.name) +
      '</div><div class="l">' + esc(m.lab) + ' · released ' + m.released + '</div></div>' + (extra || '') + '</div>';
  }
  function ranked(key, field) {
    var ok = B.models.filter(function (m) { return m[key][field] != null; }).sort(function (a, b) { return b[key][field] - a[key][field]; });
    var rest = B.models.filter(function (m) { return m[key][field] == null; });
    return { ok: ok, rest: rest };
  }
  function head(t, r) {
    var missing = r.rest.length ? '<p class="notice">' + r.rest.length + ' of ' + B.models.length + ' models ' + (r.rest.length === 1 ? 'has' : 'have') + ' no score here: ' +
      r.rest.map(function (m) { return esc(m.name); }).join(', ') + '. They are listed at the end with the reason.</p>' : '';
    return '<h1>' + t.title + '</h1><p class="lede">' + t.lede + '</p><details class="how"><summary>How this is scored</summary><p>' + t.how + '</p></details>' + (B.judge_note ? '<p class="lede" style="font-size:13px">' + B.judge_note + '</p>' : '') + missing;
  }
  function crit(d) {
    if (!d.criteria) return '';
    return '<div class="crit">' + Object.keys(d.criteria).map(function (k) { return '<span>' + k + ' <b>' + d.criteria[k] + '</b></span>'; }).join('') + '</div>';
  }
  function note(d) {
    var n = d.notes && d.notes[Object.keys(d.notes)[0]];
    return n ? '<div class="note">Judge: ' + esc(n) + '</div>' : '';
  }
  function badge(d, i) {
    return '<span class="rank">#' + (i + 1) + '</span><span class="score">' + d.score + '<small>/100</small></span>';
  }
  function failCard(m, d) {
    return '<article class="card">' + who(m) + '<div class="frame fail">' + esc(d.status === 'unscored' ? 'Produced output, but it was not scored.' : (d.error || 'No result.')) + '</div></article>';
  }

  function live(key, tall) {
    var r = ranked(key, 'score'), h = head(TABS[key], r) + '<div class="grid">';
    r.ok.forEach(function (m, i) {
      var d = m[key], src = 'out/' + key + '/' + m.id + '.html';
      var inner = key === 'alpaca'
        ? '<iframe data-src="' + src + '" sandbox="allow-scripts" loading="lazy" title="' + esc(m.name) + ' alpaca"></iframe>'
        : '<img src="img/design/' + m.id + '.jpg" loading="lazy" alt="' + esc(m.name) + ' landing page">';
      h += '<article class="card' + (i === 0 ? ' win' : '') + '">' + who(m, badge(d, i)) +
        '<div class="frame' + (tall ? ' tall' : '') + '">' + inner + '<button data-open="' + src + '" data-name="' + esc(m.name) + '" aria-label="Open ' + esc(m.name) + ' output"></button><span class="hint">Click to open live</span></div>' +
        '<div class="meta">' + crit(d) + note(d) + '<div class="stats">' + num(d.out_tokens) + ' tokens · ' + money(d.cost) + ' · ' + d.seconds + 's' +
        (key === 'alpaca' && d.motion != null ? ' · motion ' + d.motion : '') + '</div></div></article>';
    });
    r.rest.forEach(function (m) { h += failCard(m, m[key]); });
    return h + '</div>';
  }

  function recreate() {
    var r = ranked('recreate', 'score');
    var h = head(TABS.recreate, r) + '<section class="source"><img src="img/source.jpg" alt="Original: a neon city rising from desert dunes at dusk"><div><h2>The original</h2><p>A neon city rising out of desert dunes at dusk: three towers, a red-cloaked traveller with an alpaca, a neon cactus by a turquoise pool, a monorail, a crescent moon. Every model below saw only this picture.</p></div></section><div class="grid">';
    r.ok.forEach(function (m, i) {
      var d = m.recreate;
      h += '<article class="card' + (i === 0 ? ' win' : '') + '">' + who(m, badge(d, i)) +
        '<div class="pair"><figure><img src="img/source.jpg" loading="lazy" alt="Original"><figcaption>Original</figcaption></figure><figure><img src="img/recon/' + m.id + '.jpg" loading="lazy" alt="Recreation by ' + esc(m.name) + '"><figcaption>' + esc(m.name) + '</figcaption></figure></div>' +
        '<div class="meta">' + crit(d) + note(d) + '<details class="p"><summary>Prompt the model wrote</summary><p>' + esc(d.prompt) + '</p></details></div></article>';
    });
    r.rest.forEach(function (m) { h += failCard(m, m.recreate); });
    return h + '</div>';
  }

  function table(key, field, cols, rowFn, barCls, unit) {
    var r = ranked(key, field), max = r.ok.length ? r.ok[0][key][field] : 1;
    var h = head(TABS[key], r) + '<p class="lede" style="font-size:13px">Click any column heading to sort; click again to reverse.</p><div class="scroll"><table class="tbl"><thead><tr><th class="sortable" data-col="0" title="Sort by rank">#</th><th class="sortable" data-col="1" title="Sort by model">Model</th><th class="sortable" data-col="2" title="Sort by ' + unit + '">' + unit + '</th>' +
      cols.map(function (c, i) { return '<th class="sortable" data-col="' + (i + 3) + '" title="Sort by ' + c + '">' + c + '</th>'; }).join('') + '</tr></thead><tbody>';
    r.ok.forEach(function (m, i) {
      var d = m[key];
      h += '<tr><td class="num">' + (i + 1) + '</td><td>' + who(m) + '</td><td><div class="bar ' + barCls + '"><i style="width:' + Math.max(3, d[field] / max * 100) + '%"></i><b>' + d[field] + '</b></div></td>' + rowFn(m, d) + '</tr>';
    });
    r.rest.forEach(function (m) {
      h += '<tr><td class="num">–</td><td>' + who(m) + '</td><td colspan="' + (cols.length + 1) + '">' + esc(m[key].error || 'No result.') + '</td></tr>';
    });
    return h + '</tbody></table></div>';
  }
  function speed() {
    return table('speed', 'tps', ['Range (3 runs)', 'Time to first word', 'Total time', 'Output price / 1M'], function (m, d) {
      return '<td class="num">' + d.tps_min + ' – ' + d.tps_max + (d.runs < 3 ? ' (' + d.runs + ' runs)' : '') + '</td><td class="num">' + d.ttft + 's</td><td class="num">' + d.seconds + 's</td><td class="num">$' + m.price_out + '</td>';
    }, '', 'Tokens / second');
  }
  function value() {
    return table('value', 'per_1k', ['Correct', 'Each Q', 'Tokens / answer', '$ / answer', 'Per $1', 'Index'], function (m, d) {
      return '<td class="num">' + d.correct + ' / ' + d.total + '</td><td><div class="dots">' + d.per_q.map(function (q) { return '<i class="' + (q ? 'ok' : '') + '"></i>'; }).join('') +
        '</div></td><td class="num">' + num(Math.round(d.out_tokens / d.correct)) + '</td><td class="num">$' + d.per_correct_cost.toFixed(5) + '</td><td class="num">' + num(d.per_dollar) + '</td><td class="num"><strong>' + d.index.toFixed(1) + '</strong><small class="idx">#' + d.index_rank + ' of ' + B.models.length + '</small></td>';
    }, 'v', 'Correct per 1,000 tokens') +
      '<p class="valuenote"><strong>Token thrift and money thrift are different things.</strong> GPT-6.2 Astra spends 35 output tokens per correct answer where Gemini 4 Neon spends 716, so Astra is 20 times more parsimonious. But Astra\'s output costs $40 per million tokens against Neon\'s $18.75, so its lead in dollars is only 8.5 times. GLM 5.3 Flash goes the other way: 142 tokens per correct answer, four times Astra\'s, yet 19 times more correct answers per dollar, because its output price is $0.55 per million. The index rewards the models that are good on both axes — it is the geometric mean, so a model that is wasteful or expensive cannot buy its way out on the other side.</p>';
  }

  function fit() {
    document.querySelectorAll('.frame iframe').forEach(function (f) {
      f.style.transform = 'scale(' + f.parentNode.clientWidth / 1280 + ')';
      if (!f.src) f.src = f.dataset.src;
    });
  }
  function show(tab) {
    if (!TABS[tab]) tab = 'alpaca';
    document.querySelectorAll('.tabs button').forEach(function (b) { b.setAttribute('aria-selected', b.dataset.tab === tab); });
    main.innerHTML = tab === 'alpaca' ? live('alpaca') : tab === 'design' ? live('design', true) : tab === 'recreate' ? recreate() : tab === 'speed' ? speed() : value();
    document.title = TABS[tab].title + ' · BenchmarkViv';
    fit();
  }

  var modal = document.getElementById('modal'), frame = document.getElementById('modal-frame');
  function close() { modal.hidden = true; frame.removeAttribute('src'); }
  document.addEventListener('click', function (e) {
    var t = e.target.closest('[data-tab]');
    if (t) { location.hash = t.dataset.tab; return; }
    var o = e.target.closest('[data-open]');
    if (o) {
      frame.src = o.dataset.open; modal.hidden = false;
      document.getElementById('modal-title').textContent = o.dataset.name;
      document.getElementById('modal-open').href = o.dataset.open;
    }
    if (e.target.id === 'modal-close' || e.target === modal) close();
  });
  function sortKey(td) {
    var dots = td.querySelectorAll('.dots .ok').length;
    if (dots) return dots;
    var t = (td.innerText || '').trim().replace(/[$,]/g, '');
    var m = t.match(/-?\d+(?:\.\d+)?/);
    var rest = t.replace(/-?\d+(?:\.\d+)?/g, '').replace(/[s%x]/g, '').trim();
    if (m && !/[A-Za-z]/.test(rest)) return parseFloat(m[0]);
    return t.toLowerCase();
  }
  document.addEventListener('click', function (e) {
    var th = e.target.closest('th.sortable');
    if (!th) return;
    var table = th.closest('table'), tb = table.tBodies[0];
    if (!tb) return;
    var col = Number(th.dataset.col);
    var rows = Array.prototype.slice.call(tb.rows);
    var good = rows.filter(function (r) { return r.cells.length > 2; });
    var bad = rows.filter(function (r) { return r.cells.length <= 2; });
    var numeric = good.length && good.every(function (r) { return typeof sortKey(r.cells[col]) === 'number'; });
    var dir = th.dataset.dir === 'desc' ? 1 : th.dataset.dir === 'asc' ? -1 : (numeric ? -1 : 1);
    table.querySelectorAll('th.sortable').forEach(function (h) { if (h !== th) { h.removeAttribute('data-dir'); h.removeAttribute('aria-sort'); } });
    th.dataset.dir = dir === 1 ? 'asc' : 'desc';
    th.setAttribute('aria-sort', dir === 1 ? 'ascending' : 'descending');
    good.sort(function (a, b) {
      var x = sortKey(a.cells[col]), y = sortKey(b.cells[col]);
      if (typeof x === 'string' || typeof y === 'string') return dir * String(x).localeCompare(String(y));
      return dir * (x - y);
    });
    good.concat(bad).forEach(function (r) { tb.appendChild(r); });
  });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') close(); });
  window.addEventListener('hashchange', function () { show(location.hash.slice(1)); window.scrollTo(0, 0); });
  window.addEventListener('resize', fit);
  document.getElementById('foot').textContent = 'Run ' + B.generated + ' through the Venice API. One scored attempt per model per test, nothing cherry-picked. A call was repeated only when the connection failed before the model finished (API spend limit, or Venice closing the stream at 15 minutes). Contestant calls cost $' + B.contestant_spend + '.' + (B.run_note ? ' ' + B.run_note : '');
  show(location.hash.slice(1));
})();
