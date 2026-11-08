# Configuración inicial

Esto lo hace Manuel: son sus cuentas y sus claves. Claude no las ve en ningún momento.

## Ya hecho (8 nov 2026)
- App de Meta **publicador-reels** (ID 2024328411858433), caso de uso «Manage messaging & content on Instagram».
- Portfolio comercial **Profe de mates en n pasos** (ID 4602008966743918), con la app vinculada.
- Cuenta de Instagram **@profedematesennpasos** añadida al portfolio. **ID de Instagram: `17841449699063169`**.

Meta ya no permite «Instagram login» en apps nuevas: la clave sale de un **usuario de sistema** del portfolio y **no caduca**.

## 1. Crear el usuario de sistema (3 min)
En **business.facebook.com → Configuración → Usuarios → Usuarios del sistema** (*System users*):
1. **Añadir** → nombre `publicador-reels`, rol **Administrador** → Crear.
2. Con el usuario seleccionado: **Asignar activos** (*Assign assets*):
   - **Cuentas de Instagram** → @profedematesennpasos → **Control total** (*Full control*).
   - **Apps** → publicador-reels → **Control total**.
   - Guardar.

## 2. Generar la clave (2 min)
Con el mismo usuario de sistema: **Generar identificador** (*Generate token*):
1. App: **publicador-reels**.
2. Caducidad: **Nunca** (*Never*).
3. Permisos: marca **instagram_basic**, **instagram_content_publish**, **instagram_manage_insights** y **business_management**.
4. Generar → **copia la clave** (solo se muestra una vez).

## 3. Guardar en GitHub (2 min)
**github.com/Manuasg/reels-media → Settings → Secrets and variables → Actions → New repository secret**:

| Nombre | Valor |
|---|---|
| `IG_TOKEN` | la clave del paso 2 |
| `IG_USER_ID` | `17841449699063169` |

## 4. Comprobar (no publica nada)
**Actions → «Comprobar conexión con Instagram (no publica)» → Run workflow.** Debe mostrar @profedematesennpasos, los seguidores y el cupo. Avisa a Claude con lo que salga.

Después Claude hará una prueba con un vídeo que crea un reel de prueba **sin publicarlo**, y luego la primera publicación real de un solo reel, que comprobarás en la app.
