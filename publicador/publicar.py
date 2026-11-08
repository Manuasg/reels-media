"""Publica en Instagram los reels de cola/ cuya hora ya ha llegado. Lo ejecuta GitHub Actions cada 15 min.

Cada publicación es una ficha cola/<nombre>.json:
    {
      "publicar_a": "2026-11-09T10:00:00+01:00",   # con zona horaria
      "video": "rendimientos_A.mp4",               # en cola/
      "portada": "portada_rendimientos.png",       # en cola/ (opcional)
      "texto": "descripción con hashtags",
      "prueba": true,                              # reel de prueba (solo no seguidores)
      "reel": "rendimientos", "version": "A"       # para el registro y el veredicto
    }
Tras publicar: la ficha pasa a publicado/ con el id y el enlace, y el vídeo se borra de cola/
(la portada se borra cuando ya no la usa ninguna otra ficha).

    python publicador/publicar.py            # publica lo que toca
    python publicador/publicar.py --listar   # solo muestra la cola
"""
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import ig  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
COLA, PUBLICADO, ERRORES = RAIZ / "cola", RAIZ / "publicado", RAIZ / "errores"
RETRASO_MAX = timedelta(hours=6)    # si GitHub se retrasa más que esto, no se publica a deshora


def cargar():
    fichas = []
    for p in sorted(COLA.glob("*.json")):
        f = json.loads(p.read_text(encoding="utf-8"))
        f["_ruta"] = p
        f["_cuando"] = datetime.fromisoformat(f["publicar_a"])
        if f["_cuando"].tzinfo is None:
            raise SystemExit(f"{p.name}: 'publicar_a' necesita zona horaria, p. ej. +01:00")
        fichas.append(f)
    return sorted(fichas, key=lambda f: f["_cuando"])


def mover(f, destino, extra):
    destino.mkdir(exist_ok=True)
    datos = {k: v for k, v in f.items() if not k.startswith("_")} | extra
    (destino / f["_ruta"].name).write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
    f["_ruta"].unlink()


def limpiar_archivos(f):
    (COLA / f["video"]).unlink(missing_ok=True)
    portada = f.get("portada")
    if portada and not any(json.loads(p.read_text(encoding="utf-8")).get("portada") == portada
                           for p in COLA.glob("*.json")):
        (COLA / portada).unlink(missing_ok=True)


def main():
    ahora = datetime.now(timezone.utc)
    fichas = cargar()
    if "--listar" in sys.argv:
        for f in fichas:
            print(f["_cuando"].isoformat(), f["_ruta"].name, f["video"], "prueba" if f.get("prueba", True) else "normal")
        return
    pendientes = [f for f in fichas if f["_cuando"] <= ahora]
    print(f"{len(fichas)} en cola, {len(pendientes)} toca publicar ahora")
    fallos = 0
    for f in pendientes:
        nombre = f["_ruta"].name
        if ahora - f["_cuando"] > RETRASO_MAX:
            print(f"✗ {nombre}: lleva más de {RETRASO_MAX} de retraso; no se publica a deshora")
            mover(f, ERRORES, {"error": "retraso excesivo; vuelve a encolarlo con otra hora", "revisado": ahora.isoformat()})
            limpiar_archivos(f)
            fallos += 1; continue
        if not (COLA / f["video"]).exists():
            print(f"✗ {nombre}: no encuentro cola/{f['video']}")
            mover(f, ERRORES, {"error": f"falta cola/{f['video']}"}); fallos += 1; continue
        try:
            video_url = ig.REPO_RAW + "cola/" + f["video"]
            portada_url = ig.REPO_RAW + "cola/" + f["portada"] if f.get("portada") else None
            cid = ig.crear_contenedor_reel(video_url, f.get("texto", ""), portada_url, f.get("prueba", True))
            estado, detalle = ig.esperar_contenedor(cid)
            if estado != "FINISHED":
                raise ig.ErrorIG(f"Instagram no pudo procesar el vídeo: {estado} {detalle}")
            mid = ig.publicar_contenedor(cid)
            try:
                info = ig.info_media(mid)
            except ig.ErrorIG as e:   # ya está publicado: no reintentar o saldría duplicado
                print(f"! {nombre}: publicado (id {mid}) pero no pude leer el enlace: {e}")
                info = {}
            print(f"✓ {nombre}: publicado {info.get('permalink')} ({info.get('media_product_type')})")
            mover(f, PUBLICADO, {"media_id": mid, "permalink": info.get("permalink"),
                                 "publicado": info.get("timestamp"), "tipo": info.get("media_product_type")})
            limpiar_archivos(f)
        except ig.ErrorIG as e:
            print(f"✗ {nombre}: {e}")
            # se queda en cola para reintentar en la próxima vuelta, salvo que ya vaya muy tarde
            fallos += 1
    if fallos:
        sys.exit(1)   # el workflow falla y GitHub avisa por correo


if __name__ == "__main__":
    main()
