FROM eclipse-temurin:21-jre-alpine

# "latest" (or empty) pulls the newest release from github.com/Anuken/Mindustry/releases.
# Pin a specific build with e.g. --build-arg MINDUSTRY_VERSION=v156.2
ARG MINDUSTRY_VERSION=latest

RUN apk add --no-cache su-exec curl

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

COPY --chmod=755 docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh

# The server keeps config/, maps, saves and mods under ./config relative to its working dir.
WORKDIR /data
VOLUME /data

# Mindustry always listens on 6567 inside the container; pick the public port in .env.
EXPOSE 6567/tcp 6567/udp

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
