#!/usr/bin/env bash
# Commitea y sube los cambios del workflow. Reintenta si otro workflow ha subido antes.
set -euo pipefail
msg="$1"
git config user.name "github-actions[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
git add -A cola registro metricas
if git diff --cached --quiet; then echo "Sin cambios."; exit 0; fi
git commit -q -m "$msg"
for i in 1 2 3; do
  git pull -q --rebase origin main && git push -q origin HEAD:main && exit 0
  sleep $((i * 10))
done
echo "No he podido subir los cambios." >&2; exit 1
