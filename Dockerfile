FROM eclipse-temurin:21-jre-alpine

# "latest" pulls the newest release from github.com/Anuken/Mindustry/releases.
# Pin a specific build with e.g. --build-arg MINDUSTRY_VERSION=v156.2
ARG MINDUSTRY_VERSION=latest

RUN apk add --no-cache su-exec \
 && addgroup -S -g 1000 mindustry \
 && adduser -S -D -H -u 1000 -G mindustry mindustry \
 && mkdir -p /opt/mindustry /data/config \
 && if [ "$MINDUSTRY_VERSION" = "latest" ]; then \
      URL="https://github.com/Anuken/Mindustry/releases/latest/download/server-release.jar"; \
    else \
      URL="https://github.com/Anuken/Mindustry/releases/download/${MINDUSTRY_VERSION}/server-release.jar"; \
    fi \
 && echo "Downloading $URL" \
 && wget -q -O /opt/mindustry/server-release.jar "$URL" \
 && chown -R mindustry:mindustry /data

COPY --chmod=755 docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh

# The server keeps config/, maps, saves and mods under ./config relative to its working dir.
WORKDIR /data
VOLUME /data

# Mindustry always listens on 6567 inside the container; pick the public port in .env.
EXPOSE 6567/tcp 6567/udp

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
