# reels-media

Publicador automático de reels de @profedematesenNpasos con la API de Instagram y GitHub Actions. Sin servidor y sin coste.

## Cómo funciona

| Workflow | Cuándo | Qué hace |
|---|---|---|
| `publicar.yml` | cada 15 min y al subir algo a `cola/` | Publica las fichas de `cola/` cuya hora ha llegado, las archiva en `registro/` y borra el vídeo. |
| `metricas.yml` | cada 6 h | Guarda las métricas de los reels de los últimos 14 días en `metricas/` (`resumen.csv` para verlas de un vistazo). |
| `renovar-token.yml` | días 1 y 15 | Renueva la clave de Instagram, que caduca a los 60 días. |

Si algo falla, se abre una **incidencia** (issue) con la etiqueta `publicador` y GitHub te manda un correo.

### Ficha de la cola

Un vídeo y una ficha por publicación, los dos en `cola/`:

```json
{"hora": "2026-11-09T08:30", "video": "idea3_A.mp4", "portada": "portada_idea3.png",
 "texto": "Descripción con #hashtags", "prueba": true, "idea": "idea3", "version": "A"}
```

- `hora` es hora de Madrid. GitHub puede publicar entre 5 y 20 min tarde; con más de 3 h de retraso no publica y avisa.
- `prueba: true` publica un **reel de prueba** (`trial_params.graduation_strategy = MANUAL`): solo lo ven quienes no te siguen y tú decides desde la app si lo compartes con todos.
- `portada` es opcional. Varias fichas pueden usar la misma; se borra cuando ya no la usa ninguna.

En las métricas, `pasa_3s = 100 − reels_skip_rate` es el equivalente del «% que pasa de 3 s» de Metricool.

## Configuración (una sola vez, unos 20-30 min)

### 1. App de Meta y clave de Instagram
1. Entra en [developers.facebook.com/apps](https://developers.facebook.com/apps) con tu cuenta de Facebook y pulsa **Crear app**.
2. Caso de uso: **Gestionar mensajes y contenido en Instagram**. Nombre: por ejemplo «Publicador reels». Si pregunta por un portfolio empresarial, puedes no elegir ninguno.
3. En la app, ve a **Instagram → Configuración de la API con inicio de sesión de Instagram**.
4. En el paso **1. Generar identificadores de acceso**, pulsa **Añadir cuenta**, entra con @profedematesenNpasos y acepta todos los permisos (publicar contenido y ver estadísticas).
   - Si pide aceptar una invitación de evaluador: en la app de Instagram, **Configuración → Apps y sitios web → Invitaciones de evaluador**, acéptala y vuelve a pulsar Añadir cuenta.
5. Pulsa **Generar identificador** junto a la cuenta y copia la clave (empieza por `IG…`). No la pegues en ningún chat.

La app se queda en modo desarrollo: no hace falta revisión de Meta porque solo publica en tu propia cuenta.

### 2. Secretos del repo
En este repo: **Settings → Secrets and variables → Actions → New repository secret**.

| Nombre | Valor |
|---|---|
| `IG_TOKEN` | la clave de Instagram del paso 1 |
| `GH_PAT` | un token de GitHub para que el repo pueda renovar `IG_TOKEN` (ver abajo) |

Para `GH_PAT`: [github.com/settings/personal-access-tokens/new](https://github.com/settings/personal-access-tokens/new) → *Repository access: Only select repositories → reels-media* → *Permissions → Repository → Secrets: Read and write* → la caducidad más larga que te deje → **Generate token**.

### 3. Primera prueba
Avisa a Claude: subirá un solo reel de prueba a la cola. Cuando salga, comprueba en la app que aparece como **reel de prueba** (en tu perfil, Reels → Reels de prueba) y no en tu cuadrícula.

## Pruebas sin tocar Instagram

```bash
publicador/probar.sh
```

Usa una API simulada en una copia temporal del repo.
