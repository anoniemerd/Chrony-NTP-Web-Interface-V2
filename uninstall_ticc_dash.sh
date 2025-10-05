#!/usr/bin/env bash
# ==========================================
#  TICC-DASH Uninstaller
#  - Stops & disables the systemd service (ticc-dash.service)
#  - Removes the unit & symlink and reloads systemd
#  - Frees TCP port $PORT (default 5000) and kills app processes
#  - Removes sudoers rule (/etc/sudoers.d/ticc-dash)
#  - Deletes application directory (/opt/ticc-dash)
#  - Idempotent: safe to re-run if parts are already gone
# ==========================================

set -euo pipefail

APP_DIR="/opt/ticc-dash"
SERVICE_NAME="ticc-dash.service"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME"
WANTS_LINK="/etc/systemd/system/multi-user.target.wants/$SERVICE_NAME"
SUDOERS_FILE="/etc/sudoers.d/ticc-dash"
PORT="${PORT:-5000}"

log()  { printf "\n\033[1;34m%s\033[0m\n" "$*"; }
ok()   { printf "\033[1;32m%s\033[0m\n" "$*"; }
run()  { echo "  $*"; eval "$*" >/dev/null 2>&1 || true; }

trap 'echo "❌ Uninstall aborted."; exit 1' ERR

echo "=========================================="
echo "  🧹 Uninstalling TICC-DASH"
echo "=========================================="

# 1️⃣ Stop & disable the systemd service (if it exists)
if systemctl list-unit-files | grep -q "^$SERVICE_NAME"; then
  log "🛑 Stopping and disabling systemd service..."
  run "sudo systemctl stop '$SERVICE_NAME'"
  run "sudo systemctl disable '$SERVICE_NAME'"
  ok "✅ Service stopped and disabled."
fi

# 2️⃣ Remove service symlink & unit
log "🗑️  Removing service symlink & unit..."
run "sudo rm -f '$WANTS_LINK'"
run "sudo rm -f '$SERVICE_FILE'"
run "sudo systemctl reset-failed"
run "sudo systemctl daemon-reload"
ok "✅ Service removed and systemd reloaded."

# 3️⃣ Kill any process listening on the app port
log "🔌 Killing any process listening on TCP port $PORT..."
run "sudo fuser -k ${PORT}/tcp"
ok "✅ Port cleanup done."

# 4️⃣ Kill any process started from /opt/ticc-dash (TERM → KILL)
log "🪓 Killing processes started from $APP_DIR..."
run "sudo pkill -f '$APP_DIR'"
sleep 0.5
run "sudo pkill -9 -f '$APP_DIR'"
ok "✅ Process cleanup done."

# 5️⃣ Remove sudoers rule
log "🔐 Removing sudoers rule..."
run "sudo rm -f '$SUDOERS_FILE'"
run "sudo visudo -c"
ok "✅ Sudoers cleaned and syntax valid."

# 6️⃣ Remove application directory
log "📁 Removing application directory: $APP_DIR ..."
run "sudo rm -rf '$APP_DIR'"
ok "✅ Application directory removed."

# 7️⃣ Summary
echo
echo "=========================================="
ok "🎉 Uninstall completed."
echo "Removed/cleaned:"
echo "  • Service/unit/symlink: $SERVICE_NAME"
echo "  • App dir:              $APP_DIR"
echo "  • Sudoers rule:         $SUDOERS_FILE"
echo "  • Port ${PORT}:          freed"
echo
echo "Verify:"
echo "  • systemctl status $SERVICE_NAME"
echo "  • pgrep -a gunicorn"
echo "  • ss -lptn 'sport = :${PORT}'"
echo "  • ls -la $APP_DIR"
echo "=========================================="
