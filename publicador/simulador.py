"""Simulador de la API para las pruebas (IG_SIMULAR=1). No hace ninguna llamada de red.
IG_SIM_FALLO=url hace que Meta rechace la URL del vídeo, para probar la subida directa."""
import itertools
import os

_ids = itertools.count(1000)
LLAMADAS = []


def instalar(g):
    E = g['ErrorIG']
    os.environ.setdefault('IG_TOKEN', 'token-falso')

    def get(ruta, **p):
        LLAMADAS.append(('GET', ruta, p))
        if ruta == 'me':
            return {'user_id': '999', 'username': 'profedematesennpasos'}
        if ruta.endswith('content_publishing_limit'):
            return {'data': [{'quota_usage': 2, 'config': {'quota_total': 100}}]}
        if ruta.endswith('/insights'):
            if 'reels_skip_rate' in p['metric'] and os.environ.get('IG_SIM_SIN_SKIP'):
                raise E('HTTP 400: (#100) metric[9] must be one of ... reels_skip_rate not supported')
            vals = {'views': 812, 'reach': 640, 'saved': 9, 'shares': 3, 'likes': 21, 'comments': 2,
                    'total_interactions': 35, 'ig_reels_avg_watch_time': 9800,
                    'ig_reels_video_view_total_time': 7900000, 'reels_skip_rate': 56.5}
            return {'data': [{'name': m, 'values': [{'value': vals[m]}]} for m in p['metric'].split(',')]}
        if p.get('fields') == 'status_code,status':
            mal = ruta in _rechazados
            return {'status_code': 'ERROR' if mal else 'FINISHED', 'status': 'Error: 2207026' if mal else ''}
        return {'id': ruta, 'media_product_type': 'REELS', 'permalink': f'https://www.instagram.com/reel/{ruta}/'}

    _rechazados = set()

    def post(ruta, **p):
        LLAMADAS.append(('POST', ruta, p))
        if ruta.endswith('/media'):
            assert p['media_type'] == 'REELS'
            cid = str(next(_ids))
            if 'video_url' in p and os.environ.get('IG_SIM_FALLO') == 'url':
                _rechazados.add(cid)
            r = {'id': cid}
            if p.get('upload_type') == 'resumable':
                r['uri'] = f'https://rupload.facebook.com/ig-api-upload/v26.0/{cid}'
            return r
        if ruta.endswith('/media_publish'):
            return {'id': 'M' + p['creation_id']}
        raise E(f'ruta no simulada: {ruta}')

    def subir_bytes(uri, ruta_video):
        LLAMADAS.append(('UPLOAD', uri, os.path.getsize(ruta_video)))
        return {'success': True}

    g.update(get=get, post=post, subir_bytes=subir_bytes, LLAMADAS=LLAMADAS)
    g['esperar_contenedor'].__globals__['time'].sleep = lambda s: None
