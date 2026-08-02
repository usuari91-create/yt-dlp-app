FROM python:3.11-slim

# ---- Dependencias de sistema: ffmpeg, node, deno, git ----
RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg git curl unzip ca-certificates gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# Deno: motor JS que necesita el sistema EJS de yt-dlp para resolver
# los retos de firma que pone YouTube en la mayoria de videos.
RUN curl -fsSL https://deno.land/install.sh | sh -s -- -y \
    && mv /root/.deno/bin/deno /usr/local/bin/deno \
    && deno --version

WORKDIR /app

# ---- Backend Python ----
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend backend
COPY frontend frontend

# ---- bgutil POT provider (clonado y compilado en build time) ----
ARG BGUTIL_BRANCH=1.3.1
RUN git clone --single-branch --branch ${BGUTIL_BRANCH} --depth 1 \
        https://github.com/Brainicism/bgutil-ytdlp-pot-provider.git \
        /opt/bgutil-provider \
    && cd /opt/bgutil-provider/server \
    && npm ci --no-audit --no-fund \
    && npx tsc

ENV BGUTIL_DIR=/opt/bgutil-provider/server
ENV HOST=0.0.0.0

# Directorios de datos (cookies, descargas temporales).
# Nota: en Render (nivel free) el disco es efimero entre despliegues,
# aunque persiste mientras la instancia esta viva/dormida.
RUN mkdir -p backend/data backend/downloads

EXPOSE 8000

# Render inyecta la variable $PORT en tiempo de ejecucion; si no existe
# (por ejemplo al correr esto en local), usamos 8000 por defecto.
CMD ["sh", "-c", "python3 -m uvicorn main:app --app-dir backend --host 0.0.0.0 --port ${PORT:-8000}"]
