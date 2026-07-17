"use strict";
function el(id){ return document.getElementById(id); }
function esc(x){ return String(x==null||x===""?"—":x).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"); }
function showErr(msg){
  el("errbox").innerHTML = '<div class="err">' + esc(msg) + '<br><button id="retrybtn">↻ Retry</button></div>';
  el("retrybtn").addEventListener("click", loadData);
}
function toast(m){ var t = el("toast"); t.textContent = m; t.classList.add("show"); setTimeout(function(){ t.classList.remove("show"); }, 4000); }

var JOBS = [];
var STATUSES = ["To Apply","Applied","Interview Requested","Interviewing","Offer","Rejected","Expired","SKIP","N/A"];
var view = "fit", sortKey = null, sortDir = 1;
var changes = {};
var DEFAULT_SORT = { fit:["score",-1], pend:["score",-1], all:["id",-1] };
try { view = localStorage.getItem("jdash_view") || "fit"; } catch(e){}

async function loadData(){
  el("errbox").innerHTML = "";
  el("loading").style.display = "block"; el("loading").textContent = "Loading tracker database…";
  try {
    var r = await fetch("/api/jobs");
    var data = await r.json();
    if(!data.ok) throw new Error(data.error || ("HTTP " + r.status));
    JOBS = data.jobs || [];
    el("loading").style.display = "none";
    el("cards").style.display = "grid";
    el("meta").textContent = "Loaded " + JOBS.length + " jobs at " + (data.generated || "now") + " · status changes are saved straight to the database";
    updateCards(); buildStatusFilter(); render();
  } catch(e) {
    el("loading").style.display = "none";
    showErr("Could not load data: " + e.message);
  }
}

function updateCards(){
  function eff(j){ return changes[j.id] || j.status; }
  el("c_nfit").textContent    = JOBS.filter(function(j){return j.score>=4 && eff(j)==="To Apply";}).length;
  el("c_toapply").textContent = JOBS.filter(function(j){return eff(j)==="To Apply";}).length;
  el("c_applied").textContent = JOBS.filter(function(j){return eff(j)==="Applied";}).length;
  el("c_total").textContent   = JOBS.length;
}

function buildStatusFilter(){
  var fs = el("fstatus");
  while (fs.options.length > 1) fs.remove(1);
  var seen = {};
  JOBS.forEach(function(j){ if(j.status) seen[j.status]=1; });
  Object.keys(seen).sort().forEach(function(st){
    var o = document.createElement("option"); o.value = st; o.textContent = st; fs.appendChild(o); });
}

function setView(v){ view = v; sortKey = null;
  try { localStorage.setItem("jdash_view", v); } catch(e){}
  document.querySelectorAll(".tab").forEach(function(b){ b.classList.toggle("on", b.dataset.v===v); });
  el("fbar").classList.toggle("show", v==="all");
  render(); }

function currentRows(){
  var rs = JOBS.filter(function(j){
    var st = changes[j.id] || j.status;
    if(view==="fit")  return j.score>=4 && st==="To Apply";
    if(view==="pend") return st==="To Apply";
    return true; });
  if(view==="all"){
    var q = el("q").value.trim().toLowerCase();
    var fst = el("fstatus").value, fsc = el("fscore").value;
    if(q)   rs = rs.filter(function(j){ return (j.title+" "+j.co).toLowerCase().indexOf(q)>=0; });
    if(fst) rs = rs.filter(function(j){ return (changes[j.id]||j.status)===fst; });
    if(fsc) rs = rs.filter(function(j){ return j.score>=+fsc && (fsc!=="5"||j.score===5); }); }
  var dft = DEFAULT_SORT[view] || ["id",-1];
  var k = sortKey ? sortKey : dft[0], d = sortKey ? sortDir : dft[1];
  rs.sort(function(a,b){ var x=a[k], y=b[k];
    if(k==="score"||k==="id"||k==="rm"){ x=+x||0; y=+y||0; } else { x=String(x).toLowerCase(); y=String(y).toLowerCase(); }
    return (x<y?-1:x>y?1:0)*d; });
  return rs; }

var COLS = [["id","#"],["title","Role"],["sal","Salary"],["score","Fit"],["rm","Rec %"],["posted","Posted"],["status","Status"],[null,"Actions"]];
function render(){
  if(!JOBS.length){ el("tbl").innerHTML = '<div class="empty">The database returned 0 rows.</div>'; return; }
  var rs = currentRows();
  if(!rs.length){ el("tbl").innerHTML = '<div class="empty">No rows match this view.</div>'; return; }
  var showDetail = view!=="all";
  var h = "<table><thead><tr>" + COLS.map(function(c){
    var k=c[0], l=c[1];
    var dir = (sortKey===k) ? ' <span class="dir">'+(sortDir>0?"▲":"▼")+"</span>" : "";
    return k ? '<th data-sort="' + k + '">' + l + dir + "</th>" : "<th>" + l + "</th>"; }).join("") + "</tr></thead><tbody>";
  rs.forEach(function(j){
    var st = changes[j.id] || j.status;
    var opts = STATUSES.map(function(s){ return '<option ' + (s===st?"selected":"") + '>' + s + '</option>'; }).join("");
    var det = showDetail && (j.gaps||j.anchor) ? '<div class="detail">Gaps: ' + esc(j.gaps) + '<br>Anchor: ' + esc(j.anchor) + '</div>' : "";
    var acts = j.url ? '<button class="atsbtn" data-kit="' + j.id + '">📄 ATS resume</button><a class="applybtn" href="' + esc(j.url) + '" target="_blank" rel="noopener">↗ Apply</a>' : "—";
    h += '<tr><td class="id">#' + j.id + '</td>' +
      '<td><b>' + esc(j.title) + '</b><br><span class="sub">' + esc(j.co) + ' · ' + esc(j.loc) + '</span>' + det + '</td>' +
      '<td>' + esc(j.sal) + '</td><td><span class="chip s' + j.score + '">' + (j.score||"—") + '</span></td>' +
      '<td>' + (j.rm!=null ? j.rm + '%' : '—') + '</td>' +
      '<td>' + esc(j.posted) + '</td>' +
      '<td><select class="stsel ' + (changes[j.id]?"dirty":"") + '" data-id="' + j.id + '">' + opts + '</select></td>' +
      '<td class="actions">' + acts + '</td></tr>'; });
  el("tbl").innerHTML = h + "</tbody></table>"; }

function stageChange(id, val){
  var j = JOBS.find(function(x){ return x.id===id; });
  if(!j) return;
  if(j.status===val) delete changes[id]; else changes[id] = val;
  updateBar(); updateCards(); render(); }
function updateBar(){
  var n = Object.keys(changes).length;
  el("pendbar").classList.toggle("show", n>0);
  el("pendtxt").textContent = n + " status change" + (n>1?"s":"") + " queued"; }
function clearChanges(){ changes = {}; updateBar(); updateCards(); render(); }

async function applyChanges(){
  var updates = Object.keys(changes).map(function(id){ return { id: +id, status: changes[id] }; });
  if(!updates.length) return;
  var btn = el("savebtn");
  btn.disabled = true; btn.textContent = "Saving…";
  try {
    var r = await fetch("/api/updates", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ updates: updates })
    });
    var data = await r.json();
    if(!data.ok) throw new Error(data.error || ("HTTP " + r.status));
    clearChanges();
    toast("✅ " + data.applied + " change" + (data.applied>1?"s":"") + " saved to the database");
    await loadData();
  } catch(e) {
    toast("❌ Save failed");
    showErr("Save failed — nothing was lost, your changes are still queued in the bottom bar.\n" + e.message);
  } finally {
    btn.disabled = false; btn.textContent = "💾 Save to database";
    updateBar();
  }
}

async function runKit(btn, id){
  if(btn.disabled) return;
  btn.disabled = true; btn.textContent = "⏳ Starting…";
  try {
    var r = await fetch("/api/ats-kit", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ id: id })
    });
    var data = await r.json();
    if(!data.ok) throw new Error(data.error || ("HTTP " + r.status));
    btn.textContent = "⏳ Running…"; btn.classList.add("ok");
    toast("ATS kit run started for Job #" + id);
    pollKit(btn, id);
  } catch(e) {
    btn.disabled = false; btn.textContent = "📄 ATS resume"; btn.classList.remove("ok");
    toast("❌ " + e.message);
  }
}

function pollKit(btn, id){
  var iv = setInterval(async function(){
    try {
      var r = await fetch("/api/ats-kit/status?id=" + id);
      var d = await r.json();
      if(d.state === "done"){
        clearInterval(iv);
        btn.disabled = false; btn.classList.remove("ok");
        if(d.returncode === 0){ btn.textContent = "✓ Kit ready"; toast("✅ ATS kit ready for Job #" + id); }
        else { btn.textContent = "⚠ Failed"; toast("⚠ Kit run exited " + d.returncode + " — see " + d.log); }
        setTimeout(function(){ btn.textContent = "📄 ATS resume"; }, 5000);
      }
    } catch(e){ /* transient; keep polling */ }
  }, 4000);
}

el("tabs").addEventListener("click", function(ev){
  var b = ev.target.closest(".tab"); if(b) setView(b.dataset.v); });
el("refreshbtn").addEventListener("click", loadData);
el("q").addEventListener("input", render);
el("fstatus").addEventListener("change", render);
el("fscore").addEventListener("change", render);
el("savebtn").addEventListener("click", applyChanges);
el("clearbtn").addEventListener("click", clearChanges);
el("tbl").addEventListener("click", function(ev){
  var th = ev.target.closest("th[data-sort]");
  if(th){ var k = th.dataset.sort; if(sortKey===k) sortDir=-sortDir; else { sortKey=k; sortDir=1; } render(); return; }
  var kb = ev.target.closest("button[data-kit]");
  if(kb){ runKit(kb, +kb.dataset.kit); } });
el("tbl").addEventListener("change", function(ev){
  var s = ev.target.closest("select.stsel");
  if(s){ stageChange(+s.dataset.id, s.value); } });

document.querySelectorAll(".tab").forEach(function(b){ b.classList.toggle("on", b.dataset.v===view); });
el("fbar").classList.toggle("show", view==="all");
loadData();
