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

ICAR_MAC="${HEADUNIT_HUD_ICAR_MAC:-}"
RFCOMM_INDEX="${HEADUNIT_HUD_RFCOMM_INDEX:-0}"
RFCOMM_CHANNEL="${HEADUNIT_HUD_RFCOMM_CHANNEL:-1}"

if [ -z "${ICAR_MAC}" ]; then
  echo "HEADUNIT_HUD_ICAR_MAC is empty; skipping iCar rfcomm setup"
  exit 0
fi

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec "${SCRIPT_DIR}/icar-rfcomm-bind.sh" "${ICAR_MAC}" "${RFCOMM_INDEX}" "${RFCOMM_CHANNEL}"
