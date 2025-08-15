from flask import Flask, jsonify, render_template_string
import subprocess
from datetime import datetime
import socket

app = Flask(__name__)

# -----------------------------
# Helpers: parsing & sorting
# -----------------------------
def _is_ipv4(addr: str) -> bool:
    try:
        socket.inet_pton(socket.AF_INET, addr)
        return True
    except OSError:
        return False

def _is_ipv6(addr: str) -> bool:
    try:
        socket.inet_pton(socket.AF_INET6, addr)
        return True
    except OSError:
        return False

def _parse_client_line(line: str):
    """
    Parse a client line from `chronyc clients`.
    Columns (best-effort) based on chronyc:
    Hostname/IP, NTP, Drop, Int, IntL, Last, Cmd
    """
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
# Core: get chrony clients (sorted)
# -----------------------------------------
def get_chrony_clients():
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

    # Sort: hostnames A-Z, IPv4 numeric, IPv6 alphabetic
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
    return datetime.now().strftime("%d-%m-%Y, %H:%M:%S")

# -----------------------------
# Data API
# -----------------------------
@app.route("/data")
def data():
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
# UI: Dashboard with click-to-expand + "expand all" switch
# -----------------------------
@app.route("/")
def dashboard():
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
                --ok:#28a745;   
                --warn:#ffc107; 
                --bad:#dc3545;  
            }
            body { font-family: Arial, sans-serif; }

            .switch-group { position: fixed; right: 12px; top: 12px; z-index: 1000; display:flex; gap:10px; }
            .switch { position: relative; display: inline-block; width: 50px; height: 24px; }
            .switch input { display: none; }
            .slider {
                position: absolute; inset: 0; background:#ccc; border-radius:24px; cursor:pointer; transition:.25s;
            }
            .switch.theme .slider:before {
                content:"🌞"; position:absolute; height:20px; width:20px; left:2px; bottom:2px;
                background:#fff; border-radius:50%; text-align:center; line-height:20px; font-size:12px; transition:.25s;
            }
            .switch.theme input:checked + .slider { background:#666; }
            .switch.theme input:checked + .slider:before { transform: translateX(26px); content:"🌙"; }

            .switch.expand .slider:before {
                content:"📁"; position:absolute; height:20px; width:20px; left:2px; bottom:2px;
                background:#fff; border-radius:50%; text-align:center; line-height:20px; font-size:12px; transition:.25s;
            }
            .switch.expand input:checked + .slider { background:#0d6efd; }
            .switch.expand input:checked + .slider:before { transform: translateX(26px); content:"📂"; }

            .page-header { text-align:center; margin-top: 20px; font-weight:700; }
            .subinfo { text-align:center; margin-bottom: 16px; line-height: 1.6rem; }
            .badge-clients { font-size: 1rem; }

            .grid { display:grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap:16px; padding:0 16px 24px; }

            .client-card { border-radius:12px; overflow:hidden; border:1px solid #e5e7eb; }
            html[data-bs-theme="dark"] .client-card { border:1px solid #3a3f44; }

            .card-head { display:flex; align-items:center; justify-content:space-between; padding:10px 12px; cursor:pointer; }
            .card-head:hover { filter: brightness(0.95); }
            .head-left { display:flex; align-items:center; gap:10px; min-width:0; }
            .addr { font-weight:700; font-size:1.05rem; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
            .icon { font-size:1.1rem; }
            .hostname { color:#0d6efd; }
            .ipv4 { color:#198754; }
            .ipv6 { color:#6f42c1; }
            .head-ok { background: rgba(40,167,69,0.20); }
            .head-warn { background: rgba(255,193,7,0.25); }
            .head-bad { background: rgba(220,53,69,0.25); }
            html[data-bs-theme="dark"] .head-ok { background: rgba(40,167,69,0.30); }
            html[data-bs-theme="dark"] .head-warn { background: rgba(255,193,7,0.35); }
            html[data-bs-theme="dark"] .head-bad { background: rgba(220,53,69,0.35); }

            .card-body { padding:10px 12px; display:none; }
            .stats-grid { display:grid; grid-template-columns:1fr 1fr; gap:8px; }
            @media (max-width: 500px) { .stats-grid { grid-template-columns:1fr; } }
            .kv { background: rgba(0,0,0,0.03); padding:6px; border-radius:6px; }
            html[data-bs-theme="dark"] .kv { background: rgba(255,255,255,0.05); }
            .kv .k { font-size:0.85rem; color:#6c757d; }
            html[data-bs-theme="dark"] .kv .k { color:#adb5bd; }
            .kv .v { font-weight:600; font-size:0.95rem; }
        </style>
    </head>
    <body>
        <div class="switch-group">
            <label class="switch expand" title="Expand/Collapse All">
                <input type="checkbox" id="expand-toggle">
                <span class="slider"></span>
            </label>
            <label class="switch theme" title="Light/Dark Theme">
                <input type="checkbox" id="theme-toggle">
                <span class="slider"></span>
            </label>
        </div>

        <h1 class="page-header">Chrony NTP Clients</h1>
        <div class="subinfo">
            <div>Date: <span id="date-part">--</span></div>
            <div>Time: <span id="time-part">--</span></div>
            <div class="mt-1"><span class="badge bg-primary badge-clients">Clients: <span id="clients-count">0</span></span></div>
        </div>

        <div class="grid" id="grid"></div>

        <script>
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

            function classifyAddr(addr){
                if (/^\\d+\\.\\d+\\.\\d+\\.\\d+$/.test(addr)) return "ipv4";
                if (/^[0-9a-fA-F:]+$/.test(addr)) return "ipv6";
                return "hostname";
            }
            function toIntSafe(v){
                const x = parseInt(v, 10);
                return isNaN(x) ? 0 : x;
            }
            function severity(row){
                const drop = toIntSafe(row.Drop);
                if (drop >= 10) return 2;
                if (drop > 0)   return 1;
                return 0;
            }
            function headClass(sev){ return sev === 2 ? "head-bad" : (sev === 1 ? "head-warn" : "head-ok"); }
            function iconForType(t){ return t === "hostname" ? "💻" : (t === "ipv4" ? "🌐" : "🔗"); }

            function loadOpenSet(){
                try { return new Set(JSON.parse(localStorage.getItem("chrony_open_cards") || "[]")); }
                catch(e){ return new Set(); }
            }
            function saveOpenSet(s){
                try { localStorage.setItem("chrony_open_cards", JSON.stringify(Array.from(s))); } catch(e){}
            }
            let openSet = loadOpenSet();

            let lastSnapshot = "";
            let cache = [];

            function cardHTML(r){
                const type = classifyAddr(r.addr || "");
                const sev = severity(r);
                const isOpen = openSet.has(r.addr || "");
                return `
                <div class="client-card" data-addr="${r.addr || ""}">
                    <div class="card-head ${headClass(sev)}">
                        <div class="head-left">
                            <span class="icon">${iconForType(type)}</span>
                            <div class="addr ${type}" title="${r.addr || ""}">${r.addr || ""}</div>
                        </div>
                        <div class="caret">${isOpen ? "▲" : "▼"}</div>
                    </div>
                    <div class="card-body" style="display:${isOpen ? "block" : "none"}">
                        <div class="stats-grid">
                            <div class="kv"><div class="k">⏱ NTP Packets</div><div class="v">${r.NTP || "-"}</div></div>
                            <div class="kv"><div class="k">📉 Dropped Packets</div><div class="v">${r.Drop || "-"}</div></div>
                            <div class="kv"><div class="k">🔄 Interval</div><div class="v">${r.Int || "-"}</div></div>
                            <div class="kv"><div class="k">🔄 Interval (Long)</div><div class="v">${r.IntL || "-"}</div></div>
                            <div class="kv"><div class="k">👁 Last Seen</div><div class="v">${r.Last || "-"}</div></div>
                            <div class="kv"><div class="k">🛠 Commands Sent</div><div class="v">${r.Cmd || "-"}</div></div>
                        </div>
                    </div>
                </div>`;
            }

            function bindCardHandlers(){
                $(".card-head").off("click").on("click", function(){
                    const card = $(this).closest(".client-card");
                    const addr = card.data("addr");
                    const body = card.find(".card-body").first();
                    const caret = $(this).find(".caret");
                    if (body.is(":visible")){
                        body.slideUp(150);
                        caret.text("▼");
                        openSet.delete(addr);
                    } else {
                        body.slideDown(150);
                        caret.text("▲");
                        openSet.add(addr);
                    }
                    saveOpenSet(openSet);
                    updateExpandToggleVisual();
                });
            }

            function render(){
                const grid = $("#grid");
                grid.html(cache.map(cardHTML).join(""));
                bindCardHandlers();
                updateExpandToggleVisual();
            }

            function openAll(){
                $(".client-card").each(function(){
                    const card = $(this);
                    const addr = card.data("addr");
                    const body = card.find(".card-body").first();
                    const caret = card.find(".card-head .caret").first();
                    if (!body.is(":visible")){
                        body.show();
                        caret.text("▲");
                    }
                    openSet.add(addr);
                });
                saveOpenSet(openSet);
            }

            function closeAll(){
                $(".client-card").each(function(){
                    const card = $(this);
                    const addr = card.data("addr");
                    const body = card.find(".card-body").first();
                    const caret = card.find(".card-head .caret").first();
                    if (body.is(":visible")){
                        body.hide();
                        caret.text("▼");
                    }
                    openSet.delete(addr);
                });
                saveOpenSet(openSet);
            }

            function updateExpandToggleVisual(){
                const total = $(".client-card").length;
                const openCount = $(".client-card .card-body:visible").length;
                const allOpen = total > 0 && openCount === total;
                $("#expand-toggle").prop("checked", allOpen);
            }

            $("#expand-toggle").on("change", function(){
                if (this.checked){
                    openAll();
                } else {
                    closeAll();
                }
            });

            function refresh(){
                $.getJSON("/data", function(payload){
                    const [d, t] = (payload.local_time || "").split(", ");
                    $("#date-part").text(d || "--");
                    $("#time-part").text(t || "--");
                    $("#clients-count").text(payload.count || 0);

                    const snap = JSON.stringify(payload.clients_parsed || []);
                    if (snap !== lastSnapshot){
                        lastSnapshot = snap;
                        cache = payload.clients_parsed || [];
                        render();
                    } else {
                        updateExpandToggleVisual();
                    }
                });
            }

            $(document).ready(function(){
                const savedTheme = localStorage.getItem("chrony_theme") || "light";
                applyTheme(savedTheme);

                refresh();
                setInterval(refresh, 1000);
            });
        </script>
    </body>
    </html>
    """
    return render_template_string(html)

# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
