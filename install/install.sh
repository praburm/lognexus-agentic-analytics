#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC_DIR="$REPO_ROOT/src"
VENV_DIR="$REPO_ROOT/.venv"
MIN_PYTHON_MINOR=10

check_python() {
    if ! command -v python3 &>/dev/null; then
        echo "[ERROR] python3 not found. Install Python 3.$MIN_PYTHON_MINOR or later." >&2
        exit 1
    fi
    minor=$(python3 -c "import sys; print(sys.version_info.minor)")
    if [[ "$minor" -lt "$MIN_PYTHON_MINOR" ]]; then
        echo "[ERROR] Python 3.$minor found, need 3.$MIN_PYTHON_MINOR+." >&2
        exit 1
    fi
    echo "[OK] $(python3 --version)"
}

create_venv() {
    if [[ -d "$VENV_DIR" ]]; then
        echo "[INFO] Reusing existing venv at $VENV_DIR"
    else
        echo "[INFO] Creating venv at $VENV_DIR"
        python3 -m venv "$VENV_DIR"
    fi
    source "$VENV_DIR/bin/activate"
    pip install --quiet --upgrade pip
    echo "[OK] pip $(pip --version | awk '{print $2}')"
}

install_packages() {
    local req_files=()

    for pkg in anomaly-eval mcp-pipeline observability rca-engine; do
        pkg_dir="$SRC_DIR/$pkg"
        [[ -f "$pkg_dir/requirements.txt" ]]     && req_files+=("$pkg_dir/requirements.txt")
        [[ -f "$pkg_dir/requirements_mcp.txt" ]] && req_files+=("$pkg_dir/requirements_mcp.txt")
    done

    declare -A seen=()
    for f in "${req_files[@]}"; do
        if [[ -z "${seen[$f]+_}" ]]; then
            seen[$f]=1
            echo "[INFO] Installing from $f"
            pip install --quiet -r "$f"
        fi
    done
}

setup_env_file() {
    env_example="$REPO_ROOT/.env.example"

    if [[ ! -f "$REPO_ROOT/.env" ]]; then
        cat > "$env_example" <<'EOF'
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
USE_LLM=false
LOKI_URL=http://localhost:3100
PUSHOVER_TOKEN=
PUSHOVER_USER=
EOF
        echo "[INFO] Created .env.example — copy to .env and set your API keys."
    fi
}

echo "==> LogNexus Agentic Analytics — Install"
echo "    Repo: $REPO_ROOT"
echo ""

check_python
create_venv
install_packages
setup_env_file

echo ""
echo "==> Installation complete."
echo "    Activate the environment with:"
echo "      source $VENV_DIR/bin/activate"
