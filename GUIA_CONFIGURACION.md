# Configuración inicial (una sola vez, unos 20-30 min)

Esto lo hace Manuel: son sus cuentas y sus claves. Claude no las ve en ningún momento.

## 1. Crear la app en Meta (10-15 min)
1. Entra en **developers.facebook.com** con tu cuenta de Facebook. Si es la primera vez, te pedirá registrarte como desarrollador (verificación por SMS o correo).
2. **Mis apps → Crear app**.
3. Caso de uso: **«Gestionar mensajes y contenido en Instagram»** (en inglés, *Manage messaging & content on Instagram*). Si pregunta por un portfolio comercial, elige que no.
4. Nombre: por ejemplo `publicador-reels`. Crear.
5. En el panel de la app: **Casos de uso → Personalizar → Configuración de la API con inicio de sesión de Instagram** (*API setup with Instagram login*).
6. En **«Generar identificadores de acceso»**: **Añadir cuenta** → entra con **@profedematesenNpasos** y acepta los permisos.
   - Si Instagram te avisa de una invitación de «tester», acéptala en la app: **Configuración → Apps y sitios web → Invitaciones de tester**.
7. Junto a la cuenta ya añadida verás:
   - un número, el **ID de usuario de Instagram** → cópialo;
   - el botón **Generar identificador** → pulsa y copia la clave larga que sale (empieza por `IG...`). Solo se muestra una vez.

No hace falta publicar la app ni pasar la revisión de Meta: en modo desarrollo funciona para tu propia cuenta.

## 2. Guardar las claves en GitHub (5 min)
En **github.com/Manuasg/reels-media → Settings → Secrets and variables → Actions → New repository secret**, crea:

| Nombre | Valor |
|---|---|
| `IG_TOKEN` | la clave larga de Instagram |
| `IG_USER_ID` | el número del ID de usuario de Instagram |
| `GH_PAT` | la clave de GitHub del paso 3 |

## 3. Clave de GitHub para renovar la de Instagram (5 min)
La clave de Instagram caduca a los 60 días; el repo la renueva solo los días 1 y 15. Para poder guardarla necesita permiso:
1. **github.com/settings/personal-access-tokens/new** (Fine-grained token).
2. Nombre: `renovar-clave-instagram`. Caducidad: la máxima que permita (si caduca, GitHub te avisa por correo antes).
3. **Repository access → Only select repositories → `reels-media`**.
4. **Permissions → Repository permissions → Secrets → Read and write**. Nada más.
5. Genera, copia y guárdala como secreto `GH_PAT` (paso 2).

## 4. Comprobar (2 min, no publica nada)
**Actions → «Comprobar conexión con Instagram (no publica)» → Run workflow.** Debe mostrar tu cuenta, el tipo (profesional), los seguidores y el cupo. Avisa a Claude con lo que salga.

Luego Claude hará una segunda comprobación con un vídeo: crea un reel de prueba **sin publicarlo**, para confirmar que Instagram acepta el modo de prueba. Y después, la primera publicación real de un solo reel, que comprobarás en la app.
