"""Guarda las métricas de cada reel publicado (publicado/*.json) en metricas/<reel>.json. GitHub Actions, 1 vez al día.

Cada ejecución añade una «foto» con la hora, así se ve la evolución (el veredicto se da a las 48 h).
Se dejan de pedir métricas a los 14 días de publicar.

    python publicador/metricas.py             # actualiza metricas/
    python publicador/metricas.py --veredicto rendimientos   # tabla y veredicto de un reel
"""
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import ig  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
PUBLICADO, METRICAS = RAIZ / "publicado", RAIZ / "metricas"
# Se piden de una en una: si Instagram no da alguna para esta cuenta, las demás siguen.
METRICAS_IG = ["views", "reach", "saved", "shares", "likes", "comments", "total_interactions",
               "ig_reels_avg_watch_time", "ig_reels_video_view_total_time", "reels_skip_rate"]
DIAS = 14


def leer(mid):
    datos, faltan = {}, []
    for m in METRICAS_IG:
        try:
            r = ig.llamar("GET", f"{mid}/insights", metric=m)
            v = (r.get("data") or [{}])[0].get("values", [{}])[0].get("value")
            datos[m] = v
        except ig.ErrorIG:
            faltan.append(m)
    return datos, faltan


def actualizar():
    METRICAS.mkdir(exist_ok=True)
    ahora = datetime.now(timezone.utc)
    for p in sorted(PUBLICADO.glob("*.json")):
        f = json.loads(p.read_text(encoding="utf-8"))
        if not f.get("media_id") or not f.get("publicado"):
            continue
        if ahora - datetime.fromisoformat(f["publicado"].replace("+0000", "+00:00")) > timedelta(days=DIAS):
            continue
        datos, faltan = leer(f["media_id"])
        destino = METRICAS / f"{f.get('reel', p.stem)}.json"
        todo = json.loads(destino.read_text(encoding="utf-8")) if destino.exists() else {}
        v = todo.setdefault(f.get("version", p.stem), {"media_id": f["media_id"], "permalink": f.get("permalink"),
                                                         "publicado": f["publicado"], "fotos": []})
        v["fotos"].append({"hora": ahora.isoformat(timespec="minutes"), **datos})
        if faltan:
            v["no_disponibles"] = faltan
        destino.write_text(json.dumps(todo, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"{destino.name} {f.get('version')}: {datos}")


def veredicto(reel):
    todo = json.loads((METRICAS / f"{reel}.json").read_text(encoding="utf-8"))
    filas = []
    for ver, v in sorted(todo.items()):
        u = v["fotos"][-1]
        pasa3 = None if u.get("reels_skip_rate") is None else round(100 - u["reels_skip_rate"], 1)
        filas.append((ver, pasa3, u.get("views"), u.get("saved", 0) or 0, u.get("shares", 0) or 0,
                      u.get("ig_reels_avg_watch_time"), u["hora"]))
    print("versión | % pasa 3 s | vistas | guardados | compartidos | tiempo medio (ms) | medido")
    for f in filas:
        print(" | ".join(str(x) for x in f))
    con3 = [f for f in filas if f[1] is not None]
    if any((f[2] or 0) <= 100 for f in filas):
        print("Aviso: alguna versión tiene unas 100 vistas o menos: el resultado no es fiable.")
    if len(con3) == len(filas) and len(filas) > 1:
        orden = sorted(con3, key=lambda f: f[1], reverse=True)
        if orden[0][1] - orden[1][1] >= 5:
            print(f"Gana {orden[0][0]} por % que pasa de 3 s ({orden[0][1]} frente a {orden[1][1]}).")
            return
    print("Empate o sin % de 3 s: deciden guardados + compartidos:",
          max(filas, key=lambda f: (f[3] + f[4], f[2] or 0))[0])


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--veredicto":
        veredicto(sys.argv[2])
    else:
        actualizar()
