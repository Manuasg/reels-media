"""Guarda las métricas de los reels publicados en los últimos DIAS días.

- metricas/<media_id>.json: una foto por ejecución (fecha, horas desde la publicación, métricas).
- metricas/resumen.csv: la última foto de cada reel, para leerla de un vistazo.

pasa_3s = 100 − reels_skip_rate: es el equivalente del «% que pasa de 3 s» (IGRE28) de Metricool.
Meta marca reels_skip_rate como métrica estimada y en desarrollo.
"""
import csv
import datetime as dt
import json
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).parent))
import ig  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
REG, MET = RAIZ / 'registro', RAIZ / 'metricas'
MADRID = ZoneInfo('Europe/Madrid')
DIAS = 14
COLUMNAS = ['media_id', 'idea', 'version', 'prueba', 'hora_real', 'horas', 'views', 'reach', 'pasa_3s',
            'reels_skip_rate', 'avg_watch_s', 'saved', 'shares', 'likes', 'comments', 'permalink']


def pasa_3s(skip):
    if skip is None:
        return None
    s = float(skip)
    s = s * 100 if s <= 1 else s          # por si Meta lo da en tanto por uno
    return round(100 - s, 1)


def main():
    MET.mkdir(exist_ok=True)
    pub = REG / 'publicados.jsonl'
    if not pub.exists():
        print('Todavía no hay nada publicado.'); return 0
    ahora = dt.datetime.now(MADRID)
    avisos, filas = [], []
    for linea in pub.read_text().splitlines():
        if not linea.strip():
            continue
        r = json.loads(linea)
        t = dt.datetime.fromisoformat(r['hora_real'])
        t = t if t.tzinfo else t.replace(tzinfo=MADRID)
        horas = round((ahora - t).total_seconds() / 3600, 1)
        archivo = MET / f'{r["media_id"]}.json'
        hist = json.loads(archivo.read_text()) if archivo.exists() else {'reel': r, 'fotos': []}
        if horas <= DIAS * 24:
            try:
                m, fuera = ig.metricas(r['media_id'])
            except ig.ErrorIG as e:
                avisos.append(f'Métricas de {r["media_id"]} ({r.get("idea")} {r.get("version")}): {e}')
                m, fuera = None, {}
            if m is not None:
                hist['fotos'].append({'fecha': ahora.isoformat(timespec='minutes'), 'horas': horas, **m})
                if fuera:
                    hist['no_disponibles'] = sorted(fuera)
                archivo.write_text(json.dumps(hist, ensure_ascii=False, indent=1) + '\n')
        if hist['fotos']:
            u = hist['fotos'][-1]
            w = u.get('ig_reels_avg_watch_time')
            filas.append({**{k: r.get(k) for k in ('media_id', 'idea', 'version', 'prueba', 'hora_real', 'permalink')},
                          'horas': u['horas'], 'views': u.get('views'), 'reach': u.get('reach'),
                          'reels_skip_rate': u.get('reels_skip_rate'), 'pasa_3s': pasa_3s(u.get('reels_skip_rate')),
                          'avg_watch_s': round(w / 1000, 1) if isinstance(w, (int, float)) else None,
                          **{k: u.get(k) for k in ('saved', 'shares', 'likes', 'comments')}})
    with open(MET / 'resumen.csv', 'w', newline='') as h:
        w = csv.DictWriter(h, COLUMNAS); w.writeheader(); w.writerows(filas)
    print(f'{len(filas)} reels en el resumen.')
    if avisos:
        (RAIZ / 'avisos.md').write_text('\n'.join(f'- {a}' for a in avisos) + '\n'); print('\n'.join(avisos))
    return 0


if __name__ == '__main__':
    sys.exit(main())
