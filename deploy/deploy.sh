#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC_DIR="$REPO_ROOT/src"
VENV_DIR="$REPO_ROOT/.venv"
PYTHON="$VENV_DIR/bin/python"
LOG_DIR="$REPO_ROOT/deploy/logs"
SESSION="lognexus"

declare -a SERVICE_NAMES=("rca-engine" "mcp-server" "observability" "anomaly-eval")
declare -a SERVICE_DIRS=(
    "$SRC_DIR/rca-engine"
    "$SRC_DIR/mcp-pipeline"
    "$SRC_DIR/observability"
    "$SRC_DIR/anomaly-eval"
)
declare -a SERVICE_CMDS=(
    "$PYTHON app.py"
    "$PYTHON mcp/mcp_server.py"
    "$PYTHON main.py"
    "$PYTHON main.py"
)

usage() {
    echo "Usage: $0 [start|stop|status|logs]"
    echo "  start   — launch all services"
    echo "  stop    — stop all services"
    echo "  status  — show running services"
    echo "  logs    — tail deploy/logs/*.log"
    exit 1
}

check_venv() {
    if [[ ! -x "$PYTHON" ]]; then
        echo "[ERROR] Virtual env not found at $VENV_DIR."
        echo "        Run install/install.sh first."
        exit 1
    fi
}

start_with_tmux() {
    if tmux has-session -t "$SESSION" 2>/dev/null; then
        echo "[INFO] tmux session '$SESSION' already running."
    else
        tmux new-session -d -s "$SESSION" -x 220 -y 50
    fi

    for i in "${!SERVICE_NAMES[@]}"; do
        name="${SERVICE_NAMES[$i]}"
        dir="${SERVICE_DIRS[$i]}"
        cmd="${SERVICE_CMDS[$i]}"
        log="$LOG_DIR/$name.log"

        tmux new-window -t "$SESSION" -n "$name" \
            "cd '$dir' && $cmd 2>&1 | tee '$log'; exec bash" 2>/dev/null || \
        tmux send-keys -t "$SESSION:$name" "cd '$dir' && $cmd 2>&1 | tee '$log'" Enter

        echo "[START] $name — log: deploy/logs/$name.log"
    done

    echo ""
    echo "[INFO] Attach with:  tmux attach -t $SESSION"
}

start_plain() {
    mkdir -p "$LOG_DIR"
    PIDS_FILE="$LOG_DIR/pids"
    : > "$PIDS_FILE"

    for i in "${!SERVICE_NAMES[@]}"; do
        name="${SERVICE_NAMES[$i]}"
        dir="${SERVICE_DIRS[$i]}"
        cmd="${SERVICE_CMDS[$i]}"
        log="$LOG_DIR/$name.log"

        (cd "$dir" && eval "$cmd" > "$log" 2>&1) &
        pid=$!
        echo "$name $pid" >> "$PIDS_FILE"
        echo "[START] $name (pid $pid) — log: deploy/logs/$name.log"
    done
}

do_start() {
    check_venv
    mkdir -p "$LOG_DIR"

    if command -v tmux &>/dev/null; then
        start_with_tmux
    else
        echo "[INFO] tmux not found — launching services as background processes."
        start_plain
    fi

    echo ""
    echo "==> Services started."
    echo "    rca-engine   → http://localhost:8860"
    echo "    mcp-server   → stdio (MCP protocol)"
}

do_stop() {
    if command -v tmux &>/dev/null && tmux has-session -t "$SESSION" 2>/dev/null; then
        tmux kill-session -t "$SESSION"
        echo "[STOP] tmux session '$SESSION' terminated."
    fi

    pids_file="$LOG_DIR/pids"
    if [[ -f "$pids_file" ]]; then
        while read -r name pid; do
            if kill -0 "$pid" 2>/dev/null; then
                kill "$pid" && echo "[STOP] $name (pid $pid)"
            fi
        done < "$pids_file"
        rm -f "$pids_file"
    fi
}

do_status() {
    pids_file="$LOG_DIR/pids"
    if [[ -f "$pids_file" ]]; then
        echo "Running processes:"
        while read -r name pid; do
            if kill -0 "$pid" 2>/dev/null; then
                echo "  [UP]   $name (pid $pid)"
            else
                echo "  [DOWN] $name (pid $pid — not running)"
            fi
        done < "$pids_file"
    elif command -v tmux &>/dev/null && tmux has-session -t "$SESSION" 2>/dev/null; then
        echo "tmux session '$SESSION' is active:"
        tmux list-windows -t "$SESSION"
    else
        echo "[INFO] No running session found."
    fi
}

do_logs() {
    logs=("$LOG_DIR"/*.log)
    if [[ ${#logs[@]} -eq 0 || ! -f "${logs[0]}" ]]; then
        echo "[INFO] No log files found in deploy/logs/"
        exit 0
    fi
    tail -f "${logs[@]}"
}

case "${1:-start}" in
    start)  do_start ;;
    stop)   do_stop  ;;
    status) do_status ;;
    logs)   do_logs  ;;
    *)      usage ;;
esac
