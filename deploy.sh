#!/usr/bin/env bash
# deploy.sh
# Deploys all MCP files to Ableton and syncs server files to all active Claude Code worktrees.
# macOS/Linux counterpart to deploy.ps1.
#
# Run this after making any changes to:
#   - AbletonMCPLocal/*.py  (remote script - requires Ableton restart after)
#   - ableton/*.py          (MCP server files)
#   - server_arrangement.py (MCP server entry point)
#
# Usage: ./deploy.sh
#        ./deploy.sh --skip-ableton     (skip Ableton deploy, only sync worktrees)
#        ./deploy.sh --skip-worktrees   (skip worktree sync, only deploy to Ableton)

set -euo pipefail

SKIP_ABLETON=0
SKIP_WORKTREES=0

for arg in "$@"; do
    case "$arg" in
        --skip-ableton)   SKIP_ABLETON=1 ;;
        --skip-worktrees) SKIP_WORKTREES=1 ;;
        -h|--help)
            sed -n '2,14p' "$0" | sed 's/^# \{0,1\}//'
            exit 0 ;;
        *)
            echo "Unknown option: $arg" >&2
            echo "Usage: ./deploy.sh [--skip-ableton] [--skip-worktrees]" >&2
            exit 1 ;;
    esac
done

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ABLETON_DEPLOY="$HOME/Music/Ableton/User Library/Remote Scripts/AbletonMCPLocal"

CYAN=$'\033[36m'; GREEN=$'\033[32m'; YELLOW=$'\033[33m'; RESET=$'\033[0m'

# -- 1. Deploy remote script to Ableton --------------------------------------
if [ "$SKIP_ABLETON" -eq 0 ]; then
    printf '\n%s[1/2] Deploying remote script to Ableton...%s\n' "$CYAN" "$RESET"

    # Ableton only creates "Remote Scripts" on demand, so make the path if absent.
    if [ ! -d "$ABLETON_DEPLOY" ]; then
        mkdir -p "$ABLETON_DEPLOY"
        echo "  Created $ABLETON_DEPLOY"
    fi

    if [ -d "$ABLETON_DEPLOY/__pycache__" ]; then
        rm -rf "$ABLETON_DEPLOY/__pycache__"
        echo "  Deleted __pycache__"
    fi

    for f in "$PROJECT_ROOT"/AbletonMCPLocal/*.py; do
        cp -f "$f" "$ABLETON_DEPLOY/"
        echo "  Copied $(basename "$f")"
    done

    printf '  %sRemote script deployed. Restart Ableton to pick up changes.%s\n' "$GREEN" "$RESET"
fi

# -- 2. Sync server files to all active worktrees ----------------------------
if [ "$SKIP_WORKTREES" -eq 0 ]; then
    printf '\n%s[2/2] Syncing server files to Claude Code worktrees...%s\n' "$CYAN" "$RESET"

    WORKTREES_DIR="$PROJECT_ROOT/.claude/worktrees"
    if [ ! -d "$WORKTREES_DIR" ]; then
        printf '  %sNo worktrees directory found - nothing to sync.%s\n' "$YELLOW" "$RESET"
    else
        found=0
        for wt in "$WORKTREES_DIR"/*/; do
            [ -d "$wt" ] || continue
            found=1
            wt="${wt%/}"
            echo "  Worktree: $(basename "$wt")"

            # Sync ableton/ package files
            if [ -d "$wt/ableton" ]; then
                for f in "$PROJECT_ROOT"/ableton/*.py; do
                    cp -f "$f" "$wt/ableton/"
                    echo "    ableton/$(basename "$f")"
                done
            fi

            # Sync server entry point
            if [ -f "$wt/server_arrangement.py" ]; then
                cp -f "$PROJECT_ROOT/server_arrangement.py" "$wt/"
                echo "    server_arrangement.py"
            fi
        done

        if [ "$found" -eq 0 ]; then
            printf '  %sNo active worktrees found.%s\n' "$YELLOW" "$RESET"
        else
            printf '  %sWorktrees synced.%s\n' "$GREEN" "$RESET"
        fi
    fi
fi

printf '\n%sDone.%s\n\n' "$GREEN" "$RESET"
