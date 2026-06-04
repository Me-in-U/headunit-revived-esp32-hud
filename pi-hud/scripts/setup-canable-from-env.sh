#!/usr/bin/env bash
set -euo pipefail

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

CHANNEL="${HEADUNIT_HUD_CAN_CHANNEL:-}"
BITRATE="${HEADUNIT_HUD_CAN_BITRATE:-500000}"
LISTEN_ONLY="${HEADUNIT_HUD_CAN_LISTEN_ONLY:-on}"

if [ -z "${CHANNEL}" ]; then
  echo "HEADUNIT_HUD_CAN_CHANNEL is empty; skipping CAN setup"
  exit 0
fi

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec "${SCRIPT_DIR}/canable-up.sh" "${CHANNEL}" "${BITRATE}" "${LISTEN_ONLY}"
