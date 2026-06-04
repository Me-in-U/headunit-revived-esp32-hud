#!/usr/bin/env bash
set -euo pipefail

CHANNEL="${1:-can0}"
BITRATE="${2:-500000}"
LISTEN_ONLY="${3:-on}"

run_ip() {
  if [ "$(id -u)" -eq 0 ]; then
    ip "$@"
  else
    sudo ip "$@"
  fi
}

run_ip link set "${CHANNEL}" down 2>/dev/null || true
run_ip link set "${CHANNEL}" up type can bitrate "${BITRATE}" listen-only "${LISTEN_ONLY}"
ip -details link show "${CHANNEL}"
