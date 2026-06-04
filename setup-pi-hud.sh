#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${HEADUNIT_HUD_APP_DIR:-/opt/headunit-pi-hud}"
ENV_FILE="${HEADUNIT_HUD_ENV_FILE:-/etc/headunit-pi-hud.env}"
ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

run_sudo() {
  if [ "$(id -u)" -eq 0 ]; then
    "$@"
  else
    sudo "$@"
  fi
}

installed_app_dir() {
  if [ -d "${APP_DIR}/pi-hud" ]; then
    printf '%s\n' "${APP_DIR}"
  else
    printf '%s\n' "${ROOT_DIR}"
  fi
}

python_bin() {
  local app
  app="$(installed_app_dir)"
  if [ -x "${app}/.venv/bin/python" ]; then
    printf '%s\n' "${app}/.venv/bin/python"
  else
    printf '%s\n' "python3"
  fi
}

set_env_value() {
  local key="$1"
  local value="$2"
  run_sudo touch "${ENV_FILE}"
  if run_sudo grep -q "^${key}=" "${ENV_FILE}"; then
    run_sudo sed -i "s|^${key}=.*|${key}=${value}|" "${ENV_FILE}"
  else
    printf '%s=%s\n' "${key}" "${value}" | run_sudo tee -a "${ENV_FILE}" >/dev/null
  fi
}

install_or_update() {
  echo "[1/3] Installing/updating Headunit Pi HUD..."
  run_sudo bash "${ROOT_DIR}/pi-hud/scripts/install-pi.sh" "${APP_DIR}"
  echo "[2/3] Enabling HUD autostart..."
  run_sudo systemctl unmask headunit-pi-hud.service || true
  run_sudo systemctl enable headunit-pi-hud.service
  run_sudo systemctl restart headunit-pi-hud.service
  echo "[3/3] Enabling automatic git updates..."
  set_env_value HEADUNIT_HUD_AUTO_UPDATE 1
  run_sudo systemctl unmask headunit-pi-hud-update.service || true
  run_sudo systemctl unmask headunit-pi-hud-update.timer || true
  run_sudo systemctl enable headunit-pi-hud-update.timer
  run_sudo systemctl start headunit-pi-hud-update.timer
  echo "[OK] Install/update complete. HUD autostart and auto update are enabled."
}

screen_test() {
  set_env_value HEADUNIT_HUD_DUMMY 1
  run_sudo systemctl restart headunit-pi-hud.service
  echo "[OK] Dummy screen test mode enabled. Opening live HUD logs; press Ctrl+C to exit logs."
  run_sudo journalctl -u headunit-pi-hud.service -f
}

auto_configure_hardware() {
  local app
  local python
  app="$(installed_app_dir)"
  python="$(python_bin)"
  run_sudo "${python}" "${app}/pi-hud/scripts/auto-configure-hardware.py" --apply --force
  set_env_value HEADUNIT_HUD_DUMMY 0
  run_sudo systemctl restart headunit-pi-hud.service
  echo "[OK] Hardware auto-config finished. Run status check next."
}

restart_hud() {
  run_sudo systemctl restart headunit-pi-hud.service
  echo "[OK] HUD service restarted."
}

show_logs() {
  run_sudo journalctl -u headunit-pi-hud.service -f
}

status_check() {
  local app
  local python
  app="$(installed_app_dir)"
  python="$(python_bin)"
  run_sudo systemctl status headunit-pi-hud.service --no-pager || true
  "${python}" "${app}/pi-hud/scripts/first-run-status.py" --probe-display || true
}

run_update_now() {
  run_sudo systemctl start headunit-pi-hud-update.service
  run_sudo journalctl -u headunit-pi-hud-update.service -n 80 --no-pager
}

toggle_auto_update() {
  local current
  current="$(grep -E '^HEADUNIT_HUD_AUTO_UPDATE=' "${ENV_FILE}" 2>/dev/null | tail -n 1 | cut -d= -f2- || true)"
  if [ "${current}" = "1" ]; then
    set_env_value HEADUNIT_HUD_AUTO_UPDATE 0
    echo "[OK] Automatic updates disabled."
  else
    set_env_value HEADUNIT_HUD_AUTO_UPDATE 1
    run_sudo systemctl unmask headunit-pi-hud-update.service || true
    run_sudo systemctl unmask headunit-pi-hud-update.timer || true
    run_sudo systemctl enable headunit-pi-hud-update.timer
    run_sudo systemctl start headunit-pi-hud-update.timer
    echo "[OK] Automatic updates enabled."
  fi
}

print_menu() {
  cat <<'MENU'

Headunit Pi HUD Setup

1. Install/update and enable autostart
2. Screen test without OBD/CAN
3. Auto-detect iCar/CANable
4. Restart HUD service
5. Show live HUD logs
6. Status check
7. Run update now
8. Toggle automatic updates
0. Exit

MENU
}

run_choice() {
  case "$1" in
    1) install_or_update ;;
    2) screen_test ;;
    3) auto_configure_hardware ;;
    4) restart_hud ;;
    5) show_logs ;;
    6) status_check ;;
    7) run_update_now ;;
    8) toggle_auto_update ;;
    0) exit 0 ;;
    *) echo "Unknown option: $1" >&2; return 1 ;;
  esac
}

if [ "${1:-}" != "" ]; then
  run_choice "$1"
  exit $?
fi

while true; do
  print_menu
  read -r -p "Select: " choice
  run_choice "${choice}" || true
done
