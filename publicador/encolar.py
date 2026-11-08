"""Pone en cola las versiones de un reel para que GitHub las publique a su hora. Lo usa Claude con el «vale» de Manuel.

    python publicador/encolar.py --reel rendimientos --texto descripcion.txt --portada portada.png \
        --hora 2026-11-09T10:00 A=ruta/rendimientos_A.mp4 \
        --hora 2026-11-09T11:00 B=ruta/rendimientos_B.mp4 \
        --hora 2026-11-09T12:00 C=ruta/rendimientos_C.mp4

Cada --hora va delante de la versión a la que se aplica (hora de Madrid). Copia vídeos y portada a cola/,
escribe las fichas, y hace commit + push. Añade --normal para publicar como reel normal (no de prueba),
y --sin-push para dejarlo solo en local.
"""
import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

RAIZ = Path(__file__).resolve().parent.parent
COLA = RAIZ / "cola"
MADRID = ZoneInfo("Europe/Madrid")

ap = argparse.ArgumentParser()
ap.add_argument("--reel", required=True)
ap.add_argument("--texto", required=True, help="archivo con la descripción")
ap.add_argument("--portada")
ap.add_argument("--normal", action="store_true")
ap.add_argument("--sin-push", action="store_true")
args, resto = ap.parse_known_args()

# pares (hora, VERSION=ruta) en el orden en que vienen
pares, hora = [], None
for a in resto:
    if a == "--hora":
        hora = "pendiente"; continue
    if hora == "pendiente":
        hora = datetime.fromisoformat(a).replace(tzinfo=MADRID); continue
    if "=" in a and hora:
        v, ruta = a.split("=", 1); pares.append((hora, v.upper(), Path(ruta))); continue
    sys.exit(f"No entiendo «{a}». Usa: --hora AAAA-MM-DDTHH:MM VERSION=video.mp4")
if not pares:
    sys.exit("No hay ninguna versión que encolar.")

texto = Path(args.texto).read_text(encoding="utf-8").strip()
hashtags = [w for w in texto.split() if w.startswith("#")]
if len(hashtags) != 5:
    print(f"Aviso: la descripción tiene {len(hashtags)} hashtags (lo habitual son 5).")
COLA.mkdir(exist_ok=True)
nuevos = []
portada = None
if args.portada:
    portada = Path(args.portada).name
    shutil.copy2(args.portada, COLA / portada); nuevos.append(COLA / portada)
for cuando, v, ruta in pares:
    if not ruta.exists():
        sys.exit(f"No existe {ruta}")
    if cuando < datetime.now(MADRID):
        sys.exit(f"La hora de {v} ({cuando:%d/%m %H:%M}) ya ha pasado.")
    shutil.copy2(ruta, COLA / ruta.name)
    ficha = {"publicar_a": cuando.isoformat(), "video": ruta.name, "portada": portada, "texto": texto,
             "prueba": not args.normal, "reel": args.reel, "version": v}
    destino = COLA / f"{cuando:%Y%m%d_%H%M}_{args.reel}_{v}.json"
    destino.write_text(json.dumps(ficha, ensure_ascii=False, indent=2), encoding="utf-8")
    nuevos += [COLA / ruta.name, destino]
    print(f"En cola: {v} el {cuando:%d/%m a las %H:%M} ({'reel de prueba' if not args.normal else 'reel normal'})")

if not args.sin_push:
    g = ["git", "-c", "user.name=Claude", "-c", "user.email=noreply@anthropic.com"]
    subprocess.run(g + ["pull", "-q", "--rebase"], cwd=RAIZ, check=True)
    subprocess.run(g + ["add", *[str(p.relative_to(RAIZ)) for p in nuevos]], cwd=RAIZ, check=True)
    subprocess.run(g + ["commit", "-q", "-m", f"Cola: reel {args.reel} ({', '.join(v for _, v, _ in pares)})"],
                   cwd=RAIZ, check=True)
    subprocess.run(g + ["push", "-q"], cwd=RAIZ, check=True)
    print("Subido. GitHub lo publicará a su hora (puede tardar 5-20 min más).")
