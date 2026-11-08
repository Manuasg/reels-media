"""Llamadas mínimas a la API de Instagram (Instagram API with Instagram Login). Solo biblioteca estándar.

Necesita las variables de entorno IG_TOKEN e IG_USER_ID (en GitHub Actions vienen de los Secrets del repo).
"""
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://graph.instagram.com/v23.0"
REPO_RAW = "https://raw.githubusercontent.com/Manuasg/reels-media/main/"


class ErrorIG(Exception):
    pass


def _token():
    t = os.environ.get("IG_TOKEN", "").strip()
    if not t:
        raise ErrorIG("Falta IG_TOKEN (secreto del repo).")
    return t


def user_id():
    u = os.environ.get("IG_USER_ID", "").strip()
    if not u:
        raise ErrorIG("Falta IG_USER_ID (secreto del repo).")
    return u


def llamar(metodo, ruta, base=API, **params):
    params["access_token"] = _token()
    datos = urllib.parse.urlencode({k: (json.dumps(v) if isinstance(v, (dict, list)) else v)
                                    for k, v in params.items() if v is not None})
    url = f"{base}/{ruta.lstrip('/')}"
    if metodo == "GET":
        req = urllib.request.Request(f"{url}?{datos}")
    else:
        req = urllib.request.Request(url, data=datos.encode(), method=metodo)
    for intento in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            cuerpo = e.read().decode(errors="replace")
            if e.code >= 500 and intento < 2:
                time.sleep(5 * (intento + 1)); continue
            # nunca imprimir la URL: lleva el token
            raise ErrorIG(f"{metodo} {ruta} -> HTTP {e.code}: {cuerpo}") from None
        except urllib.error.URLError as e:
            if intento < 2:
                time.sleep(5 * (intento + 1)); continue
            raise ErrorIG(f"{metodo} {ruta} -> sin conexión: {e.reason}") from None


def crear_contenedor_reel(video_url, texto, portada_url=None, prueba=True):
    params = dict(media_type="REELS", video_url=video_url, caption=texto, share_to_feed="true", cover_url=portada_url)
    if prueba:
        # Reel de prueba: solo lo ven no seguidores; Manuel decide desde la app si lo pasa a todos.
        params["trial_params"] = {"graduation_strategy": "MANUAL"}
    return llamar("POST", f"{user_id()}/media", **params)["id"]


def esperar_contenedor(cid, max_s=900):
    """Espera a que Instagram procese el vídeo. Devuelve el estado final."""
    t0 = time.time()
    while True:
        r = llamar("GET", cid, fields="status_code,status")
        estado = r.get("status_code")
        if estado in ("FINISHED", "ERROR", "EXPIRED", "PUBLISHED"):
            return estado, r.get("status", "")
        if time.time() - t0 > max_s:
            return "TIMEOUT", r.get("status", "")
        time.sleep(15)


def publicar_contenedor(cid):
    return llamar("POST", f"{user_id()}/media_publish", creation_id=cid)["id"]


def info_media(mid):
    return llamar("GET", mid, fields="id,permalink,media_type,media_product_type,timestamp,caption")


def cupo():
    r = llamar("GET", f"{user_id()}/content_publishing_limit", fields="config,quota_usage")
    d = (r.get("data") or [{}])[0]
    return d.get("quota_usage"), (d.get("config") or {}).get("quota_total")
