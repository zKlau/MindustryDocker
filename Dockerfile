FROM eclipse-temurin:21-jre-alpine

# "latest" (or empty) pulls the newest release from github.com/Anuken/Mindustry/releases.
# Pin a specific build with e.g. --build-arg MINDUSTRY_VERSION=v156.2
ARG MINDUSTRY_VERSION=latest

# python3 runs the web dashboard (standard library only, no pip packages).
RUN apk add --no-cache su-exec curl python3

# Server user. No fixed UID/GID so it never collides with users already in the base image.
RUN addgroup -S mindustry \
 && adduser -S -D -H -G mindustry mindustry \
 && mkdir -p /opt/mindustry /data/config

# Download the official server jar. Fails loudly with the URL if the release/tag doesn't exist.
RUN V="${MINDUSTRY_VERSION:-latest}"; \
    if [ "$V" = "latest" ]; then \
      URL="https://github.com/Anuken/Mindustry/releases/latest/download/server-release.jar"; \
    else \
      URL="https://github.com/Anuken/Mindustry/releases/download/${V}/server-release.jar"; \
    fi; \
    echo "Downloading $URL"; \
    curl -fSL --retry 3 -o /opt/mindustry/server-release.jar "$URL" \
      || { echo "ERROR: could not download $URL (check MINDUSTRY_VERSION)"; exit 1; }; \
    ls -l /opt/mindustry/server-release.jar

RUN chown -R mindustry:mindustry /data

COPY dashboard/app/ /opt/dashboard/app/
COPY dashboard/static/ /opt/dashboard/static/
COPY --chmod=755 docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh

# The server keeps config/, maps, saves and mods under ./config relative to its working dir.
WORKDIR /data
VOLUME /data

# 6567 = game (TCP+UDP). 8080 = web dashboard (HTTP; put HTTPS in front with Cloudflare Tunnel).
EXPOSE 6567/tcp 6567/udp 8080/tcp

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s \
  CMD wget -qO- http://127.0.0.1:8080/healthz >/dev/null 2>&1 || pgrep -f server-release.jar >/dev/null

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
