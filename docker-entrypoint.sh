#!/bin/sh
set -e

# Make sure the mounted volume is writable by the server user (Coolify/bind mounts are often root-owned).
chown -R mindustry:mindustry /data

# Commands the server runs on startup, comma-separated.
# Default: keep the internal port at 6567 and start hosting a random map.
START_COMMANDS="${MINDUSTRY_START_COMMANDS:-config port 6567,host}"
if [ -n "$MINDUSTRY_SERVER_NAME" ]; then
  START_COMMANDS="config name ${MINDUSTRY_SERVER_NAME},${START_COMMANDS}"
fi

echo "Starting Mindustry server with: ${START_COMMANDS}"
# shellcheck disable=SC2086
exec su-exec mindustry java ${JAVA_OPTS} -jar /opt/mindustry/server-release.jar "${START_COMMANDS}"
