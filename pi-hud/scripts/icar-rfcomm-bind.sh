#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <icar-bluetooth-mac> [rfcomm-index] [channel]" >&2
  exit 2
fi

MAC_ADDRESS="$1"
RFCOMM_INDEX="${2:-0}"
CHANNEL="${3:-1}"
DEVICE="/dev/rfcomm${RFCOMM_INDEX}"

run_rfcomm() {
  if [ "$(id -u)" -eq 0 ]; then
    rfcomm "$@"
  else
    sudo rfcomm "$@"
  fi
}

run_rfcomm release "${RFCOMM_INDEX}" 2>/dev/null || true
run_rfcomm bind "${RFCOMM_INDEX}" "${MAC_ADDRESS}" "${CHANNEL}"
echo "${DEVICE}"
