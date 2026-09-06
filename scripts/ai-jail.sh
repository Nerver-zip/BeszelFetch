#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

show_help() {
  cat <<EOF
Usage: $0 [tool] [command] [args...]

Tools:
  agy | antigravity   Run Antigravity CLI inside ai-jail (default)
  codex               Run Codex CLI inside ai-jail

Commands:
  run                 Launch a new session inside ai-jail (default)
  resume [id]         Resume a session by ID (or continue if id omitted)
  resume:last         Resume the most recent session
  help                Show this help message

Examples:
  $0 agy run
  $0 agy resume:last
  $0 agy resume <conversation-id>
  $0 codex run
  $0 codex resume:last
  $0 codex resume [session-id]
  $0 run
EOF
  exit 0
}

# Check if help is requested
if [[ "${1:-}" =~ ^(help|--help|-h)$ ]]; then
  show_help
fi

# Detect tool (codex vs agy/antigravity), default to agy
tool="agy"
if [[ "${1:-}" == "codex" ]]; then
  tool="codex"
  shift
elif [[ "${1:-}" == "agy" || "${1:-}" == "antigravity" ]]; then
  tool="agy"
  shift
fi

subcommand="${1:-run}"

case "$subcommand" in
  help|--help|-h)
    show_help
    ;;
esac

case "$tool" in
  agy)
    mkdir -p "$HOME/.gemini"
    case "$subcommand" in
      run)
        shift || true
        exec ai-jail --exec --display --x11 --terminal-passthrough --network --systemd-user --rw-map "$HOME/.gemini" -- \
          agy --dangerously-skip-permissions "$@"
        ;;
      resume)
        shift || true
        if [[ $# -gt 0 && "${1:-}" != -* ]]; then
          conv_id="$1"
          shift
          exec ai-jail --exec --display --x11 --terminal-passthrough --network --systemd-user --rw-map "$HOME/.gemini" -- \
            agy --dangerously-skip-permissions --conversation "$conv_id" "$@"
        else
          exec ai-jail --exec --display --x11 --terminal-passthrough --network --rw-map "$HOME/.gemini" -- \
            agy --dangerously-skip-permissions --continue "$@"
        fi
        ;;
      resume:last)
        shift || true
        exec ai-jail --exec --display --x11 --terminal-passthrough --network --systemd-user --rw-map "$HOME/.gemini" -- \
          agy --dangerously-skip-permissions --continue "$@"
        ;;
      *)
        exec ai-jail --exec --display --x11 --terminal-passthrough --network --systemd-user --rw-map "$HOME/.gemini" -- \
          agy --dangerously-skip-permissions "$@"
        ;;
    esac
    ;;
  codex)
    mkdir -p "$HOME/.codex"
    case "$subcommand" in
      run)
        shift || true
        exec ai-jail --exec --display --x11 --terminal-passthrough --network --rw-map "$HOME/.codex" -- \
          codex --dangerously-bypass-approvals-and-sandbox "$@"
        ;;
      resume)
        shift || true
        exec ai-jail --exec --display --x11 --terminal-passthrough --network --rw-map "$HOME/.codex" -- \
          codex --dangerously-bypass-approvals-and-sandbox resume "$@"
        ;;
      resume:last)
        shift || true
        exec ai-jail --exec --display --x11 --terminal-passthrough --network --rw-map "$HOME/.codex" -- \
          codex --dangerously-bypass-approvals-and-sandbox resume --last "$@"
        ;;
      *)
        exec ai-jail --exec --display --x11 --terminal-passthrough --network --rw-map "$HOME/.codex" -- \
          codex --dangerously-bypass-approvals-and-sandbox "$@"
        ;;
    esac
    ;;
esac
