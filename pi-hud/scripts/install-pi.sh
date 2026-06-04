#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${1:-/opt/headunit-pi-hud}"
SERVICE_FILE=/etc/systemd/system/headunit-pi-hud.service
UPDATE_SERVICE_FILE=/etc/systemd/system/headunit-pi-hud-update.service
UPDATE_TIMER_FILE=/etc/systemd/system/headunit-pi-hud-update.timer
ENV_FILE=/etc/headunit-pi-hud.env

if [ "$(id -u)" -ne 0 ]; then
  echo "Run with sudo: sudo $0 [install-dir]" >&2
  exit 2
fi

DEFAULT_SERVICE_USER="${SUDO_USER:-}"
if [ -z "${DEFAULT_SERVICE_USER}" ] || [ "${DEFAULT_SERVICE_USER}" = "root" ]; then
  DEFAULT_SERVICE_USER="$(logname 2>/dev/null || true)"
fi
if [ -z "${DEFAULT_SERVICE_USER}" ] || [ "${DEFAULT_SERVICE_USER}" = "root" ]; then
  DEFAULT_SERVICE_USER="$(getent passwd 1000 | cut -d: -f1 || true)"
fi
if [ -z "${DEFAULT_SERVICE_USER}" ]; then
  DEFAULT_SERVICE_USER=pi
fi
SERVICE_USER="${HEADUNIT_HUD_USER:-${DEFAULT_SERVICE_USER}}"
if ! id -u "${SERVICE_USER}" >/dev/null 2>&1; then
  echo "Service user '${SERVICE_USER}' does not exist. Set HEADUNIT_HUD_USER to the Pi login user and rerun." >&2
  exit 3
fi

SRC_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"

apt-get update
apt-get install -y python3-venv python3-pip can-utils bluez git fonts-noto-cjk

install -d "${APP_DIR}"
if command -v rsync >/dev/null 2>&1; then
  rsync -a --delete \
    --exclude .gradle \
    --exclude '.venv' \
    --exclude 'android-app/build' \
    --exclude 'bridge-core/build' \
    "${SRC_DIR}/" "${APP_DIR}/"
else
  cp -a "${SRC_DIR}/." "${APP_DIR}/"
fi

python3 -m venv "${APP_DIR}/.venv"
"${APP_DIR}/.venv/bin/python" -m pip install --upgrade pip
"${APP_DIR}/.venv/bin/python" -m pip install -r "${APP_DIR}/pi-hud/requirements.txt"

if [ ! -f "${ENV_FILE}" ]; then
  install -m 0644 "${APP_DIR}/pi-hud/config/pi-hud.env.example" "${ENV_FILE}"
fi

chmod 0755 \
  "${APP_DIR}/pi-hud/scripts/canable-up.sh" \
  "${APP_DIR}/pi-hud/scripts/icar-rfcomm-bind.sh" \
  "${APP_DIR}/pi-hud/scripts/setup-obd-from-env.sh" \
  "${APP_DIR}/pi-hud/scripts/run-from-env.sh" \
  "${APP_DIR}/pi-hud/scripts/setup-canable-from-env.sh" \
  "${APP_DIR}/pi-hud/scripts/collect-vehicle-baseline.py" \
  "${APP_DIR}/pi-hud/scripts/first-run-status.py" \
  "${APP_DIR}/pi-hud/scripts/acceptance-check.py" \
  "${APP_DIR}/pi-hud/scripts/summarize-can-baseline.py" \
  "${APP_DIR}/pi-hud/scripts/scan-ble-obd.py" \
  "${APP_DIR}/pi-hud/scripts/auto-configure-hardware.py" \
  "${APP_DIR}/pi-hud/scripts/build-field-pack.py" \
  "${APP_DIR}/pi-hud/scripts/apply-field-pack.py" \
  "${APP_DIR}/pi-hud/scripts/diagnose-inputs.py" \
  "${APP_DIR}/pi-hud/scripts/verify-layout.py" \
  "${APP_DIR}/pi-hud/scripts/update-from-git.sh" \
  "${APP_DIR}/pi-hud/scripts/probe-bridge.py"

if [ "${HEADUNIT_HUD_SKIP_AUTO_CONFIG:-0}" != "1" ]; then
  "${APP_DIR}/.venv/bin/python" \
    "${APP_DIR}/pi-hud/scripts/auto-configure-hardware.py" \
    --apply \
    --no-restart \
    --env-file "${ENV_FILE}" || true
fi

sed \
  -e "s|^User=.*|User=${SERVICE_USER}|" \
  -e "s|/opt/headunit-pi-hud|${APP_DIR}|g" \
  "${APP_DIR}/pi-hud/systemd/headunit-pi-hud.service" > "${SERVICE_FILE}"

sed \
  -e "s|/opt/headunit-pi-hud|${APP_DIR}|g" \
  "${APP_DIR}/pi-hud/systemd/headunit-pi-hud-update.service" > "${UPDATE_SERVICE_FILE}"

sed \
  "${APP_DIR}/pi-hud/systemd/headunit-pi-hud-update.timer" > "${UPDATE_TIMER_FILE}"

usermod -aG dialout,video,render,input,bluetooth "${SERVICE_USER}" || true

systemctl daemon-reload
systemctl enable headunit-pi-hud.service
systemctl enable headunit-pi-hud-update.timer

echo "Installed ${SERVICE_FILE}"
echo "Installed ${UPDATE_SERVICE_FILE}"
echo "Installed ${UPDATE_TIMER_FILE}"
echo "Hardware auto-config was attempted. Edit ${ENV_FILE} only if iCar/CANable values are still missing, then run:"
echo "  sudo systemctl restart headunit-pi-hud.service"
echo "  sudo journalctl -u headunit-pi-hud.service -f"
echo "Git updates are enabled by default with HEADUNIT_HUD_AUTO_UPDATE=1 in ${ENV_FILE}."
