#!/usr/bin/env bash
# scripts/start-dev.sh — Start the development environment
if [ -z "${BASH_VERSION:-}" ]; then
    exec bash "$0" "$@"
fi
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$ROOT_DIR/Backend"
FRONTEND_DIR="$ROOT_DIR/Frontend"
VENV_PYTHON="$ROOT_DIR/.venv/bin/python"
VENV_PIP="$ROOT_DIR/.venv/bin/pip"
DEFAULT_FASTTEXT_MODEL_PATH="$ROOT_DIR/.models/fasttext/cc.es.300.bin"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

cleanup() {
    log_info "Stopping services..."
    if [[ -n "${BACKEND_PID:-}" ]]; then
        kill "$BACKEND_PID" 2>/dev/null || true
    fi
    if [[ -n "${FRONTEND_PID:-}" ]]; then
        kill "$FRONTEND_PID" 2>/dev/null || true
    fi
    if [[ -n "${COMPOSE_PID:-}" ]]; then
        kill "$COMPOSE_PID" 2>/dev/null || true
    fi
    log_info "Cleanup complete."
    exit 0
}
trap cleanup SIGINT SIGTERM

show_help() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Start the development environment (backend + frontend).

OPTIONS:
    --backend         Start only the backend in foreground
    --frontend        Start only the frontend in foreground
    --both            Start both services in background
    --both-parallel   Start both services in foreground with interleaved output
    --fasttext        Enable local fastText suggestions using .models/fasttext/cc.es.300.bin
    --fasttext-model PATH
                      Enable local fastText suggestions using a custom .bin model path
    -h, --help        Show this help message

EXAMPLES:
    $(basename "$0") --backend         # Start only backend
    $(basename "$0") --frontend        # Start only frontend
    $(basename "$0") --both            # Start both in background
    $(basename "$0") --both-parallel   # Start both in foreground
    $(basename "$0") --both-parallel --fasttext
    $(basename "$0") --backend --fasttext-model /path/to/cc.es.300.bin

EOF
}

check_uv() {
    if command -v uv &>/dev/null; then
        return 0
    else
        return 1
    fi
}

choose_python() {
    if command -v python3.11 &>/dev/null; then
        command -v python3.11
    elif command -v python3 &>/dev/null; then
        command -v python3
    else
        return 1
    fi
}

check_venv() {
    if [[ ! -d "$ROOT_DIR/.venv" ]]; then
        if check_uv; then
            log_info "Creating virtual environment with uv..."
            cd "$ROOT_DIR" && uv venv
        else
            PYTHON_BIN="$(choose_python)" || {
                log_error "No python3 interpreter found to create the virtual environment"
                exit 1
            }
            log_info "Creating virtual environment with python..."
            "$PYTHON_BIN" -m venv "$ROOT_DIR/.venv"
        fi
    fi

    if [[ ! -f "$VENV_PYTHON" ]]; then
        log_error "Virtual environment Python not found at $VENV_PYTHON"
        exit 1
    fi
}

install_backend_deps() {
    log_info "Checking backend dependencies..."
    if check_uv; then
        cd "$ROOT_DIR" && uv pip install -r "$BACKEND_DIR/requirements.txt" -r "$BACKEND_DIR/requirements-dev.txt"
    else
        "$VENV_PIP" install -r "$BACKEND_DIR/requirements.txt"
        "$VENV_PIP" install -r "$BACKEND_DIR/requirements-dev.txt"
    fi
}

install_frontend_deps() {
    log_info "Checking frontend dependencies..."
    if [[ -f "$FRONTEND_DIR/package.json" ]]; then
        if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
            log_info "Installing frontend dependencies..."
            cd "$FRONTEND_DIR" && npm install
        fi
    fi
}

start_databases() {
    log_info "Starting databases..."
    cd "$BACKEND_DIR"
    docker compose up -d
    log_info "Waiting for databases to be ready..."
    sleep 3
    cd "$ROOT_DIR"
}

run_migrations() {
    log_info "Checking database migrations..."
    cd "$BACKEND_DIR"
    if ! "$VENV_PYTHON" -c "import psycopg2" 2>/dev/null; then
        log_warn "psycopg2 not installed, skipping migrations"
        cd "$ROOT_DIR"
        return
    fi
    "$VENV_PYTHON" -m alembic upgrade head 2>/dev/null || \
    "$VENV_PYTHON" -m alembic upgrade head
    cd "$ROOT_DIR"
}

configure_fasttext() {
    FASTTEXT_ENV_ARGS=()

    if [[ -z "${FASTTEXT_MODEL_PATH:-}" ]]; then
        return
    fi

    if [[ ! -f "$FASTTEXT_MODEL_PATH" ]]; then
        log_warn "fastText model not found at $FASTTEXT_MODEL_PATH"
        log_warn "Run: scripts/download-fasttext-es.sh"
        log_warn "Starting backend without fastText fallback."
        return
    fi

    FASTTEXT_ENV_ARGS=("NEWSRADAR_FASTTEXT_MODEL_PATH=$FASTTEXT_MODEL_PATH")
    log_info "Using fastText Spanish model: $FASTTEXT_MODEL_PATH"
}

start_backend() {
    log_info "Starting backend..."
    cd "$BACKEND_DIR"
    env NEWSRADAR_CONFIGURE_LOCAL_ELASTICSEARCH=true "${FASTTEXT_ENV_ARGS[@]}" "$VENV_PYTHON" -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
    BACKEND_PID=$!
    cd "$ROOT_DIR"
    log_info "Backend started on http://localhost:8000"
}

start_backend_blocking() {
    log_info "Starting backend (blocking)..."
    cd "$BACKEND_DIR"
    exec env NEWSRADAR_CONFIGURE_LOCAL_ELASTICSEARCH=true "${FASTTEXT_ENV_ARGS[@]}" "$VENV_PYTHON" -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
}

start_frontend() {
    log_info "Starting frontend..."
    cd "$FRONTEND_DIR"
    npm run dev &
    FRONTEND_PID=$!
    cd "$ROOT_DIR"
    log_info "Frontend started"
}

start_frontend_blocking() {
    log_info "Starting frontend (blocking)..."
    cd "$FRONTEND_DIR"
    exec npm run dev
}

wait_for_services() {
    if [[ -n "${BACKEND_PID:-}" && -n "${FRONTEND_PID:-}" ]]; then
        log_info "Both services are running. Press Ctrl+C to stop."
        wait $BACKEND_PID $FRONTEND_PID
    elif [[ -n "${BACKEND_PID:-}" ]]; then
        wait $BACKEND_PID
    elif [[ -n "${FRONTEND_PID:-}" ]]; then
        wait $FRONTEND_PID
    fi
}

MODE=""
FASTTEXT_MODEL_PATH="${NEWSRADAR_FASTTEXT_MODEL_PATH:-}"
while [[ $# -gt 0 ]]; do
    case $1 in
        --backend)
            MODE="backend"
            shift
            ;;
        --frontend)
            MODE="frontend"
            shift
            ;;
        --both)
            MODE="both"
            shift
            ;;
        --both-parallel)
            MODE="both-parallel"
            shift
            ;;
        --fasttext)
            FASTTEXT_MODEL_PATH="$DEFAULT_FASTTEXT_MODEL_PATH"
            shift
            ;;
        --fasttext-model)
            if [[ -z "${2:-}" ]]; then
                log_error "--fasttext-model requires a path"
                show_help
                exit 1
            fi
            FASTTEXT_MODEL_PATH="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

if [[ -z "$MODE" ]]; then
    show_help
    exit 1
fi

case "$MODE" in
    backend)
        check_venv
        install_backend_deps
        start_databases
        run_migrations
        configure_fasttext
        start_backend_blocking
        ;;
    frontend)
        install_frontend_deps
        start_frontend_blocking
        ;;
    both)
        check_venv
        install_backend_deps
        install_frontend_deps
        start_databases
        run_migrations
        configure_fasttext
        start_backend
        sleep 2
        start_frontend
        log_info "Both services started in background. Press Ctrl+C to stop."
        wait
        ;;
    both-parallel)
        check_venv
        install_backend_deps
        install_frontend_deps
        start_databases
        run_migrations
        configure_fasttext
        log_info "Starting both services in parallel..."

        cd "$BACKEND_DIR"
        env NEWSRADAR_CONFIGURE_LOCAL_ELASTICSEARCH=true "${FASTTEXT_ENV_ARGS[@]}" "$VENV_PYTHON" -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
        BACKEND_PID=$!
        cd "$ROOT_DIR"

        cd "$FRONTEND_DIR"
        npm run dev &
        FRONTEND_PID=$!
        cd "$ROOT_DIR"

        log_info "Backend started on http://localhost:8000"
        log_info "Frontend started"
        log_info "Both services running. Press Ctrl+C to stop."

        wait $BACKEND_PID $FRONTEND_PID
        ;;
esac
