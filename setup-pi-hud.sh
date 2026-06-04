#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${HEADUNIT_HUD_APP_DIR:-/opt/headunit-pi-hud}"
ENV_FILE="${HEADUNIT_HUD_ENV_FILE:-/etc/headunit-pi-hud.env}"
TEST_ENV_FILE="${HEADUNIT_HUD_TEST_ENV_FILE:-/run/headunit-pi-hud-test.env}"
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

desktop_user() {
  local user="${SUDO_USER:-}"
  if [ -n "${user}" ] && [ "${user}" != "root" ]; then
    printf '%s\n' "${user}"
    return 0
  fi
  user="$(logname 2>/dev/null || true)"
  if [ -n "${user}" ] && [ "${user}" != "root" ]; then
    printf '%s\n' "${user}"
    return 0
  fi
  user="$(getent passwd 1000 | cut -d: -f1 || true)"
  if [ -n "${user}" ]; then
    printf '%s\n' "${user}"
    return 0
  fi
  id -un
}

run_desktop_hud() {
  local app user uid home
  local env_args=()
  app="$(installed_app_dir)"
  user="$(desktop_user)"
  uid="$(id -u "${user}")"
  home="$(getent passwd "${user}" | cut -d: -f6)"

  env_args+=("HEADUNIT_HUD_ENV_FILE=${ENV_FILE}")
  env_args+=("HEADUNIT_HUD_TEST_ENV_FILE=${TEST_ENV_FILE}")
  env_args+=("HOME=${home}")
  if [ -d "/run/user/${uid}" ]; then
    env_args+=("XDG_RUNTIME_DIR=/run/user/${uid}")
  fi
  if [ -S "/run/user/${uid}/wayland-0" ]; then
    env_args+=("WAYLAND_DISPLAY=wayland-0")
  fi
  if [ -S /tmp/.X11-unix/X0 ]; then
    env_args+=("DISPLAY=:0")
  fi
  if [ -r "${home}/.Xauthority" ]; then
    env_args+=("XAUTHORITY=${home}/.Xauthority")
  fi

  if [ "$(id -u)" -eq 0 ] && [ "${user}" != "root" ]; then
    sudo -u "${user}" env "${env_args[@]}" "${app}/pi-hud/scripts/run-from-env.sh"
  else
    env "${env_args[@]}" "${app}/pi-hud/scripts/run-from-env.sh"
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

clear_screen_test_env() {
  run_sudo rm -f "${TEST_ENV_FILE}"
}

detect_framebuffer_size() {
  local fb_path="${HEADUNIT_HUD_FRAMEBUFFER_SIZE_FILE:-/sys/class/graphics/fb0/virtual_size}"
  local raw normalized width height extra
  [ -r "${fb_path}" ] || return 1
  raw="$(head -n 1 "${fb_path}" 2>/dev/null || true)"
  normalized="${raw//x/,}"
  normalized="${normalized// /,}"
  IFS=',' read -r width height extra <<< "${normalized}"
  if [[ "${width}" =~ ^[0-9]+$ ]] && [[ "${height}" =~ ^[0-9]+$ ]] && [ "${width}" -gt 0 ] && [ "${height}" -gt 0 ]; then
    printf '%s %s\n' "${width}" "${height}"
    return 0
  fi
  return 1
}

write_screen_test_env() {
  local width="${1:-}"
  local height="${2:-}"
  run_sudo install -d -m 0755 "$(dirname -- "${TEST_ENV_FILE}")"
  {
    printf 'HEADUNIT_HUD_DUMMY=1\n'
    printf 'HEADUNIT_HUD_REQUIRE_HANDOFF=0\n'
    if [ -n "${width}" ] && [ -n "${height}" ]; then
      printf 'HEADUNIT_HUD_WIDTH=%s\n' "${width}"
      printf 'HEADUNIT_HUD_HEIGHT=%s\n' "${height}"
    fi
  } | run_sudo tee "${TEST_ENV_FILE}" >/dev/null
  run_sudo chmod 0644 "${TEST_ENV_FILE}"
}

install_or_update() {
  echo "[1/3] Installing/updating Headunit Pi HUD..."
  run_sudo bash "${ROOT_DIR}/pi-hud/scripts/install-pi.sh" "${APP_DIR}"
  echo "[2/3] Enabling HUD autostart..."
  clear_screen_test_env
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
  local size width height
  width=""
  height=""
  if size="$(detect_framebuffer_size)"; then
    width="${size%% *}"
    height="${size##* }"
    echo "[OK] Detected display ${width}x${height}; screen test will use it."
  else
    echo "[WARN] Could not detect display size; screen test will use configured width/height."
  fi
  write_screen_test_env "${width}" "${height}"
  run_sudo systemctl stop headunit-pi-hud.service || true
  echo "[OK] Starting direct HUD screen test; press Ctrl+C to exit."
  echo "[INFO] This does not depend on systemd desktop session access."
  run_desktop_hud
}

auto_configure_hardware() {
  local app
  local python
  app="$(installed_app_dir)"
  python="$(python_bin)"
  run_sudo "${python}" "${app}/pi-hud/scripts/auto-configure-hardware.py" --apply --force
  clear_screen_test_env
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
