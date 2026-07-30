# Guía de despliegue en Render (gratis, sin tarjeta)

Render construye la imagen a partir del `Dockerfile` del proyecto y te da una
URL pública tipo `https://ytdlp-app-xxxx.onrender.com` con HTTPS automático,
sin necesidad de meter ningún dato de pago para el plan gratuito de "Web
Service".

Antes de empezar, ten en cuenta las limitaciones del plan gratis para esta
app en concreto:

- **512 MB de RAM y 0.1 CPU** — suficiente para uso personal ligero, pero la
  primera compilación (ffmpeg + Node + Python) puede tardar varios minutos.
- **Se "duerme" tras 15 minutos sin uso** — la primera petición después de
  dormir tarda 30-60 segundos en responder mientras despierta.
- **Disco no persistente entre despliegues** — las cookies que subas desde
  el panel de la app sobreviven mientras la instancia está viva, pero se
  borran cada vez que Render reconstruye/despliega de nuevo (por ejemplo, si
  subes un cambio de código). Tendrás que volver a subir el `cookies.txt`
  después de cada actualización.

---

## Paso 1 — Sube el proyecto a GitHub

Render despliega conectándose a un repositorio de GitHub (o GitLab), no
aceptando un zip directamente. Si no tienes el proyecto en GitHub todavía:

1. Ve a [github.com](https://github.com) y crea una cuenta si no tienes
   (gratis, no pide tarjeta).
2. Pulsa el botón **"+"** arriba a la derecha → **"New repository"**.
3. Ponle un nombre, por ejemplo `yt-dlp-app`. Puedes dejarlo como
   **privado** (Render puede acceder igualmente a repos privados).
4. No marques ninguna casilla de inicialización (README, .gitignore, etc.).
5. Pulsa **"Create repository"**.

Ahora sube el código desde tu ordenador. Abre una terminal en la carpeta del
proyecto (la que descomprimiste del zip) y ejecuta:

```bash
cd yt-dlp-app
git init
git add .
git commit -m "Primera versión"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/yt-dlp-app.git
git push -u origin main
```

Sustituye `TU_USUARIO` por tu usuario de GitHub. Te pedirá autenticarte
(GitHub ya no acepta contraseña normal para esto: usa un **Personal Access
Token** que puedes generar en GitHub → Settings → Developer settings →
Personal access tokens, o simplemente instala GitHub Desktop y haz el push
desde ahí si prefieres interfaz gráfica).

---

## Paso 2 — Crear cuenta en Render

1. Ve a [render.com](https://render.com) → **"Get Started"**.
2. Regístrate con tu cuenta de GitHub (lo más simple, así Render ya tiene
   acceso a tus repos sin pasos extra).
3. No te pedirá ningún dato de tarjeta en este proceso.

---

## Paso 3 — Crear el Web Service

1. En el dashboard de Render, pulsa **"New +"** → **"Web Service"**.
2. Elige **"Build and deploy from a Git repository"** → conecta el repo
   `yt-dlp-app` que acabas de subir (si no aparece, pulsa "Configure account"
   y dale permiso a Render sobre ese repositorio).
3. Render detectará el `Dockerfile` automáticamente y marcará **Runtime:
   Docker** — no toques esto, es justo lo que necesitamos.
4. Configura estos campos:
   - **Name**: el nombre que quieras, por ejemplo `ytdlp-app` (formará parte
     de tu URL: `ytdlp-app.onrender.com`).
   - **Region**: la más cercana a ti (Frankfurt si estás en España/Europa).
   - **Branch**: `main`.
   - **Instance Type**: elige **Free** (ojo, por defecto a veces preselecciona
     un plan de pago — asegúrate de marcar el que dice "Free — $0/month").
5. Antes de crear, despliega la sección **"Advanced"** y añade las variables
   de entorno para proteger tu app con usuario/contraseña:
   - `APP_USER` = el usuario que quieras, por ejemplo `admin`
   - `APP_PASSWORD` = una contraseña segura que elijas

   (Esto activa el sistema de autenticación que ya añadí en el código;
   si dejas estas dos variables vacías, la app queda sin contraseña).
6. Pulsa **"Create Web Service"**.

---

## Paso 4 — Esperar el primer build

Render empieza a construir la imagen Docker automáticamente. Verás los logs
en directo en la pantalla. La primera vez tarda **entre 5 y 10 minutos**
(clona y compila el servidor de PO Tokens, instala ffmpeg, Node y las
dependencias de Python) — es normal, no lo canceles.

Sabrás que terminó bien cuando el estado pase a **"Live"** (círculo verde)
arriba del todo, y en los logs veas algo como:

```
Uvicorn running on http://0.0.0.0:10000
```

Si algo falla, los logs te dirán exactamente en qué paso — los errores más
típicos son fallos de red temporales al clonar `bgutil-ytdlp-pot-provider`
(simplemente pulsa "Manual Deploy" → "Deploy latest commit" para reintentar).

---

## Paso 5 — Probar la app

Arriba del dashboard verás la URL de tu servicio, algo como:

```
https://ytdlp-app.onrender.com
```

Ábrela en el navegador. Si configuraste `APP_USER`/`APP_PASSWORD`, el propio
navegador te mostrará un diálogo pidiendo usuario y contraseña antes de
enseñarte la interfaz.

> 💡 Si tardó 30-60 segundos en cargar la primera vez, es normal: el
> servicio estaba "dormido" por falta de uso y Render tuvo que despertarlo.
> Las siguientes peticiones, mientras siga activo, son instantáneas.

---

## Paso 6 — Actualizar la app en el futuro

Cada vez que quieras subir un cambio de código:

```bash
git add .
git commit -m "Descripción del cambio"
git push
```

Render detecta el push automáticamente y vuelve a desplegar (puedes verlo
en la pestaña "Events" del dashboard). Recuerda que el disco se resetea en
cada despliegue, así que si tenías cookies subidas, tendrás que volver a
subirlas después.

---

## Sobre YouTube y las IPs de Render

Igual que con cualquier proveedor cloud, las IPs de Render son de datacenter
y YouTube puede bloquearlas con más frecuencia que a una IP residencial,
independientemente del PO Token. El resto de sitios que soporta yt-dlp
(Vimeo, SoundCloud, TikTok, etc.) no suelen tener este problema. Si ves
errores de YouTube, sube tu `cookies.txt` desde el panel de la propia app —
recuerda que tendrás que repetirlo tras cada nuevo despliegue, por lo
comentado del disco no persistente.

---

## Si en el futuro necesitas más (sin salir de "gratis, sin tarjeta")

Si el límite de 512 MB de RAM se queda corto o quieres que no se duerma,
la alternativa sin gastar dinero ni meter tarjeta sigue siendo montar la
app en tu propio ordenador con Cloudflare Tunnel (sin límites de RAM/disco,
la única condición es dejar el equipo encendido). Si llegas a ese punto,
dímelo y te preparo esa guía.
