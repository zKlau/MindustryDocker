#!/bin/sh
set -e

# Make sure the mounted volume is writable by the server user (Coolify/bind mounts are often root-owned).
chown -R mindustry:mindustry /data

# The dashboard app supervises the Mindustry server: it starts it, resumes the last game,
# restarts it if it crashes, saves on shutdown, and serves the web UI when ADMIN_PASSWORD is set.
cd /opt/dashboard
exec su-exec mindustry python3 -u -m app
