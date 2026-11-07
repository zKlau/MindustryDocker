# Mindustry server in Docker (with web dashboard)

Builds the official dedicated server from [Anuken/Mindustry releases](https://github.com/Anuken/Mindustry/releases) and runs it in one container, together with a small password-protected web dashboard.

## Run locally

```bash
cp .env.example .env   # set ADMIN_PASSWORD
docker compose up -d --build
docker compose logs -f
```

- Players connect to `<your-host>:<SERVER_PORT>`.
- The dashboard is at `http://<your-host>:<DASHBOARD_PORT>`.

## Settings (`.env`)

| Variable                   | Default                 | What it does                                                                   |
| -------------------------- | ----------------------- | ------------------------------------------------------------------------------ |
| `SERVER_PORT`              | `6567`                  | Public game port on the host, forwarded to 6567 in the container (TCP and UDP) |
| `ADMIN_PASSWORD`           | empty                   | Dashboard password. Empty = dashboard disabled                                 |
| `DASHBOARD_PORT`           | `8080`                  | Host port for the dashboard (plain HTTP)                                       |
| `MINDUSTRY_VERSION`        | `latest`                | Release tag to download at build time, for example `v156.2`                    |
| `MINDUSTRY_SERVER_NAME`    | empty                   | Server name shown in the browser (no commas)                                   |
| `MINDUSTRY_START_COMMANDS` | `config port 6567,host` | Console commands run at startup, comma-separated                               |
| `JAVA_OPTS`                | `-Xmx1G`                | JVM options                                                                    |

## Dashboard

| Tab      | What you can do                                                                                                                                                                                                   |
| -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Overview | Map, planet, mode, wave, next-wave timer, players, play time, FPS, memory. Pause/resume, send next wave, fill core, force game over, restart server, broadcast a message                                          |
| Map      | Pick any custom-game map or campaign sector (Serpulo and Erekir), filter by planet, play it now or after the current game. Players stay connected. Upload and delete custom `.msav` maps                          |
| Rules    | Presets (endless, manual waves, peaceful, chill, creative) and individual rules: win wave, wave timer and interval, infinite resources, fog, build/unit/damage multipliers. Applied live and kept for future maps |
| Saves    | Save, load, download, upload and delete saved games                                                                                                                                                               |
| Players  | Online players with kick, ban and admin. Ban list with unban                                                                                                                                                      |
| Mods     | Installed mods/plugins with load status, upload and delete                                                                                                                                                        |
| Settings | What happens on start (continue last game, a fixed map, or env commands), plus name, description, MOTD, player limit, autosave, pause when empty, vote-kick                                                       |
| Console  | Live server log and a command box for any server command                                                                                                                                                          |

### Planets

The planet is part of the map: each map or campaign sector belongs to Serpulo or Erekir and brings that planet's blocks, units and environment. To play on Erekir, pick an Erekir map on the Map tab (for example _Onset_, _Aegis_ or the _Domain_ custom-game map).

### Keeping your world

On every shutdown, redeploy or "Restart server", the world is saved as `last-session`. With the default startup setting ("Continue the last game"), the server loads the newest of that save and the autosaves when it starts again, so a redeploy doesn't throw away your base. `MINDUSTRY_START_COMMANDS` is only used when there is no save yet, or when you choose that option in Settings.

### HTTPS

The dashboard itself speaks plain HTTP. Get HTTPS by pointing a Cloudflare Tunnel public hostname (for example `mindustry-admin.example.com`) at `http://localhost:<DASHBOARD_PORT>`, or at `http://<container>:8080` if `cloudflared` runs in Docker. Adding Cloudflare Access in front gives you a second login layer.

Don't port-forward the dashboard port on your router. Only the game port needs to be public.

## Project layout

```
Dockerfile, docker-compose.yml, docker-entrypoint.sh
dashboard/
  app/                    Python backend (standard library only), run with `python -m app`
    __main__.py           entry point: starts the web server and supervises Mindustry
    settings.py           environment variables and paths
    state.py              dashboard-owned settings (rule overrides, startup behaviour)
    server.py             Mindustry process: console input, log buffer, JS queries
    validation.py         input checks for anything sent to the console
    data/                 block_colors.json (map colours for previews)
    services/             one module per feature: game, maps, previews, rules, saves,
                          players, mods, server_config, startup
    web/                  HTTP layer: auth, router, routes (API endpoints), handler
  static/                 frontend (plain ES modules, no build step)
    index.html            page layout plus <template> elements for repeated pieces
    css/                  base, layout, components/*, pages/*
    js/main.js            app shell: login, tabs, polling
    js/api.js, ui.js, store.js
    js/tabs/*.js          one module per tab
tools/
  extract_block_colors.py regenerates dashboard/app/data/block_colors.json
```

The backend reads structured data from the server by evaluating JavaScript with Mindustry's `js` console command, so no server plugin is needed.

### Map previews

The headless server doesn't load textures, so every block's map colour is black. The dashboard sets real colours from `dashboard/app/data/block_colors.json` on each server start, then renders previews with the game's own `MapIO` and caches them in `/data/dashboard/previews`. After a Mindustry update adds new terrain blocks, regenerate the colours with the commands at the top of `tools/extract_block_colors.py`.

## Development

Formatting and linting run locally only; nothing here is needed in the Docker image.

```bash
npm install
pip install ruff
```

```bash
npm run format     # Prettier (JS, CSS, HTML, JSON, Markdown, YAML) + Ruff formatter
npm run lint       # ESLint, Stylelint, Prettier check, Ruff lint + format check
npm run lint:fix   # auto-fix what can be fixed
```

Style rules worth knowing:

- JavaScript: no ternaries or one-line `if`s (`curly`, `no-ternary`, `no-unused-expressions`), small functions (complexity and length warnings). HTML for repeated pieces lives in `<template>` elements, not in JS strings.
- CSS: one file per component or page, one declaration per line (Stylelint standard config).
- Python: Ruff with pycodestyle, pyflakes, import sorting, bugbear, naming, simplify, pathlib and a complexity limit of 10. Inline `x if c else y` is avoided on purpose.

To run the dashboard without Docker (needs Java 17+ and the server jar):

```bash
cd dashboard
MINDUSTRY_DATA=/tmp/mindustry MINDUSTRY_JAR=/path/to/server-release.jar ADMIN_PASSWORD=test python -m app
```

## Console from the terminal

```bash
docker attach mindustry
```

Detach with `Ctrl+P` then `Ctrl+Q`. The server restarts automatically if it exits (including after `exit`). To stop it for good, stop the container.

## Data

Everything lives in the `mindustry-data` volume at `/data/config`: settings, saves, maps (`config/maps`) and mods/plugins (`config/mods`).

## Updating

`latest` is resolved when the image is built. To get a newer release, rebuild:

```bash
docker compose build --no-cache && docker compose up -d
```

## Coolify

1. Create a resource from this Git repo and choose **Docker Compose** as the build pack.
2. Set the variables above in the Environment Variables tab (at least `SERVER_PORT` and `ADMIN_PASSWORD`).
3. Deploy. Players use `<server-ip>:<SERVER_PORT>`. Open that port for TCP and UDP in the firewall and router.
4. For the dashboard, add a Cloudflare Tunnel hostname pointing at the dashboard port.
