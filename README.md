# Mindustry server in Docker

Builds the official dedicated server from [Anuken/Mindustry releases](https://github.com/Anuken/Mindustry/releases) and runs it in a container.

## Run locally

```bash
cp .env.example .env
docker compose up -d --build
docker compose logs -f
```

Players connect to `<your-host>:<SERVER_PORT>`.

## Settings (`.env`)

| Variable | Default | What it does |
|---|---|---|
| `SERVER_PORT` | `6567` | Public port on the host, forwarded to 6567 in the container (TCP and UDP) |
| `MINDUSTRY_VERSION` | `latest` | Release tag to download at build time, for example `v156.2` |
| `MINDUSTRY_SERVER_NAME` | empty | Server name shown in the browser (no commas) |
| `MINDUSTRY_START_COMMANDS` | `config port 6567,host` | Console commands run at startup, comma-separated |
| `JAVA_OPTS` | `-Xmx1G` | JVM options |

## Console

```bash
docker attach mindustry
```

Type commands such as `help`, `status` or `host Ancient_Caldera survival`. Detach with `Ctrl+P` then `Ctrl+Q`. `Ctrl+C` stops the server.

## Data

Everything lives in the `mindustry-data` volume at `/data/config`: settings, saves, maps (`config/maps`) and mods/plugins (`config/mods`).

## Updating

`latest` is resolved when the image is built. To get a newer release, rebuild:

```bash
docker compose build --no-cache && docker compose up -d
```

## Coolify

1. Create a resource from this Git repo and choose **Docker Compose** as the build pack.
2. Set the variables above in the Environment Variables tab.
3. Deploy. Coolify's proxy only handles HTTP, so players use `<server-ip>:<SERVER_PORT>` directly. Open that port for both TCP and UDP in the server firewall.
