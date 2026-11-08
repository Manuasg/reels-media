# reels-media

Publicador propio de reels para @profedematesenNpasos (sustituye a Metricool para publicar). Todo funciona con GitHub Actions, sin servidor.

## Cómo se usa (para Claude, desde el portátil o desde el proyecto de la nube)
1. Con el «vale» de Manuel, encola las versiones:
   ```bash
   python publicador/encolar.py --reel rendimientos --texto descripcion.txt --portada portada_rendimientos.png \
     --hora 2026-11-09T10:00 A=rendimientos_A.mp4 \
     --hora 2026-11-09T11:00 B=rendimientos_B.mp4 \
     --hora 2026-11-09T12:00 C=rendimientos_C.mp4
   ```
   Horas en hora de Madrid. Por defecto son **reels de prueba** (solo no seguidores, `graduation_strategy: MANUAL`: Manuel decide desde la app si pasa la ganadora a todos). `--normal` para un reel normal.
2. GitHub revisa `cola/` cada 15 min y publica lo que toca (puede salir 5-20 min tarde). La ficha pasa a `publicado/` con el enlace, y el vídeo se borra.
3. Cada mañana guarda las métricas en `metricas/<reel>.json`.
4. Veredicto, solo cuando Manuel lo pida: `python publicador/metricas.py --veredicto rendimientos`.

Si algo falla, el workflow sale en rojo en **Actions** y GitHub avisa por correo. Las publicaciones fallidas por retraso (> 6 h) van a `errores/`.

## Carpetas
| | |
|---|---|
| `cola/` | vídeos, portadas y fichas pendientes |
| `publicado/` | fichas de lo publicado, con `media_id` y enlace |
| `metricas/` | métricas diarias por reel y versión |
| `errores/` | lo que no se pudo publicar |
| `publicador/` | código (solo biblioteca estándar de Python) |

## Workflows
- **Publicar reels en cola**: cada 15 min.
- **Guardar métricas de los reels**: cada día.
- **Renovar clave de Instagram**: días 1 y 15.
- **Comprobar conexión con Instagram (no publica)**: manual.

Configuración inicial: [GUIA_CONFIGURACION.md](GUIA_CONFIGURACION.md). Claves en los Secrets del repo: `IG_TOKEN`, `IG_USER_ID`, `GH_PAT`.
