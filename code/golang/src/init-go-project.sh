#!/usr/bin/env bash
# Scaffolds a standard Go project layout in the current directory.
# Usage: init-go-project.sh <application-name> [--ghcr|--dockerhub] [--no-windows]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── Args ──────────────────────────────────────────────────────────────────────
APPLICATION="${1:-}"
REGISTRY="ghcr"   # ghcr | dockerhub
WINDOWS=true

if [[ -z "$APPLICATION" ]]; then
    # Try to infer from go.mod
    if [[ -f go.mod ]]; then
        APPLICATION=$(awk '/^module /{print $2}' go.mod | awk -F/ '{print $NF}')
    fi
fi

if [[ -z "$APPLICATION" ]]; then
    echo "Usage: $0 <application-name> [--ghcr|--dockerhub] [--no-windows]" >&2
    exit 1
fi

shift || true
for arg in "$@"; do
    case "$arg" in
        --ghcr)       REGISTRY="ghcr" ;;
        --dockerhub)  REGISTRY="dockerhub" ;;
        --no-windows) WINDOWS=false ;;
        *) echo "Unknown flag: $arg" >&2; exit 1 ;;
    esac
done

echo "Scaffolding Go project: ${APPLICATION} (registry=${REGISTRY}, windows=${WINDOWS})"

# ── Directory layout ──────────────────────────────────────────────────────────
mkdir -p \
    "build/package" \
    "cmd/${APPLICATION}" \
    "deployments" \
    "docs/decisions" \
    "internal" \
    "scripts" \
    "test/integration" \
    "test/functional" \
    "test/smoke" \
    "test/e2e" \
    ".github/workflows"

# ── scripts/variables.mk ──────────────────────────────────────────────────────
if [[ ! -f scripts/variables.mk ]]; then
    cp "${SCRIPT_DIR}/templates/variables.mk" scripts/variables.mk
    echo "  [create] scripts/variables.mk"
fi

# ── scripts/go.mk ─────────────────────────────────────────────────────────────
if [[ ! -f scripts/go.mk ]]; then
    cp "${SCRIPT_DIR}/templates/go.mk" scripts/go.mk
    echo "  [create] scripts/go.mk"
fi

# ── Makefile ──────────────────────────────────────────────────────────────────
if [[ ! -f Makefile ]]; then
    cp "${SCRIPT_DIR}/templates/Makefile" Makefile
    echo "  [create] Makefile"
fi

# ── Dockerfile ────────────────────────────────────────────────────────────────
if [[ ! -f build/package/Dockerfile ]]; then
    sed "s/{{APPLICATION}}/${APPLICATION}/g" \
        "${SCRIPT_DIR}/templates/Dockerfile" > build/package/Dockerfile
    echo "  [create] build/package/Dockerfile"
fi

# ── cmd/<app>/main.go ─────────────────────────────────────────────────────────
if [[ ! -f "cmd/${APPLICATION}/main.go" ]]; then
    sed "s/{{APPLICATION}}/${APPLICATION}/g" \
        "${SCRIPT_DIR}/templates/main.go.tmpl" > "cmd/${APPLICATION}/main.go"
    echo "  [create] cmd/${APPLICATION}/main.go"
fi

# ── GitHub workflow: docker.yml ───────────────────────────────────────────────
if [[ ! -f .github/workflows/docker.yml ]]; then
    sed "s/{{APPLICATION}}/${APPLICATION}/g" \
        "${SCRIPT_DIR}/templates/docker-${REGISTRY}.yml" > .github/workflows/docker.yml
    echo "  [create] .github/workflows/docker.yml (${REGISTRY})"
fi

# ── GitHub workflow: release.yml ──────────────────────────────────────────────
if [[ ! -f .github/workflows/release.yml ]]; then
    if [[ "$WINDOWS" == "true" ]]; then
        sed "s/{{APPLICATION}}/${APPLICATION}/g" \
            "${SCRIPT_DIR}/templates/release-all.yml" > .github/workflows/release.yml
    else
        sed "s/{{APPLICATION}}/${APPLICATION}/g" \
            "${SCRIPT_DIR}/templates/release-nix.yml" > .github/workflows/release.yml
    fi
    echo "  [create] .github/workflows/release.yml (windows=${WINDOWS})"
fi

echo ""
echo "Done. Next steps:"
echo "  1. Run 'go mod init github.com/jnovack/${APPLICATION}' if go.mod doesn't exist"
echo "  2. Review and commit the generated files"
echo "  3. Add lang-golang snippet to CLAUDE.md via /claude-init"
