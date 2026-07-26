#!/bin/sh
# One-time setup: use repo-managed git hooks (includes notebook validation on push).
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
git config core.hooksPath .githooks
chmod +x .githooks/pre-push
echo "Installed git hooks from .githooks/ (pre-push validates notebooks before push)."
