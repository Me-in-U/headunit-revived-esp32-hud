#!/usr/bin/env bash
set -euo pipefail

update_failed() {
  local exit_code="$1"
  local command="$2"
  echo "[FAIL] update failed while running: ${command}" >&2
  exit "${exit_code}"
}
trap 'update_failed "$?" "$BASH_COMMAND"' ERR

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

truthy() {
  case "${1:-0}" in
    1|true|TRUE|yes|YES|on|ON) return 0 ;;
    *) return 1 ;;
  esac
}

service_is_active() {
  local service="$1"
  systemctl is-active --quiet "${service}"
}

requirements_changed() {
  if "${GIT[@]}" diff --quiet "${CURRENT_HEAD}" "${FETCHED_HEAD}" -- pi-hud/requirements.txt; then
    return 1
  fi
  local status="$?"
  if [ "${status}" -eq 1 ]; then
    return 0
  fi
  return "${status}"
}

restart_service() {
  local service="$1"
  if ! service_is_active "${service}"; then
    echo "[OK] ${service} is not active; leaving it stopped after update"
    return 0
  fi
  if systemctl restart "${service}"; then
    return 0
  fi
  echo "[WARN] updated git checkout, but failed to restart ${service}" >&2
  systemctl status "${service}" -n 30 --no-pager || true
  journalctl -u "${service}" -n 80 --no-pager || true
  return 0
}

if ! truthy "${HEADUNIT_HUD_AUTO_UPDATE:-0}"; then
  echo "[SKIP] HEADUNIT_HUD_AUTO_UPDATE is disabled"
  exit 0
fi

APP_DIR="${HEADUNIT_HUD_APP_DIR:-/opt/headunit-pi-hud}"
REMOTE="${HEADUNIT_HUD_GIT_REMOTE:-origin}"
BRANCH="${HEADUNIT_HUD_GIT_BRANCH:-main}"
SERVICE="${HEADUNIT_HUD_UPDATE_SERVICE:-headunit-pi-hud.service}"

if [ ! -d "${APP_DIR}/.git" ]; then
  echo "[SKIP] ${APP_DIR} is not a git checkout"
  exit 0
fi

APP_DIR="$(cd "${APP_DIR}" && pwd -P)"
GIT=(git -c "safe.directory=${APP_DIR}" -c "core.fileMode=false")
cd "${APP_DIR}"

CURRENT_HEAD="$("${GIT[@]}" rev-parse HEAD)"
"${GIT[@]}" fetch "${REMOTE}" "${BRANCH}"
FETCHED_HEAD="$("${GIT[@]}" rev-parse FETCH_HEAD)"

if [ "${CURRENT_HEAD}" = "${FETCHED_HEAD}" ]; then
  echo "[OK] already up to date at ${CURRENT_HEAD}"
  exit 0
fi

REQUIREMENTS_CHANGED=0
if requirements_changed; then
  REQUIREMENTS_CHANGED=1
else
  status="$?"
  if [ "${status}" -ne 1 ]; then
    exit "${status}"
  fi
fi

"${GIT[@]}" merge --ff-only FETCH_HEAD

PYTHON="${HEADUNIT_HUD_PYTHON:-}"
if [ -z "${PYTHON}" ]; then
  if [ -x "${APP_DIR}/.venv/bin/python" ]; then
    PYTHON="${APP_DIR}/.venv/bin/python"
  else
    PYTHON=python3
  fi
fi

if [ -f "${APP_DIR}/pi-hud/requirements.txt" ]; then
  if [ "${REQUIREMENTS_CHANGED}" = "1" ]; then
    "${PYTHON}" -m pip install -r "${APP_DIR}/pi-hud/requirements.txt"
  else
    echo "[OK] requirements unchanged; skipping pip install"
  fi
fi

restart_service "${SERVICE}"
echo "[OK] updated ${APP_DIR} from ${CURRENT_HEAD} to ${FETCHED_HEAD}"
