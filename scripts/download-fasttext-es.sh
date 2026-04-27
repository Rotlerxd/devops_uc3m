#!/usr/bin/env bash
# scripts/download-fasttext-es.sh — Download Spanish fastText vectors for local development
if [ -z "${BASH_VERSION:-}" ]; then
    exec bash "$0" "$@"
fi
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
MODEL_DIR="$ROOT_DIR/.models/fasttext"
MODEL_GZ_PATH="$MODEL_DIR/cc.es.300.bin.gz"
MODEL_PATH="$MODEL_DIR/cc.es.300.bin"
MODEL_URL="https://dl.fbaipublicfiles.com/fasttext/vectors-crawl/cc.es.300.bin.gz"
FORCE=false

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

show_help() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Download the Spanish fastText binary vectors used by the optional synonym fallback.

OPTIONS:
    --force      Re-download and overwrite the local model
    -h, --help   Show this help message

OUTPUT:
    $MODEL_PATH

EXAMPLES:
    $(basename "$0")
    $(basename "$0") --force

EOF
}

download_file() {
    if command -v curl &>/dev/null; then
        curl -L --fail --progress-bar "$MODEL_URL" -o "$MODEL_GZ_PATH"
    elif command -v wget &>/dev/null; then
        wget -O "$MODEL_GZ_PATH" "$MODEL_URL"
    else
        log_error "curl or wget is required to download fastText vectors"
        exit 1
    fi
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --force)
            FORCE=true
            shift
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

mkdir -p "$MODEL_DIR"

if [[ -f "$MODEL_PATH" && "$FORCE" != true ]]; then
    log_info "Spanish fastText model already exists: $MODEL_PATH"
    log_info "Use --force to re-download it."
    exit 0
fi

log_warn "This downloads the Spanish fastText binary model. It is large and remains untracked."
log_info "Source: $MODEL_URL"

rm -f "$MODEL_GZ_PATH"
download_file

log_info "Decompressing model..."
gzip -dc "$MODEL_GZ_PATH" > "$MODEL_PATH"
rm -f "$MODEL_GZ_PATH"

log_info "Spanish fastText model ready: $MODEL_PATH"
log_info "Start dev with: scripts/start-dev.sh --both-parallel --fasttext"
