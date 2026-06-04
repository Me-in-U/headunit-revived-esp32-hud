#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd -- "${SCRIPT_DIR}/../.." && pwd)"

ENV_FILE="${HEADUNIT_HUD_ENV_FILE:-}"
if [ -z "${ENV_FILE}" ] && [ -r /etc/headunit-pi-hud.env ]; then
  ENV_FILE=/etc/headunit-pi-hud.env
fi

if [ -n "${ENV_FILE}" ]; then
  set -a
  # shellcheck disable=SC1090
  . "${ENV_FILE}"
  set +a
fi

TEST_ENV_FILE="${HEADUNIT_HUD_TEST_ENV_FILE:-/run/headunit-pi-hud-test.env}"
if [ -r "${TEST_ENV_FILE}" ]; then
  set -a
  # shellcheck disable=SC1090
  . "${TEST_ENV_FILE}"
  set +a
fi

truthy() {
  case "${1:-0}" in
    1|true|TRUE|yes|YES|on|ON) return 0 ;;
    *) return 1 ;;
  esac
}

configure_display_environment() {
  local uid runtime_dir
  uid="$(id -u)"
  runtime_dir="/run/user/${uid}"

  if [ -z "${XDG_RUNTIME_DIR:-}" ] && [ -d "${runtime_dir}" ]; then
    export XDG_RUNTIME_DIR=/run/user/${uid}
  fi
  if [ -z "${WAYLAND_DISPLAY:-}" ] && [ -n "${XDG_RUNTIME_DIR:-}" ] && [ -S "${XDG_RUNTIME_DIR}/wayland-0" ]; then
    export WAYLAND_DISPLAY=wayland-0
  fi
  if [ -z "${DISPLAY:-}" ] && [ -S /tmp/.X11-unix/X0 ]; then
    export DISPLAY=:0
  fi
  if [ -z "${XAUTHORITY:-}" ] && [ -n "${HOME:-}" ] && [ -r "${HOME}/.Xauthority" ]; then
    export XAUTHORITY=${HOME}/.Xauthority
  fi
  if [ -z "${HEADUNIT_HUD_SDL_VIDEODRIVER:-}" ] && [ -z "${DISPLAY:-}" ] && [ -z "${WAYLAND_DISPLAY:-}" ] && { [ -e /dev/dri/card0 ] || [ -e /dev/dri/renderD128 ]; }; then
    export SDL_VIDEODRIVER=kmsdrm
  fi
}

APP_DIR="${HEADUNIT_HUD_APP_DIR:-${ROOT_DIR}}"
PI_DIR="${HEADUNIT_HUD_PI_DIR:-${APP_DIR}/pi-hud}"
LAYOUT="${HEADUNIT_HUD_LAYOUT:-${APP_DIR}/layouts/avante_hd_2010_default.json}"
WIDTH="${HEADUNIT_HUD_WIDTH:-1920}"
HEIGHT="${HEADUNIT_HUD_HEIGHT:-480}"
LANGUAGE="${HEADUNIT_HUD_LANGUAGE:-}"
UDP_PORT="${HEADUNIT_HUD_UDP_PORT:-4210}"
DISCOVERY_PORT="${HEADUNIT_HUD_DISCOVERY_PORT:-4211}"
OBD_PORT="${HEADUNIT_HUD_OBD_PORT:-}"
OBD_BAUD="${HEADUNIT_HUD_OBD_BAUD:-38400}"
OBD_BLE_MAC="${HEADUNIT_HUD_OBD_BLE_MAC:-}"
OBD_BLE_RX_UUID="${HEADUNIT_HUD_OBD_BLE_RX_UUID:-}"
OBD_BLE_TX_UUID="${HEADUNIT_HUD_OBD_BLE_TX_UUID:-}"
CAN_CHANNEL="${HEADUNIT_HUD_CAN_CHANNEL:-}"

configure_display_environment
if [ -n "${HEADUNIT_HUD_SDL_VIDEODRIVER:-}" ]; then
  export SDL_VIDEODRIVER="${HEADUNIT_HUD_SDL_VIDEODRIVER}"
fi
export PYGAME_HIDE_SUPPORT_PROMPT=1

PYTHON="${HEADUNIT_HUD_PYTHON:-}"
if [ -z "${PYTHON}" ]; then
  if [ -x "${APP_DIR}/.venv/bin/python" ]; then
    PYTHON="${APP_DIR}/.venv/bin/python"
  elif [ -x "${PI_DIR}/.venv/bin/python" ]; then
    PYTHON="${PI_DIR}/.venv/bin/python"
  else
    PYTHON=python3
  fi
fi

ARGS=(
  "${PI_DIR}/run.py"
  --layout "${LAYOUT}"
  --width "${WIDTH}"
  --height "${HEIGHT}"
  --udp-port "${UDP_PORT}"
  --discovery-port "${DISCOVERY_PORT}"
  --obd-baud "${OBD_BAUD}"
)

if [ -n "${LANGUAGE}" ]; then
  ARGS+=(--language "${LANGUAGE}")
fi

if truthy "${HEADUNIT_HUD_WINDOWED:-0}"; then
  ARGS+=(--windowed)
fi
if truthy "${HEADUNIT_HUD_DUMMY:-0}"; then
  ARGS+=(--dummy)
fi
if truthy "${HEADUNIT_HUD_DISABLE_DISCOVERY:-0}"; then
  ARGS+=(--disable-discovery)
fi
if truthy "${HEADUNIT_HUD_REQUIRE_HANDOFF:-0}"; then
  ARGS+=(--require-layout-handoff)
fi
if [ -n "${OBD_PORT}" ]; then
  ARGS+=(--obd-port "${OBD_PORT}")
elif [ -n "${OBD_BLE_MAC}" ]; then
  ARGS+=(
    --obd-ble-mac "${OBD_BLE_MAC}"
    --obd-ble-rx-uuid "${OBD_BLE_RX_UUID}"
    --obd-ble-tx-uuid "${OBD_BLE_TX_UUID}"
  )
fi
if [ -n "${CAN_CHANNEL}" ]; then
  ARGS+=(--can-channel "${CAN_CHANNEL}")
fi

echo "[INFO] HUD display env DISPLAY=${DISPLAY:-none}, WAYLAND_DISPLAY=${WAYLAND_DISPLAY:-none}, XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-none}, SDL_VIDEODRIVER=${SDL_VIDEODRIVER:-auto}"
echo "[INFO] HUD runtime display ${WIDTH}x${HEIGHT}, windowed=${HEADUNIT_HUD_WINDOWED:-0}, dummy=${HEADUNIT_HUD_DUMMY:-0}, SDL_VIDEODRIVER=${SDL_VIDEODRIVER:-auto}"

cd "${APP_DIR}"
exec "${PYTHON}" "${ARGS[@]}"
