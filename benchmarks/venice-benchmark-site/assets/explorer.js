"use strict";
(() => {
  const $ = (s, root = document) => root.querySelector(s);
  const $$ = (s, root = document) => [...root.querySelectorAll(s)];
  const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[c]);
  const norm = (id) => String(id).replace(/_/g, "-");
  const mean = (values) => values.length ? values.reduce((a, b) => a + b, 0) / values.length : null;
  const fmt = (n, digits = 1) => Number.isFinite(n) ? n.toFixed(digits) : "—";
  const money = (n) => Number.isFinite(n) ? `$${n.toFixed(3)}` : "—";
  const providers = {
    openai:["OpenAI","OA","#ede8f6","#755399"],claude:["Anthropic","A","#f6ebe3","#a26443"],deepseek:["DeepSeek","DS","#e7eff5","#3d687f"],gemini:["Google Gemini","G","#e7f0f0","#427d83"],grok:["xAI","X","#ececea","#565c56"],qwen:["Alibaba Qwen","Q","#f0e9f3","#886095"],kimi:["Moonshot Kimi","K","#f5eedf","#987a3c"],minimax:["MiniMax","M","#f4e9ec","#9b6070"],glm:["Z-AI / GLM","Z","#e4efea","#3c8068"],nvidia:["NVIDIA","N","#ebf0df","#6c843b"],mistral:["Mistral","M","#f5eae4","#a66c4b"],aion:["Aion Labs","A","#f5e8eb","#a46070"],inkling:["Inkling","I","#eaedeb","#68766b"],xiaomi:["Xiaomi","X","#f6ece2","#a37445"],stealth:["Stealth","S","#eceeeb","#727c72"],inception:["Inception Labs","I","#e7f0f1","#4b8188"],meta:["Meta","M","#e8eef5","#527a9c"],tencent:["Tencent","T","#e7eef5","#527a9c"],community:["Community","C","#eceeea","#6d786c"],other:["Independent","•","#eceeea","#6d786c"]
  };
  const state = {models:[], tracks:[], view:"models", intent:"overall", search:"", provider:"all", sort:"rank", limit:12, active:null, compare:[], track:"intent-understanding", filterOpen:false};
  const intents = {
    overall:{label:"overall performance", description:"A balanced view across five practical capabilities."},
    building:{label:"building products", description:"One-shot UI, startup planning, and practical reasoning.", tracks:["one-shot-ui","startup-in-a-weekend","intent-understanding"]},
    research:{label:"research & analysis", description:"Intent understanding, domain knowledge, and concise answers.", tracks:["intent-understanding","pharma-regulatory-comprehension","pharma-drug-interaction","value-density"]},
    speed:{label:"output speed", description:"Measured completion tokens per second across scored runs."},
    value:{label:"cost efficiency", description:"VivIndex quality relative to the average measured cost per run."}
  };

  function aggregateModels(raw) {
    const catalog = Object.fromEntries(raw.models.map(m => [m.id, m]));
    return raw.models.map(meta => {
      const rows = raw.results.filter(r => r.model_id === meta.id && ["ok","success","completed"].includes(String(r.status || "ok").toLowerCase()) && Number.isFinite(r.score));
      const scores = {};
      rows.forEach(r => { scores[norm(r.benchmark_id)] = r.score; });
      const weighted = state.tracks.filter(t => t.inVivIndex && Number.isFinite(scores[t.id]));
      const totalWeight = weighted.reduce((sum, t) => sum + t.weight, 0);
      const viv = totalWeight ? weighted.reduce((sum,t) => sum + scores[t.id] * t.weight, 0) / totalWeight : null;
      const speedRows = rows.filter(r => r.completion_tokens > 0 && r.latency > 0);
      const speed = speedRows.length ? speedRows.reduce((s,r) => s+r.completion_tokens,0) / speedRows.reduce((s,r) => s+r.latency,0) : null;
      return {id:meta.id, name:meta.display, provider:meta.provider || "other", providerLabel:meta.providerLabel || providers[meta.provider]?.[0] || "Independent", scores, viv, coverage:weighted.length, speed, latency:mean(rows.map(r=>r.latency).filter(Number.isFinite)), cost:mean(rows.map(r=>r.estimated_cost_usd).filter(Number.isFinite))};
    });
  }

  function scoreFor(model) {
    if (state.intent === "speed") return model.speed;
    if (state.intent === "value") return model.viv != null && model.cost > 0 ? model.viv / model.cost : null;
    const cfg = intents[state.intent];
    if (!cfg.tracks) return model.viv;
    const present = cfg.tracks.filter(t => Number.isFinite(model.scores[t]));
    return present.length ? mean(present.map(t => model.scores[t])) : null;
  }
  function rankedModels() {
    return state.models.filter(m => (state.provider === "all" || m.provider === state.provider) && `${m.name} ${m.providerLabel}`.toLowerCase().includes(state.search.toLowerCase())).sort((a,b) => {
      if (state.sort === "alpha") return a.name.localeCompare(b.name);
      if (state.sort === "cost") return (a.cost ?? Infinity) - (b.cost ?? Infinity);
      if (state.sort === "speed") return (b.speed ?? -1) - (a.speed ?? -1);
      if (state.sort === "viv") return (b.viv ?? -1) - (a.viv ?? -1);
      return (scoreFor(b) ?? -1) - (scoreFor(a) ?? -1);
    });
  }
  function avatar(model, extra="") { const p=providers[model.provider]||providers.other; return `<span class="provider-avatar ${extra}" style="--avatar-bg:${p[2]};--avatar-color:${p[3]};--avatar-line:${p[2]}" aria-hidden="true">${esc(p[1])}</span>`; }
  function currentScoreLabel() { return state.intent === "speed" ? "TOK / SEC" : state.intent === "value" ? "SCORE / $" : state.intent === "overall" ? "VIVINDEX" : "MATCH SCORE"; }
  function displayScore(model) { const s=scoreFor(model); if(!Number.isFinite(s)) return {value:"—",percent:0}; if(state.intent==="speed") return {value:fmt(s),percent:Math.min(s/state.models.reduce((m,x)=>Math.max(m,x.speed||0),1)*100,100)}; if(state.intent==="value") return {value:fmt(s,0),percent:Math.min(s/1500*100,100)}; return {value:fmt(s),percent:s}; }

  function renderRanking() {
    const models=rankedModels();
    const visible=models.slice(0,state.limit);
    $("#resultCount").textContent=models.length;
    $("#resultDescription").textContent=`ranked by ${intents[state.intent].label}`;
    $("#rankMetricLabel").textContent=currentScoreLabel();
    $("#explorerScope").textContent=state.intent==="overall"?"All models":intents[state.intent].label[0].toUpperCase()+intents[state.intent].label.slice(1);
    $("#emptyState").hidden=models.length>0;
    $("#rankingRows").innerHTML=visible.map((m,i)=>{
      const s=displayScore(m), active=state.active===m.id, compared=state.compare.includes(m.id);
      return `<article class="ranking-row ${active?"is-active":""}" data-model="${esc(m.id)}"><button class="model-cell" data-action="inspect" aria-label="Inspect ${esc(m.name)}" aria-expanded="${active}"><span class="rank-number">${String(i+1).padStart(2,"0")}</span>${avatar(m)}<span class="model-info"><span class="model-name">${esc(m.name)}</span><span class="model-provider">${esc(m.providerLabel)}${m.coverage<5?` · ${m.coverage}/5 tracks`:""}</span></span></button><div class="metric-cell"><span class="metric-score">${s.value}</span><span class="score-track" aria-hidden="true"><i style="width:${s.percent}%"></i></span></div><div class="metric-cell metric-secondary">${money(m.cost)}<small>avg / run</small></div><div class="metric-cell metric-secondary">${Number.isFinite(m.speed)?fmt(m.speed):"—"}<small>tokens / sec</small></div><button class="compare-check" data-action="compare" aria-label="${compared?"Remove":"Add"} ${esc(m.name)} ${compared?"from":"to"} comparison" aria-pressed="${compared}" title="${compared?"Remove from":"Add to"} comparison"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m5 12 4 4L19 6"/></svg></button></article>`;
    }).join("");
    const remaining=Math.max(0,models.length-state.limit);
    $("#showMore").hidden=remaining===0;
    $("#showMore").innerHTML=`Show all ${remaining} more models <span aria-hidden="true">↓</span>`;
    $("#selectionHint").textContent=state.compare.length?`${state.compare.length} of 3 selected · Compare now`:"Select up to 3 to compare";
    $("#compareTabCount").hidden=!state.compare.length;
    $("#compareTabCount").textContent=state.compare.length;
    const filters=(state.provider!=="all")+!!state.search;
    $("#filterBadge").hidden=!filters; $("#filterBadge").textContent=filters;
    if (state.active) { const m=models.find(x=>x.id===state.active)||state.models.find(x=>x.id===state.active); if(m) renderInsight(m); }
  }
  function renderInsight(m) {
    const ranked=rankedModels(); const rank=ranked.findIndex(x=>x.id===m.id)+1;
    const tracks=state.tracks.filter(t=>!t.retired).map(t=>({...t,score:m.scores[t.id]})).sort((a,b)=>(b.score??-1)-(a.score??-1));
    $("#insightContent").innerHTML=`<div class="insight-provider">${avatar(m)} ${esc(m.providerLabel)}</div><h3>${esc(m.name)}</h3><div class="insight-score"><div><strong>${displayScore(m).value}</strong><span> ${currentScoreLabel().toLowerCase()}</span></div>${rank?`<span class="rank-tag">#${rank} match</span>`:""}</div><div class="insight-strengths">${tracks.slice(0,5).map(t=>`<div class="strength-row"><span>${esc(t.short)}</span><div class="strength-track"><i style="width:${t.score||0}%"></i></div><b>${Number.isFinite(t.score)?fmt(t.score,0):"—"}</b></div>`).join("")}</div><dl class="insight-facts"><div><dt>Average run cost</dt><dd>${money(m.cost)}</dd></div><div><dt>Output speed</dt><dd>${Number.isFinite(m.speed)?fmt(m.speed)+" tok/s":"—"}</dd></div></dl><div class="insight-actions"><button class="insight-compare" data-insight-compare="${esc(m.id)}">${state.compare.includes(m.id)?"✓ In comparison":"+ Compare model"}</button><button class="profile-link" data-insight-profile="${esc(m.id)}">Full profile ↗</button></div>`;
  }
  function setView(view) {
    state.view=view;
    $$(".view-tab").forEach(b=>{const active=b.dataset.view===view;b.classList.toggle("active",active);b.setAttribute("aria-selected",String(active));b.tabIndex=active?0:-1;});
    $$("[role=tabpanel]").forEach(p=>p.tabIndex=0);
    $("#modelsView").hidden=view!=="models";$("#compareView").hidden=view!=="compare";$("#tracksView").hidden=view!=="tracks";
    if(view==="compare")renderCompare();if(view==="tracks")renderTrackView();
    updateURL();
  }
  function toggleCompare(id) {
    const i=state.compare.indexOf(id);
    if(i>=0)state.compare.splice(i,1);else if(state.compare.length>=3){toast("Compare up to three models at a time.");return;}else state.compare.push(id);
    renderRanking();if(state.view==="compare")renderCompare();updateURL();
  }
  function compareOptions(index) { return state.models.slice().sort((a,b)=>a.name.localeCompare(b.name)).map(m=>`<option value="${esc(m.id)}" ${state.compare[index]===m.id?"selected":""}>${esc(m.name)}</option>`).join(""); }
  function renderCompare() {
    const models=state.compare.map(id=>state.models.find(m=>m.id===id)).filter(Boolean);
    if(models.length<2){$("#compareView").innerHTML=`<div class="view-heading"><div><h2>A little perspective.</h2><p>Select two or three models from the explorer. Their quality, speed, cost, and individual track scores will line up here.</p></div><button class="text-button" data-back>Choose models ↗</button></div><div class="empty-state"><span class="empty-icon">⇄</span><h3>${models.length?"One more model to compare":"Your comparison starts here"}</h3><p>${models.length?"Add another model to see the trade-offs.":"Use the checkboxes beside any model to add it."}</p></div>`;return;}
    const rows=[{label:"VivIndex",get:m=>m.viv,format:v=>fmt(v),high:true},{label:"Output speed",get:m=>m.speed,format:v=>Number.isFinite(v)?`${fmt(v)} <small>tokens / sec</small>`:"—",high:true},{label:"Average run cost",get:m=>m.cost,format:money,high:false},{label:"Avg response time",get:m=>m.latency,format:v=>Number.isFinite(v)?`${fmt(v)}s`:"—",high:false},...state.tracks.filter(t=>!t.retired).map(t=>({label:t.short,get:m=>m.scores[t.id],format:v=>fmt(v,0),high:true}))];
    const columns=(content,cls="")=>`<div class="${cls}" role="cell">${content}</div>`;
    let html=`<div class="view-heading"><div><h2>Same work. Different strengths.</h2><p>Best values are highlighted per row. A score is only meaningful with its coverage and trade-offs.</p></div><button class="text-button" data-clear-compare>Clear comparison</button></div><div class="compare-selectors">${models.map((m,i)=>`<div class="compare-select"><label for="compareSelect${i}">MODEL ${String.fromCharCode(65+i)}</label><select id="compareSelect${i}" data-compare-select="${i}" aria-label="Comparison model ${i+1}">${compareOptions(i)}</select></div>`).join("")}</div><div class="compare-columns" role="table" aria-label="Model comparison" style="--compare-count:${models.length}"><div class="compare-grid-row" role="row">${columns("", "compare-label")}${models.map(m=>columns(`${avatar(m)}<h3>${esc(m.name)}</h3><small>${esc(m.providerLabel)}</small>`,"compare-model-head")).join("")}</div>`;
    rows.forEach(row=>{const vals=models.map(row.get),valid=vals.filter(Number.isFinite);const best=valid.length?(row.high?Math.max(...valid):Math.min(...valid)):null;html+=`<div class="compare-grid-row" role="row">${columns(row.label,"compare-label")+models.map((m,i)=>{const v=vals[i],isBest=Number.isFinite(v)&&v===best;const delta=Number.isFinite(v)&&Number.isFinite(vals[0])&&i>0?((v-vals[0])*(row.high?1:-1)):null;return columns(`${row.format(v)}${delta!==null?`<span class="delta-value ${delta>=0?"positive":"negative"}">${delta>=0?"+":""}${fmt(delta)} vs A</span>`:""}`,"compare-value"+(isBest?" best":""));}).join("")}</div>`;});
    $("#compareView").innerHTML=html+"</div>";
  }
  function renderTrackView() {
    const active=state.tracks.find(t=>t.id===state.track)||state.tracks[0];
    const top=state.models.filter(m=>Number.isFinite(m.scores[active.id])).sort((a,b)=>b.scores[active.id]-a.scores[active.id]).slice(0,10);
    $("#tracksView").innerHTML=`<div class="view-heading"><div><h2>One capability at a time.</h2><p>Choose a track to see its leaders. Experimental and partial tracks are labeled — never treated as full-roster results.</p></div></div><div class="track-view-list">${state.tracks.filter(t=>!t.retired).map((t,i)=>trackCard(t,i,true)).join("")}</div><div class="track-results"><h3>${esc(active.name)} <span class="section-kicker" style="display:inline;margin-left:10px">${active.scoredRuns} scored runs</span></h3><div class="track-bars">${top.map(m=>`<div class="track-bar-row"><span>${esc(m.name)}</span><div class="track-bar"><i style="width:${m.scores[active.id]}%"></i></div><b>${fmt(m.scores[active.id],0)}</b></div>`).join("")}</div></div>`;
  }
  function trackCard(t,i,interactive=false) { const leader=state.models.filter(m=>Number.isFinite(m.scores[t.id])).sort((a,b)=>b.scores[t.id]-a.scores[t.id])[0];return `<${interactive?"button":"article"} class="track-card ${state.track===t.id&&interactive?"active":""}" ${interactive?`data-track="${esc(t.id)}"`:""}><div class="track-card-head"><h3>${esc(t.name)}</h3><span class="track-number">${String(i+1).padStart(2,"0")}</span></div><p>${esc(t.description)}</p><div class="track-card-footer"><span class="track-kind ${t.coverage==="partial"?"partial":""}">${t.kind}${t.coverage==="partial"?" · partial":""}</span>${leader?`<span class="track-leader">Leader <b>${esc(leader.name)}</b> · ${fmt(leader.scores[t.id],0)}</span>`:""}</div></${interactive?"button":"article"}>`; }
  function openProfile(id) { const m=state.models.find(x=>x.id===id);if(!m)return;const rank=state.models.slice().sort((a,b)=>(b.viv??-1)-(a.viv??-1)).findIndex(x=>x.id===id)+1;$("#dialogContent").innerHTML=`<span class="eyebrow">MODEL PROFILE / ${esc(m.providerLabel)}</span><h2 id="dialogTitle">${esc(m.name)}</h2><p class="dialog-subtitle">${m.coverage} of 5 VivIndex tracks scored · #${rank} on the overall index</p><div class="dialog-score-row"><div><strong>${fmt(m.viv)}</strong><span>VivIndex / 100</span></div><div><strong>${money(m.cost)}</strong><span>Average measured run</span></div><div><strong>${Number.isFinite(m.speed)?fmt(m.speed):"—"}</strong><span>Output tokens / second</span></div></div><div class="dialog-tracks">${state.tracks.filter(t=>!t.retired).map(t=>`<div class="strength-row"><span>${esc(t.short)}</span><div class="strength-track"><i style="width:${m.scores[t.id]||0}%"></i></div><b>${Number.isFinite(m.scores[t.id])?fmt(m.scores[t.id],0):"—"}</b></div>`).join("")}</div><p class="dialog-note">VivIndex combines startup planning (25%), intent (20%), value density (20%), reverse-prompt vision (20%), and one-shot UI (15%). Missing scores renormalize the available weights rather than becoming zero.</p><button class="button-dark" data-dialog-compare="${esc(m.id)}">${state.compare.includes(m.id)?"View comparison":"Add to comparison"} <span>↗</span></button>`;$("#modelDialog").showModal(); }
  function updateURL(){const q=new URLSearchParams();if(state.intent!=="overall")q.set("for",state.intent);if(state.search)q.set("q",state.search);if(state.provider!=="all")q.set("provider",state.provider);if(state.compare.length)q.set("compare",state.compare.join(","));if(state.view!=="models")q.set("view",state.view);const url=`${location.pathname}${q.toString()?"?"+q:""}${location.hash}`;history.replaceState(null,"",url);}
  let toastTimer;function toast(text){$("#toast").textContent=text;$("#toast").classList.add("visible");clearTimeout(toastTimer);toastTimer=setTimeout(()=>$("#toast").classList.remove("visible"),2800);}
  function clearFilters(){state.search="";state.provider="all";state.sort="rank";state.limit=12;$("#modelSearch").value="";$("#providerFilter").value="all";$("#modelSort").value="rank";renderRanking();updateURL();}
  function bindEvents(){
    $$(".view-tab").forEach(b=>{b.addEventListener("click",()=>setView(b.dataset.view));b.addEventListener("keydown",e=>{if(!["ArrowLeft","ArrowRight","Home","End"].includes(e.key))return;e.preventDefault();const tabs=$$(".view-tab"),i=tabs.indexOf(b);const next=e.key==="Home"?0:e.key==="End"?tabs.length-1:(i+(e.key==="ArrowRight"?1:-1)+tabs.length)%tabs.length;setView(tabs[next].dataset.view);tabs[next].focus();});});
    $$(".intent").forEach(b=>b.addEventListener("click",()=>{state.intent=b.dataset.intent;state.limit=12;state.sort="rank";$("#modelSort").value="rank";$$(".intent").forEach(x=>{x.classList.toggle("active",x===b);x.setAttribute("aria-pressed",x===b)});renderRanking();updateURL();}));
    $("#modelSearch").addEventListener("input",e=>{state.search=e.target.value.trim();state.limit=12;renderRanking();updateURL();});
    $("#providerFilter").addEventListener("change",e=>{state.provider=e.target.value;state.limit=12;renderRanking();updateURL();});
    $("#modelSort").addEventListener("change",e=>{state.sort=e.target.value;renderRanking();});
    $("#showMore").addEventListener("click",()=>{state.limit=Infinity;renderRanking();});
    ["#clearFilters","#emptyClear"].forEach(s=>$(s).addEventListener("click",clearFilters));
    $("#filterToggle").addEventListener("click",()=>{state.filterOpen=!state.filterOpen;$("#filterRow").classList.toggle("open",state.filterOpen);$("#filterToggle").setAttribute("aria-expanded",state.filterOpen);});
    $("#rankingRows").addEventListener("click",e=>{const row=e.target.closest("[data-model]");if(!row)return;if(e.target.closest('[data-action="compare"]')){toggleCompare(row.dataset.model);return;}state.active=state.active===row.dataset.model?null:row.dataset.model;renderRanking();});
    $("#insightContent").addEventListener("click",e=>{const compare=e.target.closest("[data-insight-compare]"),profile=e.target.closest("[data-insight-profile]");if(compare)toggleCompare(compare.dataset.insightCompare);if(profile)openProfile(profile.dataset.insightProfile);});
    $("#closeInsight").addEventListener("click",()=>{state.active=null;renderRanking();$("#insightContent").innerHTML="";});
    $("#compareView").addEventListener("change",e=>{if(e.target.dataset.compareSelect!==undefined){state.compare[Number(e.target.dataset.compareSelect)]=e.target.value;renderCompare();renderRanking();updateURL();}});
    $("#compareView").addEventListener("click",e=>{if(e.target.closest("[data-back]"))setView("models");if(e.target.closest("[data-clear-compare]")){state.compare=[];renderCompare();renderRanking();updateURL();}});
    $("#tracksView").addEventListener("click",e=>{const card=e.target.closest("[data-track]");if(card){state.track=card.dataset.track;renderTrackView();}});
    $("#openTracks").addEventListener("click",()=>{setView("tracks");$("#explorer").scrollIntoView({behavior:"smooth"});});
    $("#closeDialog").addEventListener("click",()=>$("#modelDialog").close());
    $("#modelDialog").addEventListener("click",e=>{if(e.target===$("#modelDialog"))$("#modelDialog").close();const c=e.target.closest("[data-dialog-compare]");if(c){if(!state.compare.includes(c.dataset.dialogCompare))toggleCompare(c.dataset.dialogCompare);$("#modelDialog").close();setView("compare");}});
    $("#shareButton").addEventListener("click",async()=>{try{await navigator.clipboard.writeText(location.href);toast("Explorer link copied to your clipboard.");}catch{toast("Copy the URL from your browser to share this view.");}});
    document.addEventListener("keydown",e=>{if(e.key==="/"&&!["INPUT","SELECT","TEXTAREA"].includes(document.activeElement.tagName)&&!$("#modelDialog").open){e.preventDefault();if(innerWidth<=640){state.filterOpen=true;$("#filterRow").classList.add("open");$("#filterToggle").setAttribute("aria-expanded","true");}$("#modelSearch").focus();}});
  }
  async function init(){
    $("#rankingRows").innerHTML=Array.from({length:7},()=>'<div class="skeleton"></div>').join("");
    try{const response=await fetch("data/results-lite.json",{cache:"no-store"});if(!response.ok)throw new Error(`HTTP ${response.status}`);const raw=await response.json();if(!raw.models?.length||!raw.results?.length)throw new Error("No benchmark results");state.tracks=raw.benchmarks.filter(t=>t.kind!=="retired").map(t=>({id:norm(t.id),name:t.name,short:t.short||t.name,kind:t.kind,coverage:t.coverage,description:t.description,weight:t.weight||0,inVivIndex:!!t.in_vivindex,scoredRuns:t.scoredRuns}));state.models=aggregateModels(raw);const params=new URLSearchParams(location.search);if(intents[params.get("for")])state.intent=params.get("for");state.search=params.get("q")||"";state.provider=params.get("provider")||"all";state.compare=(params.get("compare")||"").split(",").filter(id=>state.models.some(m=>m.id===id)).slice(0,3);state.active=state.models.slice().sort((a,b)=>(b.viv??-1)-(a.viv??-1))[0]?.id;const selectedView=params.get("view");if(["compare","tracks"].includes(selectedView))state.view=selectedView;
      $("#modelSearch").value=state.search;[...new Set(state.models.map(m=>m.provider))].sort((a,b)=>(providers[a]?.[0]||a).localeCompare(providers[b]?.[0]||b)).forEach(p=>{const opt=document.createElement("option");opt.value=p;opt.textContent=providers[p]?.[0]||p;$("#providerFilter").appendChild(opt);});$("#providerFilter").value=state.provider;
      $$(".intent").forEach(b=>{const active=b.dataset.intent===state.intent;b.classList.toggle("active",active);b.setAttribute("aria-pressed",active)});
      $("#heroModelCount").textContent=raw.totals.models;$("#heroRunCount").textContent=raw.totals.scoredRuns;$("#heroTrackCount").textContent=raw.totals.activeTracks;$("#updatedAt").textContent=`Evaluation data · ${new Date(raw.generated_at).toLocaleDateString("en-US",{month:"short",day:"numeric",year:"numeric"})}`;$("#dataStatus").classList.add("loaded");$("#dataStatus").innerHTML="<i></i> Live data";const top=state.models.slice().sort((a,b)=>(b.viv??-1)-(a.viv??-1))[0];$("#whyTopScore").textContent=fmt(top.viv);$("#whyTopModel").textContent=top.name;$("#trackCards").innerHTML=state.tracks.map((t,i)=>trackCard(t,i)).join("");bindEvents();renderRanking();setView(state.view);
    }catch(error){console.error("BenchmarkViv data failed to load",error);$("#dataStatus").classList.add("error");$("#dataStatus").innerHTML="<i></i> Data unavailable";$("#rankingRows").innerHTML=`<div class="empty-state"><h3>We couldn't load the results.</h3><p>Please refresh to try again.</p></div>`;}
  }
  init();
})();