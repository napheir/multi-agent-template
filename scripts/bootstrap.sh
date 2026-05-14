#!/usr/bin/env bash
# Multi-agent project bootstrap (POSIX)
# Phase 1.4 minimal implementation: single-clone bootstrap for example projects.

set -euo pipefail

PROJECT_ROOT="${1:?usage: bootstrap.sh PROJECT_ROOT [AGENTS [RITUAL_PHRASE]]}"
AGENTS="${2:-core,data}"
RITUAL_PHRASE="${3:-Acknowledged}"

echo "[bootstrap] Project root: $PROJECT_ROOT"
echo "[bootstrap] Agents:       $AGENTS"
echo "[bootstrap] Ritual phrase: $RITUAL_PHRASE"

mkdir -p "$PROJECT_ROOT"

if [ ! -d "$PROJECT_ROOT/.git" ]; then
    git -C "$PROJECT_ROOT" init -b master >/dev/null
    echo "[bootstrap] Initialized git repo."
fi

PROJECT_NAME="$(basename "$PROJECT_ROOT")"
INSTALL_ROOT="$(dirname "$PROJECT_ROOT")"
SHARED_STATE_ROOT="${INSTALL_ROOT}/shared_state/${PROJECT_NAME}"

# Build agents JSON
IFS=',' read -ra AGENT_ARR <<< "$AGENTS"
AGENTS_JSON="["
for i in "${!AGENT_ARR[@]}"; do
    a="${AGENT_ARR[$i]}"
    if [ "$a" = "core" ]; then
        branch="master"
    else
        branch="feature/$a"
    fi
    if [ "$i" -gt 0 ]; then AGENTS_JSON+=","; fi
    AGENTS_JSON+="{\"name\":\"$a\",\"branch\":\"$branch\",\"clone_dir\":\"agent-$a\"}"
done
AGENTS_JSON+="]"

CORE_AGENT_NAME="${AGENT_ARR[0]}"
OVERRIDES=$(printf '{"project_name":"%s","ritual_phrase":"%s","install_root":"%s","shared_state_root":"%s","core_agent_name":"%s","agents":%s}' \
    "$PROJECT_NAME" "$RITUAL_PHRASE" "$INSTALL_ROOT" "$SHARED_STATE_ROOT" "$CORE_AGENT_NAME" "$AGENTS_JSON")

echo "[bootstrap] Calling governance-core install..."
governance-core install --project-root "$PROJECT_ROOT" --config-overrides "$OVERRIDES" --force

if [ -n "$(git -C "$PROJECT_ROOT" status --porcelain)" ]; then
    git -C "$PROJECT_ROOT" add -A
    git -C "$PROJECT_ROOT" commit -m "chore: bootstrap $PROJECT_NAME via multi-agent-template + governance-core" >/dev/null
    echo "[bootstrap] Initial commit created."
fi

echo "[bootstrap] Done. Verify with:"
echo "  governance-core doctor --project-root $PROJECT_ROOT"
