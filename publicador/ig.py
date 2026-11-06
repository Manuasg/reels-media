"""Cliente mínimo de la API de Instagram (Instagram API with Instagram Login).

Solo usa la librería estándar. La clave se lee de la variable de entorno IG_TOKEN.
Con IG_SIMULAR=1 no se hace ninguna llamada real: se usa un simulador para las pruebas.
"""
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

GRAPH = 'https://graph.instagram.com'
VERSION = os.environ.get('IG_API_VERSION', 'v26.0')


class ErrorIG(Exception):
    pass


def _token():
    t = os.environ.get('IG_TOKEN', '').strip()
    if not t:
        raise ErrorIG('Falta el secreto IG_TOKEN.')
    return t


def _peticion(metodo, url, params=None, cuerpo=None, cabeceras=None, intentos=3):
    params = dict(params or {})
    if metodo == 'GET':
        url = url + ('&' if '?' in url else '?') + urllib.parse.urlencode(params)
        data = None
    elif cuerpo is not None:
        data = cuerpo
    else:
        data = json.dumps(params).encode()
        cabeceras = {'Content-Type': 'application/json', **(cabeceras or {})}
    req = urllib.request.Request(url, data=data, method=metodo, headers=cabeceras or {})
    for k in range(intentos):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read().decode() or '{}')
        except urllib.error.HTTPError as e:
            texto = e.read().decode(errors='replace')
            # 5xx o límite de ritmo: reintentar; 4xx: error definitivo
            if e.code >= 500 or e.code == 429:
                if k < intentos - 1:
                    time.sleep(10 * (k + 1)); continue
            raise ErrorIG(f'{metodo} {url.split("?")[0]} -> HTTP {e.code}: {_limpia(texto)}')
        except urllib.error.URLError as e:
            if k < intentos - 1:
                time.sleep(10 * (k + 1)); continue
            raise ErrorIG(f'{metodo} {url.split("?")[0]} -> {e}')


def _limpia(texto):
    """Quita cualquier rastro de la clave de los mensajes de error."""
    t = os.environ.get('IG_TOKEN', '')
    return texto.replace(t, '***') if t else texto


def get(ruta, **params):
    params['access_token'] = _token()
    return _peticion('GET', f'{GRAPH}/{VERSION}/{ruta}', params)


def post(ruta, **params):
    return _peticion('POST', f'{GRAPH}/{VERSION}/{ruta}', params,
                     cabeceras={'Authorization': f'Bearer {_token()}'})


# ---------------------------------------------------------------- funciones de alto nivel
def yo():
    return get('me', fields='user_id,username,account_type,followers_count')


def cupo(ig_id):
    """Uso del cupo de 24 h: devuelve (usadas, maximo)."""
    r = get(f'{ig_id}/content_publishing_limit', fields='quota_usage,config')
    d = (r.get('data') or [{}])[0]
    return d.get('quota_usage', 0), (d.get('config') or {}).get('quota_total', 100)


def crear_contenedor(ig_id, *, video_url=None, texto='', portada_url=None, prueba=True, resumible=False):
    p = {'media_type': 'REELS', 'caption': texto}
    if resumible:
        p['upload_type'] = 'resumable'
    else:
        p['video_url'] = video_url
    if portada_url:
        p['cover_url'] = portada_url
    if prueba:
        # Solo no seguidores; Manuel decide desde la app si lo comparte con todos.
        p['trial_params'] = {'graduation_strategy': 'MANUAL'}
    else:
        p['share_to_feed'] = True
    return post(f'{ig_id}/media', **p)


def subir_bytes(uri, ruta_video):
    with open(ruta_video, 'rb') as f:
        datos = f.read()
    return _peticion('POST', uri, cuerpo=datos, cabeceras={
        'Authorization': f'OAuth {_token()}', 'offset': '0', 'file_size': str(len(datos))})


def esperar_contenedor(cid, max_s=900, cada=15):
    """Espera a que Meta procese el vídeo. Devuelve el status_code final."""
    t0 = time.time()
    while True:
        r = get(cid, fields='status_code,status')
        sc = r.get('status_code')
        if sc in ('FINISHED', 'PUBLISHED'):
            return sc, r.get('status')
        if sc in ('ERROR', 'EXPIRED') or time.time() - t0 > max_s:
            return sc or 'TIMEOUT', r.get('status')
        time.sleep(cada)


def publicar_contenedor(ig_id, cid):
    return post(f'{ig_id}/media_publish', creation_id=cid)['id']


def ficha_media(mid):
    return get(mid, fields='id,media_type,media_product_type,permalink,timestamp,caption')


METRICAS = ['views', 'reach', 'saved', 'shares', 'likes', 'comments', 'total_interactions',
            'ig_reels_avg_watch_time', 'ig_reels_video_view_total_time', 'reels_skip_rate']


def metricas(mid):
    """Pide todas las métricas; si Meta rechaza alguna, la quita y vuelve a intentar."""
    pend = list(METRICAS); fuera = {}
    for _ in range(len(METRICAS)):
        try:
            r = get(f'{mid}/insights', metric=','.join(pend))
            out = {}
            for m in r.get('data', []):
                vals = m.get('values') or [{}]
                out[m['name']] = vals[0].get('value', m.get('total_value', {}).get('value'))
            return out, fuera
        except ErrorIG as e:
            caida = next((m for m in pend if m in str(e)), None)
            if not caida:
                raise
            pend.remove(caida); fuera[caida] = str(e)[:200]
            if not pend:
                return {}, fuera
    return {}, fuera


def renovar_token():
    r = _peticion('GET', f'{GRAPH}/refresh_access_token',
                  {'grant_type': 'ig_refresh_token', 'access_token': _token()})
    return r['access_token'], r.get('expires_in')


if os.environ.get('IG_SIMULAR') == '1':        # para las pruebas sin red
    from simulador import instalar
    instalar(globals())
