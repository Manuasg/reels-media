"""Publica las fichas de cola/ cuya hora ya ha llegado.

Uso:
  python publicador/publicar.py            publica lo que toca
  python publicador/publicar.py validar    solo revisa las fichas (no publica nada)

Ficha (cola/<nombre>.json):
  {"hora": "2026-11-09T08:30", "video": "idea3_A.mp4", "portada": "portada_idea3.png",
   "texto": "descripción con hashtags", "prueba": true, "idea": "idea3", "version": "A"}
  - hora: hora de Madrid. "video" y "portada" son archivos de cola/. "portada" es opcional.
  - prueba: true = reel de prueba (solo no seguidores, se comparte a mano desde la app).

Lo que pasa al publicar: la ficha se mueve a registro/fichas/, se apunta una línea en
registro/publicados.jsonl y se borran de cola/ el vídeo y la portada (si ya no los usa
otra ficha). Los avisos se escriben en avisos.md: el workflow abre una incidencia con ellos.
"""
import datetime as dt
import json
import os
import subprocess
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).parent))
import ig  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
COLA, REG = RAIZ / 'cola', RAIZ / 'registro'
MADRID = ZoneInfo('Europe/Madrid')
RETRASO_MAX = dt.timedelta(hours=3)     # si GitHub se retrasa más, no se publica y se avisa
MAX_INTENTOS = 3
avisos = []


def ahora():
    fijo = os.environ.get('AHORA')          # para las pruebas
    return dt.datetime.fromisoformat(fijo).replace(tzinfo=MADRID) if fijo else dt.datetime.now(MADRID)


def leer_fichas():
    fichas = []
    for p in sorted(COLA.glob('*.json')):
        try:
            f = json.loads(p.read_text())
        except json.JSONDecodeError as e:
            avisos.append(f'`{p.name}`: no es un JSON válido ({e}).'); continue
        fichas.append((p, f))
    return fichas


def duracion(video):
    try:
        out = subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                                       '-of', 'csv=p=0', str(video)], text=True)
        return float(out)
    except (OSError, subprocess.CalledProcessError, ValueError):
        return None


def validar(p, f):
    errores = []
    for campo in ('hora', 'video', 'texto'):
        if not f.get(campo):
            errores.append(f'falta «{campo}»')
    try:
        dt.datetime.fromisoformat(f.get('hora', ''))
    except ValueError:
        errores.append(f'hora no válida: {f.get("hora")!r} (formato 2026-11-09T08:30)')
    v = COLA / f.get('video', '-')
    if f.get('video') and not v.exists():
        errores.append(f'no está el vídeo cola/{f["video"]}')
    elif v.exists():
        mb = v.stat().st_size / 2**20
        if mb > 300:
            errores.append(f'el vídeo pesa {mb:.0f} MB (máximo 300)')
        d = duracion(v)
        if d is not None and not 3 <= d <= 90:
            errores.append(f'el vídeo dura {d:.1f} s (debe estar entre 3 y 90)')
    if f.get('portada') and not (COLA / f['portada']).exists():
        errores.append(f'no está la portada cola/{f["portada"]}')
    if len(f.get('texto', '')) > 2200:
        errores.append('la descripción pasa de 2.200 caracteres')
    if f.get('texto', '').count('#') > 30:
        errores.append('más de 30 hashtags')
    return errores


def url_publica(nombre):
    repo = os.environ.get('GITHUB_REPOSITORY', 'Manuasg/reels-media')
    sha = os.environ.get('GITHUB_SHA') or subprocess.check_output(
        ['git', '-C', str(RAIZ), 'rev-parse', 'HEAD'], text=True).strip()
    return f'https://raw.githubusercontent.com/{repo}/{sha}/cola/{nombre}'


def publicar_una(ig_id, p, f):
    portada = url_publica(f['portada']) if f.get('portada') else None
    prueba = f.get('prueba', True)
    # 1.º intento: Meta descarga el vídeo de la URL pública del repo.
    c = ig.crear_contenedor(ig_id, video_url=url_publica(f['video']), texto=f['texto'],
                            portada_url=portada, prueba=prueba)
    estado, detalle = ig.esperar_contenedor(c['id'])
    if estado not in ('FINISHED', 'PUBLISHED'):
        # 2.º intento: subida directa de los bytes (subida reanudable).
        print(f'  URL rechazada ({estado}: {detalle}); pruebo la subida directa')
        c = ig.crear_contenedor(ig_id, texto=f['texto'], portada_url=portada, prueba=prueba, resumible=True)
        ig.subir_bytes(c['uri'], COLA / f['video'])
        estado, detalle = ig.esperar_contenedor(c['id'])
        if estado not in ('FINISHED', 'PUBLISHED'):
            raise ig.ErrorIG(f'Meta no ha procesado el vídeo: {estado} ({detalle})')
    mid = ig.publicar_contenedor(ig_id, c['id'])
    m = ig.ficha_media(mid)
    if m.get('media_product_type') != 'REELS':
        avisos.append(f'`{p.name}` se ha publicado como {m.get("media_product_type")}, no como reel: {m.get("permalink")}')
    return m


def archivar(p, f, m, t):
    (REG / 'fichas').mkdir(parents=True, exist_ok=True)
    linea = {'media_id': m['id'], 'permalink': m.get('permalink'), 'idea': f.get('idea'),
             'version': f.get('version'), 'prueba': f.get('prueba', True), 'hora_prevista': f['hora'],
             'hora_real': t.isoformat(timespec='minutes'), 'ficha': p.name}
    with open(REG / 'publicados.jsonl', 'a') as h:
        h.write(json.dumps(linea, ensure_ascii=False) + '\n')
    f['media_id'] = m['id']; f['permalink'] = m.get('permalink')
    (REG / 'fichas' / p.name).write_text(json.dumps(f, ensure_ascii=False, indent=2) + '\n')
    p.unlink()


def limpiar_archivos():
    """Borra de cola/ los vídeos y portadas que ya no usa ninguna ficha pendiente."""
    usados = set()
    for _, f in leer_fichas():
        usados.update(x for x in (f.get('video'), f.get('portada')) if x)
    for a in COLA.iterdir():
        if a.suffix.lower() in ('.mp4', '.mov', '.png', '.jpg', '.jpeg') and a.name not in usados:
            a.unlink(); print(f'  borrado cola/{a.name}')


def main():
    modo = sys.argv[1] if len(sys.argv) > 1 else 'publicar'
    COLA.mkdir(exist_ok=True)
    fichas = leer_fichas()
    for p, f in fichas:
        for e in validar(p, f):
            avisos.append(f'`{p.name}`: {e}.')
    if modo == 'validar':
        print('\n'.join(avisos) or f'{len(fichas)} fichas, todo bien.')
        return terminar()

    t = ahora()
    toca = [(p, f) for p, f in fichas if not validar(p, f) and dt.datetime.fromisoformat(f['hora']).replace(tzinfo=MADRID) <= t]
    if not toca:
        print('Nada que publicar.'); return terminar()

    ig_id = ig.yo()['user_id']
    usadas, maximo = ig.cupo(ig_id)
    print(f'Cupo de 24 h: {usadas}/{maximo}')
    for p, f in sorted(toca, key=lambda x: x[1]['hora']):
        prevista = dt.datetime.fromisoformat(f['hora']).replace(tzinfo=MADRID)
        if t - prevista > RETRASO_MAX:
            avisos.append(f'`{p.name}` no se ha publicado: tocaba a las {f["hora"]} y ya han pasado más de 3 h. '
                          'Sigue en cola/; cámbiale la hora o bórrala.')
            continue
        if usadas >= maximo:
            avisos.append(f'`{p.name}` espera: cupo de 24 h agotado ({usadas}/{maximo}).'); break
        print(f'Publicando {p.name} ({f.get("idea")} {f.get("version")}, prevista {f["hora"]})')
        try:
            m = publicar_una(ig_id, p, f)
        except ig.ErrorIG as e:
            f['intentos'] = f.get('intentos', 0) + 1
            if f['intentos'] >= MAX_INTENTOS:
                avisos.append(f'`{p.name}` ha fallado {MAX_INTENTOS} veces y se ha apartado a registro/fallidas/: {e}')
                (REG / 'fallidas').mkdir(parents=True, exist_ok=True)
                (REG / 'fallidas' / p.name).write_text(json.dumps(f, ensure_ascii=False, indent=2) + '\n'); p.unlink()
            else:
                print(f'  fallo {f["intentos"]}/{MAX_INTENTOS}: {e}')
                p.write_text(json.dumps(f, ensure_ascii=False, indent=2) + '\n')
            continue
        usadas += 1
        print(f'  publicado: {m.get("permalink")}')
        archivar(p, f, m, t)
    limpiar_archivos()
    return terminar()


def terminar():
    if avisos:
        (RAIZ / 'avisos.md').write_text('\n'.join(f'- {a}' for a in avisos) + '\n')
        print('AVISOS:\n' + '\n'.join(avisos))
    return 0


if __name__ == '__main__':
    sys.exit(main())
