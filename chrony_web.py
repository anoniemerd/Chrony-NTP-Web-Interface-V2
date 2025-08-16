from flask import Flask, jsonify, render_template_string
import subprocess
from datetime import datetime
import socket

app = Flask(__name__)

# -----------------------------
# Helper functions: parsing & sorting
# -----------------------------
def _is_ipv4(addr: str) -> bool:
    """Check if a string is a valid IPv4 address."""
    try:
        socket.inet_pton(socket.AF_INET, addr)
        return True
    except OSError:
        return False

def _is_ipv6(addr: str) -> bool:
    """Check if a string is a valid IPv6 address."""
    try:
        socket.inet_pton(socket.AF_INET6, addr)
        return True
    except OSError:
        return False

def _parse_client_line(line: str):
    """Parse one line of `chronyc clients` output into a dict."""
    parts = line.split()
    if not parts:
        return None
    addr = parts[0]
    f = parts[1:]
    def g(i): return f[i] if i < len(f) else ""
    return {
        "addr": addr,
        "NTP": g(0),
        "Drop": g(1),
        "Int": g(2),
        "IntL": g(3),
        "Last": g(4),
        "Cmd": g(5)
    }

# -----------------------------------------
# Core: run chronyc and return parsed clients
# -----------------------------------------
def get_chrony_clients():
    """Call `chronyc clients`, parse the output and return clients sorted
    (hostnames alphabetically, IPv4 numerically, IPv6 lexicographically)."""
    try:
        output = subprocess.check_output(["sudo", "chronyc", "clients"], universal_newlines=True)
    except Exception as e:
        return [], 0, f"Error: {e}"

    lines = output.strip().split("\n")
    if len(lines) < 3:
        return [], 0, ""

    body = [ln.rstrip() for ln in lines[2:] if ln.strip() != ""]

    hostnames, ipv4s, ipv6s = [], [], []
    for ln in body:
        addr = (ln.split() or [""])[0]
        if _is_ipv4(addr):
            ipv4s.append(ln)
        elif _is_ipv6(addr):
            ipv6s.append(ln)
        else:
            hostnames.append(ln)

    # Sorting rules
    hostnames.sort(key=lambda x: x.split()[0].lower())
    ipv4s.sort(key=lambda x: tuple(map(int, (x.split()[0]).split("."))))
    ipv6s.sort(key=lambda x: x.split()[0])

    sorted_lines = hostnames + ipv4s + ipv6s

    parsed = []
    for ln in sorted_lines:
        row = _parse_client_line(ln)
        if row:
            parsed.append(row)

    return parsed, len(parsed), ""

def get_local_time():
    """Return the current server time (local)."""
    return datetime.now().strftime("%d-%m-%Y, %H:%M:%S")

# -----------------------------
# JSON API for frontend
# -----------------------------
@app.route("/data")
def data():
    """Return live chrony clients as JSON for the frontend."""
    parsed, count, err = get_chrony_clients()
    payload = {
        "clients_parsed": parsed,
        "count": count,
        "local_time": get_local_time(),
    }
    if err:
        payload["error"] = err
    return jsonify(payload)

# -----------------------------
# Web UI Dashboard
# -----------------------------
@app.route("/")
def dashboard():
    """Render the dashboard HTML (Bootstrap + jQuery frontend)."""
    html = """
    <!DOCTYPE html>
    <html lang="en" data-bs-theme="light">
    <head>
        <meta charset="UTF-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1"/>
        <title>Chrony NTP Clients Dashboard</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css"/>
        <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
        <style>
            :root{
                --ok:#198754;
                --warn:#ffc107;
                --bad:#dc3545;

                --bg-light:#e7ebef;
                --card-light:#f5f6f8;
                --card-dark:#2a2f36;
            }
            body { font-family: Arial, sans-serif; background: var(--bg-light); }
            html[data-bs-theme="dark"] body { background: #1f2328; }

            /* -------- Switches (horizontal row, top right) -------- */
            .switch-group {
                position: fixed;
                right: 12px;
                top: 12px;
                z-index: 1000;
                display: flex;
                flex-direction: row;
                align-items: center;
                justify-content: flex-end;
                gap: 12px;
                flex-wrap: nowrap;
            }
            .switch {
                display: flex;
                align-items: center;
                gap: 6px;
                user-select: none;
                white-space: nowrap;
            }
            .switch input { display: none; }
            .slider {
                position: relative; width: 50px; height: 24px;
                background: #ccc; border-radius: 24px; cursor: pointer; transition: .25s;
            }
            .slider::before{
                content: ""; position: absolute; height: 20px; width: 20px;
                left: 2px; bottom: 2px; background: #fff; border-radius: 50%; transition: .25s;
            }
            .switch input:checked + .slider { background:#666; }
            .switch input:checked + .slider::before { transform: translateX(26px); }
            .icon { font-size: 16px; opacity: .55; transition: .2s; }
            .switch.theme .icon.sun { opacity: 1; }
            .switch.theme input:checked ~ .icon.sun { opacity: .35; }
            .switch.theme input:checked ~ .icon.moon { opacity: 1; }
            .switch.expand .icon.box-open { opacity: 1; }
            .switch.expand input:checked ~ .icon.box-open { opacity: .35; }
            .switch.expand input:checked ~ .icon.box-checked { opacity: 1; }

            /* Header */
            .page-header { text-align:center; margin-top: 20px; font-weight:700; }
            .subinfo { text-align:center; margin-bottom: 8px; line-height: 1.6rem; }
            .subinfo .datetime { font-size: 1.2rem; font-weight: 500; }
            .badge-clients { font-size: 1rem; }

            /* Spacers */
            .spacer-1line { height: 18px; }

            /* Summary pills */
            .summary-bar { display:flex; gap:10px; justify-content:center; align-items:center; flex-wrap:wrap; }
            .summary-pill { display:inline-flex; align-items:center; gap:6px; border-radius:20px; padding:4px 10px; font-weight:600; color:#fff; }
            .pill-ok   { background: var(--ok); }
            .pill-warn { background: var(--warn); color:#212529; }
            .pill-bad  { background: var(--bad); }

            /* Controls */
            .controls { display:flex; gap:8px; justify-content:center; align-items:center; flex-wrap:wrap; }            .controls .form-select { width: 260px; }
            .controls .form-control { width: 320px; }

            /* ---------- Masonry with CSS Grid + row spanning ---------- */
            .grid{
                display:grid;
                grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
                gap:16px;
                padding:0 16px 24px;
                grid-auto-rows: 8px;     /* tiny rows; JS sets span */
                grid-auto-flow: dense;
            }
            .client-card{
                border-radius:12px;
                overflow:hidden;
                border:1px solid #e5e7eb;
                background: var(--card-light);
                grid-row-end: span var(--rows, 1); /* updated by JS */
            }
            html[data-bs-theme="dark"] .client-card { border:1px solid #3a3f44; background: var(--card-dark); }

            /* Card header (status color) */
            .card-head { display:flex; align-items:center; justify-content:space-between; padding:10px 12px; cursor:pointer; color:#fff; }
            .head-ok   { background: var(--ok); }
            .head-warn { background: var(--warn); color:#212529; }
            .head-bad  { background: var(--bad); }

            .head-left { display:flex; align-items:center; gap:10px; min-width:0; }
            .addr { font-weight:700; font-size:1.06rem; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
            .icon-addr { font-size:1.05rem; }

            /* Card body */
            .card-body { padding:10px 12px; display:none; }
            .detail-row { display:flex; flex-direction:column; gap:6px; }
            .kv { display:flex; align-items:center; gap:8px; padding:6px 8px; border-radius:8px; background: rgba(0,0,0,0.04); }
            html[data-bs-theme="dark"] .kv { background: rgba(255,255,255,0.06); }
            .k { min-width:200px; font-weight:600; }
        </style>
    </head>
    <body>
        <!-- Switches in a horizontal row: expand left, theme right -->
        <div class="switch-group">
            <label class="switch expand" title="Expand/Collapse All">
                <span class="icon box-open">☐</span>
                <input type="checkbox" id="expand-toggle">
                <span class="slider"></span>
                <span class="icon box-checked">☑</span>
            </label>
            <label class="switch theme" title="Light/Dark Theme">
                <span class="icon sun">☀</span>
                <input type="checkbox" id="theme-toggle">
                <span class="slider"></span>
                <span class="icon moon">☾</span>
            </label>
        </div>

        <h1 class="page-header">Chrony NTP Clients</h1>
        <div class="subinfo">
            <div class="datetime">Date: <span id="date-part">--</span></div>
            <div class="datetime">Time: <span id="time-part">--</span></div>

            <div class="spacer-1line"></div>

            <div><span class="badge bg-primary badge-clients">Clients: <span id="clients-count">0</span></span></div>
        </div>

        <!-- extra spacing -->
        <div class="spacer-1line"></div>

        <div class="summary-bar">
            <span class="summary-pill pill-ok">🟢 OK: <span id="count-ok">0</span></span>
            <span class="summary-pill pill-warn">🟡 Warning: <span id="count-warn">0</span></span>
            <span class="summary-pill pill-bad">🔴 Critical: <span id="count-bad">0</span></span>
        </div>

        <div class="spacer-1line"></div>

        <!-- Controls: sorting and search -->
        <div class="controls">
            <select id="sort-select" class="form-select" title="Sort clients">
                <option value="ip_order">Sort by: IP Address (IPv4 numeric, then others)</option>
                <option value="drop_desc">Sort by: Drop Count (high → low)</option>
                <option value="last_recent">Sort by: Last Seen (recent → old)</option>
            </select>
            <input id="search" type="text" class="form-control" placeholder="Search clients..."/>
        </div>

        <div class="spacer-1line"></div>

        <!-- Masonry grid for client cards -->
        <div class="grid" id="grid"></div>

        <script>
            /* ---------------- THEME PERSISTENCE ---------------- */
            function applyTheme(theme){
                $("html").attr("data-bs-theme", theme);
                $("#theme-toggle").prop("checked", theme === "dark");
            }
            const savedTheme = localStorage.getItem("chrony_theme") || "light";
            applyTheme(savedTheme);
            $("#theme-toggle").on("change", function(){
                const theme = this.checked ? "dark" : "light";
                localStorage.setItem("chrony_theme", theme);
                applyTheme(theme);
            });

            /* ---------------- UTILITIES ---------------- */
            function toInt(v){ const n=parseInt(v,10); return isNaN(n)?0:n; }
            function lastToSeconds(raw){
                if(!raw) return null;
                const s = String(raw).trim().toLowerCase();
                if (s === "-" || s === "?" || s === "") return null;
                if (/^\\d+$/.test(s)) return parseInt(s,10);
                const m = s.match(/^(\\d+(?:\\.\\d+)?)\\s*([a-z]+)$/i);
                if (!m) return null;
                const num = parseFloat(m[1]); const unit = m[2];
                if (["s","sec","secs","second","seconds"].includes(unit)) return num;
                if (["m","min","mins","minute","minutes"].includes(unit)) return num*60;
                if (["h","hr","hrs","hour","hours"].includes(unit)) return num*3600;
                if (["d","day","days"].includes(unit)) return num*86400;
                return null;
            }
            function humanLast(raw){
                const sec = lastToSeconds(raw);
                if (sec === null) return raw || "-";
                if (sec < 60)  return `${Math.floor(sec)} sec ago`;
                const m = Math.floor(sec/60);
                if (m < 60)   return `${m} min ago`;
                const h = Math.floor(m/60);
                if (h < 24)   return `${h} hr ago`;
                return `${Math.floor(h/24)} d ago`;
            }
            function severity(row){
                const d=toInt(row.Drop);
                if (d>=10) return 2;
                if (d>0)   return 1;
                return 0;
            }
            function headClass(sev){ return sev===2?"head-bad":(sev===1?"head-warn":"head-ok"); }
            function iconForAddr(addr){
                if (/^\\d+\\.\\d+\\.\\d+\\.\\d+$/.test(addr)) return "🌐";
                if (/^[0-9a-fA-F:]+$/.test(addr)) return "🔗";
                return "💻";
            }

            /* ---------------- MASONRY (row spanning via ResizeObserver) ---------------- */
            const AUTO_ROW = 8;
            const GAP = 16;

            function sizeCard(el){
                el.style.setProperty("--rows", 1);
                const h = el.scrollHeight;
                const rows = Math.ceil((h + GAP) / (AUTO_ROW + GAP));
                el.style.setProperty("--rows", rows);
            }
            function sizeAllCards(){
                document.querySelectorAll(".client-card").forEach(sizeCard);
            }
            let cardObserver = null;
            function attachResizeObservers(){
                if (cardObserver) cardObserver.disconnect();
                cardObserver = new ResizeObserver(entries => {
                    for (const entry of entries) sizeCard(entry.target);
                });
                document.querySelectorAll(".client-card").forEach(el => cardObserver.observe(el));
            }
            window.addEventListener("resize", () => {
                clearTimeout(window._rsz);
                window._rsz = setTimeout(sizeAllCards, 100);
            });

            /* ---------------- STATE ---------------- */
            function loadOpenSet(){
                try { return new Set(JSON.parse(localStorage.getItem("chrony_open_cards")||"[]")); }
                catch(e){ return new Set(); }
            }
            function saveOpenSet(s){
                try { localStorage.setItem("chrony_open_cards", JSON.stringify([...s])); } catch(e){}
            }
            let openSet = loadOpenSet();

            /* ---------------- SORTING & FILTERING ---------------- */
            function ipTuple(addr){
                if (!/^\\d+\\.\\d+\\.\\d+\\.\\d+$/.test(addr)) return null;
                return addr.split(".").map(n=>parseInt(n,10));
            }
            function sortRows(rows, mode){
                if (mode==="ip_order"){
                    rows.sort((a,b)=>{
                        const A=ipTuple(a.addr||""); const B=ipTuple(b.addr||"");
                        if (A && B){ for(let i=0;i<4;i++){ if(A[i]!=B[i]) return A[i]-B[i]; } return 0; }
                        if (A && !B) return -1;
                        if (!A && B) return 1;
                        return (a.addr||"").toLowerCase().localeCompare((b.addr||"").toLowerCase());
                    });
                } else if (mode==="drop_desc"){
                    rows.sort((a,b)=> (toInt(b.Drop)-toInt(a.Drop)));
                } else if (mode==="last_recent"){
                    rows.sort((a,b)=>{
                        const as=lastToSeconds(a.Last), bs=lastToSeconds(b.Last);
                        if (as===null && bs===null) return 0;
                        if (as===null) return 1;
                        if (bs===null) return -1;
                        return as - bs;
                    });
                }
                return rows;
            }

            /* ---------------- SUMMARY ---------------- */
            function updateSummary(rows){
                let ok=0, warn=0, bad=0;
                rows.forEach(r=>{ const s=severity(r); if(s===0) ok++; else if (s===1) warn++; else bad++; });
                $("#count-ok").text(ok); $("#count-warn").text(warn); $("#count-bad").text(bad);
            }

            /* ---------------- RENDER ---------------- */
            function cardHTML(r){
                const sev = severity(r);
                const addr = r.addr || "";
                const isOpen = openSet.has(addr);
                return `
                <div class="client-card" data-addr="${addr}">
                    <div class="card-head ${headClass(sev)}">
                        <div class="head-left">
                            <span class="icon-addr">${iconForAddr(addr)}</span>
                            <div class="addr" title="${addr}">${addr}</div>
                        </div>
                        <div class="caret">${isOpen ? "▲" : "▼"}</div>
                    </div>
                    <div class="card-body" style="display:${isOpen ? "block" : "none"}">
                        <div class="detail-row">
                            <div class="kv"><span class="k">🕙 NTP Packets:</span> <span>${r.NTP || "-"}</span></div>
                            <div class="kv"><span class="k">📉 Dropped Packets:</span> <span>${r.Drop || "-"}</span></div>
                            <div class="kv"><span class="k">📨 Command Packets:</span> <span>${r.Cmd || "-"}</span></div>
                            <div class="kv"><span class="k">🔄 Interval:</span> <span>${r.Int || "-"}</span></div>
                            <div class="kv"><span class="k">👁️ Last Seen:</span> <span>${humanLast(r.Last)}</span></div>
                        </div>
                    </div>
                </div>`;
            }

            function bindHandlers(){
                // Card toggle
                $(".card-head").off("click").on("click", function(){
                    const cardEl = $(this).closest(".client-card")[0];
                    const $card = $(cardEl);
                    const addr = $card.data("addr");
                    const $body = $card.find(".card-body");
                    const $caret = $(this).find(".caret");
                    const willOpen = !$body.is(":visible");

                    if (willOpen){
                        $body.slideDown(80).promise().then(()=>{
                            sizeCard(cardEl);
                            updateExpandToggleVisual();
                        });
                        $caret.text("▲");
                        openSet.add(addr);
                    } else {
                        $body.slideUp(80).promise().then(()=>{
                            sizeCard(cardEl);
                            updateExpandToggleVisual();
                        });
                        $caret.text("▼");
                        openSet.delete(addr);
                    }
                    saveOpenSet(openSet);
                });

                // Expand-all switch
                $("#expand-toggle").off("change").on("change", function(){
                    if (this.checked){
                        $(".client-card").each(function(){
                            const $card=$(this); const addr=$card.data("addr");
                            $card.find(".card-body").stop(true,true).show();
                            $card.find(".caret").text("▲");
                            openSet.add(addr);
                        });
                    } else {
                        $(".client-card").each(function(){
                            const $card=$(this); const addr=$card.data("addr");
                            $card.find(".card-body").stop(true,true).hide();
                            $card.find(".caret").text("▼");
                            openSet.delete(addr);
                        });
                    }
                    sizeAllCards();
                    saveOpenSet(openSet);
                });
            }

            function updateExpandToggleVisual(){
                const total = $(".client-card").length;
                const openCount = $(".client-card .card-body:visible").length;
                $("#expand-toggle").prop("checked", total>0 && openCount===total);
            }

            function render(){
                const q = $("#search").val().trim().toLowerCase();
                const mode = $("#sort-select").val();

                let rows = cache.filter(r => !q || JSON.stringify(r).toLowerCase().includes(q));
                rows = sortRows(rows, mode);
                updateSummary(rows);

                $("#grid").html(rows.map(cardHTML).join(""));
                bindHandlers();
                sizeAllCards();
                attachResizeObservers();
                updateExpandToggleVisual();
            }

            /* ---------------- REFRESH LOOP ---------------- */
            let cache = [];
            function refresh(){
                $.getJSON("/data", function(payload){
                    const [d, t] = (payload.local_time || "").split(", ");
                    $("#date-part").text(d || "--");
                    $("#time-part").text(t || "--");
                    $("#clients-count").text(payload.count || 0);

                    cache = payload.clients_parsed || [];
                    render();
                });
            }
            $(function(){
                $("#sort-select").on("change", render);
                $("#search").on("input", render);
                refresh();
                setInterval(refresh, 1000);
            });
        </script>
    </body>
    </html>
    """
    return render_template_string(html)

# -----------------------------
# Main entrypoint
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
