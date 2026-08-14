#!/usr/bin/env bash
set -euo pipefail

ROOT_BASH="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
to_native_path() {
  case "$1" in
    /mnt/[a-z]/*)
      local drive="${1:5:1}"
      local rest="${1:7}"
      printf '%s:/%s' "${drive^^}" "$rest"
      ;;
    /[a-z]/*)
      local drive="${1:1:1}"
      local rest="${1:3}"
      printf '%s:/%s' "${drive^^}" "$rest"
      ;;
    *)
      printf '%s' "$1"
      ;;
  esac
}
ROOT="$(to_native_path "$ROOT_BASH")"
PYTHON="${CTXMAP_PYTHON:-$ROOT_BASH/.venv/Scripts/python.exe}"
cd "$ROOT_BASH"
if [[ ! -x "$PYTHON" ]]; then
  if command -v python3 >/dev/null 2>&1; then
    PYTHON="$(command -v python3)"
  elif command -v python >/dev/null 2>&1; then
    PYTHON="$(command -v python)"
  fi
fi
if [[ "$PYTHON" == *.exe ]]; then
  PY_ROOT="$ROOT"
else
  PY_ROOT="$ROOT_BASH"
fi
ALLOWLIST_FILE=""
NO_COMMIT=0
NO_PUSH=0
WATCH_MODE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --allowlist-file)
      [[ $# -ge 2 ]] || { echo "[auto-commit] ALLOWLIST_REQUIRED" >&2; exit 1; }
      ALLOWLIST_FILE="$2"
      shift 2
      ;;
    --no-commit)
      NO_COMMIT=1
      shift
      ;;
    --no-push)
      NO_PUSH=1
      shift
      ;;
    --watch-mode)
      WATCH_MODE=1
      shift
      ;;
    *)
      echo "[auto-commit] UNKNOWN_ARGUMENT" >&2
      exit 1
      ;;
  esac
done

if [[ -z "$ALLOWLIST_FILE" ]]; then
  echo "[auto-commit] ALLOWLIST_REQUIRED" >&2
  exit 1
fi
case "$ALLOWLIST_FILE" in
  /*|/mnt/*|[A-Za-z]:\\*|[A-Za-z]:/*)
    echo "[auto-commit] ALLOWLIST_PATH_MUST_BE_REPOSITORY_RELATIVE" >&2
    exit 1
    ;;
esac

if ! git diff --cached --quiet; then
  echo "[auto-commit] PREEXISTING_INDEX_DIRTY" >&2
  exit 1
fi

if [[ -z "$(git status --short)" ]]; then
  echo "[auto-commit] No changes detected."
  exit 0
fi

REPORT="$PY_ROOT/plan/context_index/runtime/auto_commit_gate_report.json"
mkdir -p "$ROOT_BASH/plan/context_index/runtime"
GATE_ARGS=(
  -m scripts.context_index.check_context_gate
  --root "$PY_ROOT"
  --changed-list "$ALLOWLIST_FILE"
  --report "$REPORT"
)
if [[ "$WATCH_MODE" -eq 1 ]]; then
  GATE_ARGS+=(--require-h1 --h1-receipt "${CTXMAP_H1_RECEIPT:-$ROOT/plan/context_index/CTXMAP-H1_approval.json}")
fi
if [[ -n "${CTXMAP_A07_RESPONSES:-}" ]]; then
  case "$CTXMAP_A07_RESPONSES" in
    /*|/mnt/*|[A-Za-z]:\\*|[A-Za-z]:/*)
      echo "[auto-commit] A07_RESPONSES_PATH_MUST_BE_REPOSITORY_RELATIVE" >&2
      exit 1
      ;;
  esac
  GATE_ARGS+=(--a07-responses "$CTXMAP_A07_RESPONSES")
fi

GATE_OUTPUT=""
if ! GATE_OUTPUT=$("$PYTHON" "${GATE_ARGS[@]}"); then
  echo "[auto-commit] Gate failed; index was not changed." >&2
  exit 1
fi
EXPECTED_REPORT_HASH=""
if ! EXPECTED_REPORT_HASH=$("$PYTHON" -c 'import json, sys; value = json.loads(sys.stdin.read()); status = value.get("status"); digest = value.get("report_sha256"); sys.exit(1) if status != "PASS" or not isinstance(digest, str) else print(digest)' <<<"$GATE_OUTPUT"); then
  echo "[auto-commit] Gate report fingerprint was not returned." >&2
  exit 1
fi
if [[ ! "$EXPECTED_REPORT_HASH" =~ ^[a-f0-9]{64}$ ]]; then
  echo "[auto-commit] Gate report fingerprint was invalid." >&2
  exit 1
fi

APPROVED_FILE="$ROOT_BASH/plan/context_index/runtime/auto_commit_allowlist.txt"
if ! "$PYTHON" -c 'import sys; from pathlib import Path; from scripts.context_index.check_context_gate import approved_paths_from_report; print("\n".join(approved_paths_from_report(Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3])))' "$REPORT" "$PY_ROOT" "$EXPECTED_REPORT_HASH" > "$APPROVED_FILE"; then
  echo "[auto-commit] Gate allowlist could not be revalidated." >&2
  exit 1
fi
mapfile -t ALLOWED_PATHS < "$APPROVED_FILE"
if [[ "${#ALLOWED_PATHS[@]}" -eq 0 ]]; then
  echo "[auto-commit] No gate-approved paths."
  exit 0
fi

git add -- "${ALLOWED_PATHS[@]}"

if ! "$PYTHON" -c 'import sys; from pathlib import Path; from scripts.context_index.check_context_gate import verify_index_matches_report; verify_index_matches_report(Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3])' "$REPORT" "$PY_ROOT" "$EXPECTED_REPORT_HASH"; then
  git reset --quiet -- "${ALLOWED_PATHS[@]}" >/dev/null 2>&1 || true
  echo "[auto-commit] Gate-approved content changed before commit; index was restored." >&2
  exit 1
fi

if [[ "$NO_COMMIT" -eq 1 ]]; then
  echo "[auto-commit] Gate-approved paths staged; commit skipped."
  exit 0
fi

timestamp="$(date '+%Y-%m-%d %H:%M:%S')"
branch="$(git branch --show-current)"
if [[ -z "$branch" ]]; then
  echo "[auto-commit] Could not determine the current branch." >&2
  exit 1
fi

git commit --only -m "auto: update by Codex [$timestamp]" -- "${ALLOWED_PATHS[@]}"
if [[ "$NO_PUSH" -eq 0 ]]; then
  git push origin "$branch"
fi
