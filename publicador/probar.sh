#!/usr/bin/env bash
# Prueba completa con la API simulada, en una copia temporal del repo. Uso: publicador/probar.sh
set -euo pipefail
src="$(cd "$(dirname "$0")/.." && pwd)"
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
cp -r "$src/publicador" "$tmp/"; mkdir -p "$tmp/cola" "$tmp/registro" "$tmp/metricas"
cd "$tmp"; git init -q; git commit -q --allow-empty -m init
export IG_SIMULAR=1 GITHUB_SHA=abc123 PYTHONDONTWRITEBYTECODE=1
ok() { echo "  OK  $1"; }; mal() { echo "  MAL $1"; exit 1; }

ffmpeg -loglevel error -f lavfi -i color=c=0xF2EBDD:s=1080x1920:d=4 -f lavfi -i anullsrc -shortest \
  -c:v libx264 -preset veryfast -pix_fmt yuv420p -c:a aac cola/idea3_A.mp4
cp cola/idea3_A.mp4 cola/idea3_B.mp4; cp cola/idea3_A.mp4 cola/idea3_C.mp4
printf 'png' > cola/portada_idea3.png
for v in A:08:30 B:09:30 C:10:30; do
  ver=${v%%:*}; h=${v#*:}
  cat > "cola/2026-11-09_${h/:/}_idea3_$ver.json" <<EOF
{"hora": "2026-11-09T$h", "video": "idea3_$ver.mp4", "portada": "portada_idea3.png",
 "texto": "f = 1 + ∫f #matematicas", "prueba": true, "idea": "idea3", "version": "$ver"}
EOF
done
echo '{"hora": "mañana", "texto": ""}' > cola/rota.json

echo "1. Validar"
python publicador/publicar.py validar | tee out.txt >/dev/null
grep -q 'rota.json.*hora no válida' out.txt && ok "detecta ficha rota" || mal "no detecta ficha rota"
rm cola/rota.json avisos.md

echo "2. Antes de la hora no publica nada"
AHORA=2026-11-09T08:00 python publicador/publicar.py | grep -q 'Nada que publicar' && ok "espera" || mal "publica antes de hora"

echo "3. A las 09:40 publica A y B; C sigue en cola"
AHORA=2026-11-09T09:40 python publicador/publicar.py > out.txt
[ "$(wc -l < registro/publicados.jsonl)" = 2 ] && ok "2 publicadas" || mal "$(cat out.txt)"
[ -f cola/idea3_C.mp4 ] && [ ! -f cola/idea3_A.mp4 ] && [ -f cola/portada_idea3.png ] && ok "borra A y B, deja C y la portada" || mal "limpieza"
grep -q '"prueba": true' registro/fichas/*idea3_A.json && ok "ficha archivada" || mal "ficha"

echo "4. Comprueba que se pide como reel de prueba"
python - <<'EOF'
import os, sys; sys.path.insert(0, 'publicador'); os.environ['IG_SIMULAR'] = '1'
import ig
c = ig.crear_contenedor('999', video_url='u', texto='t', prueba=True)
p = ig.LLAMADAS[-1][2]
assert p['trial_params'] == {'graduation_strategy': 'MANUAL'} and 'share_to_feed' not in p, p
ig.crear_contenedor('999', video_url='u', texto='t', prueba=False)
assert 'trial_params' not in ig.LLAMADAS[-1][2]
print('  OK  trial_params MANUAL solo en las de prueba')
EOF

echo "5. Si Meta rechaza la URL, sube los bytes directamente"
IG_SIM_FALLO=url AHORA=2026-11-09T10:35 python publicador/publicar.py > out.txt
grep -q 'pruebo la subida directa' out.txt && [ "$(wc -l < registro/publicados.jsonl)" = 3 ] && ok "plan B" || mal "$(cat out.txt)"
[ -z "$(ls cola)" ] && ok "cola vacía, portada borrada" || mal "quedan: $(ls cola)"

echo "6. Retraso de más de 3 h: no publica y avisa"
ffmpeg -loglevel error -f lavfi -i color=c=white:s=1080x1920:d=4 -c:v libx264 -preset veryfast -pix_fmt yuv420p cola/x.mp4
echo '{"hora": "2026-11-10T08:30", "video": "x.mp4", "texto": "t", "idea": "x", "version": "A"}' > cola/x.json
AHORA=2026-11-10T12:00 python publicador/publicar.py >/dev/null
grep -q 'más de 3 h' avisos.md && [ -f cola/x.json ] && ok "avisa y la deja en cola" || mal "retraso"
rm -f cola/x.* avisos.md

echo "7. Métricas"
python publicador/metricas.py >/dev/null
grep -q 'idea3,A,True' metricas/resumen.csv && grep -q ',43.5,' metricas/resumen.csv && ok "resumen con pasa_3s = 100 − 56,5" || mal "$(cat metricas/resumen.csv)"
IG_SIM_SIN_SKIP=1 python publicador/metricas.py >/dev/null
grep -A1 no_disponibles metricas/M1000.json | grep -q reels_skip_rate && ok "si falta una métrica, sigue con las demás" || mal "métrica caída"
echo "Todo bien."
