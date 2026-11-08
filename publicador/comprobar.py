"""Comprueba la conexión con Instagram sin publicar nada.

    python publicador/comprobar.py                    # cuenta, tipo, seguidores y cupo de la API
    python publicador/comprobar.py --contenedor URL   # además, crea un contenedor de reel de PRUEBA con ese
                                                      # vídeo y espera a que Instagram lo procese, pero NO lo publica
                                                      # (el contenedor caduca solo a las 24 h)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import ig  # noqa: E402

yo = ig.llamar("GET", ig.user_id(), fields="username,followers_count,media_count")
print(f"Cuenta: @{yo.get('username')}  seguidores: {yo.get('followers_count')}  publicaciones: {yo.get('media_count')}")
if (yo.get("followers_count") or 0) < 1000:
    print("Ojo: los reels de prueba piden al menos 1.000 seguidores.")
usado, total = ig.cupo()
print(f"Cupo de la API en las últimas 24 h: {usado} de {total}")

if len(sys.argv) > 2 and sys.argv[1] == "--contenedor":
    cid = ig.crear_contenedor_reel(sys.argv[2], "Prueba técnica: no se publica", prueba=True)
    print("Contenedor de reel de prueba creado (Instagram aceptó trial_params):", cid)
    estado, detalle = ig.esperar_contenedor(cid)
    print("Estado tras procesar el vídeo:", estado, detalle)
    print("No se ha publicado nada.")
