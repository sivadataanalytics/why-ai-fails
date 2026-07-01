#!/bin/bash
# One-time GitHub push using a fine-grained personal access token.
# Usage (do NOT paste token into chat — run locally):
#   export GITHUB_USER="your-github-username"
#   export GITHUB_TOKEN="github_pat_..."
#   bash push-to-github.sh

set -euo pipefail

REPO_NAME="${REPO_NAME:-why-ai-fails}"
GITHUB_USER="${GITHUB_USER:?Set GITHUB_USER}"
GITHUB_TOKEN="${GITHUB_TOKEN:?Set GITHUB_TOKEN}"

echo "Creating repo ${GITHUB_USER}/${REPO_NAME} (if it does not exist)..."
curl -fsS -X POST \
  -H "Authorization: Bearer ${GITHUB_TOKEN}" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/user/repos" \
  -d "{\"name\":\"${REPO_NAME}\",\"private\":false,\"description\":\"Context pruning demo — Why AI Fails Series 2.1\"}" \
  >/dev/null 2>&1 || echo "(Repo may already exist — continuing)"

git remote remove origin 2>/dev/null || true
git remote add origin "https://github.com/${GITHUB_USER}/${REPO_NAME}.git"

echo "Pushing to GitHub..."
git push -u "https://${GITHUB_USER}:${GITHUB_TOKEN}@github.com/${GITHUB_USER}/${REPO_NAME}.git" main

git remote set-url origin "https://github.com/${GITHUB_USER}/${REPO_NAME}.git"
echo "Done: https://github.com/${GITHUB_USER}/${REPO_NAME}"
