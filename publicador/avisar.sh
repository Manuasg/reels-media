#!/usr/bin/env bash
# Si hay avisos.md, abre una incidencia (o comenta en la abierta). Así llega un correo a Manuel.
set -euo pipefail
[ -s avisos.md ] || exit 0
cuerpo="$(cat avisos.md)
_${GITHUB_WORKFLOW} · [ejecución](${GITHUB_SERVER_URL}/${GITHUB_REPOSITORY}/actions/runs/${GITHUB_RUN_ID})_"
gh label create publicador --color D93F0B --description "Avisos automáticos" --force >/dev/null
abierta=$(gh issue list --label publicador --state open --json number --jq '.[0].number // empty')
if [ -z "$abierta" ]; then
  gh issue create --title "Aviso del publicador de reels" --label publicador --body "$cuerpo"
else
  # No repetir el mismo aviso cada 15 minutos
  ultimo=$(gh issue view "$abierta" --json body,comments --jq '(.comments | last | .body) // .body')
  previo="${ultimo%$'\n'_*}"
  if [ "$previo" != "$(cat avisos.md)" ]; then gh issue comment "$abierta" --body "$cuerpo"; fi
fi
