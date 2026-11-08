export const API = {
  session: "/api/session",
  login: "/api/login",
  logout: "/api/logout",
  status: "/api/status",
  logs: "/api/logs",
  console: "/api/console",
  config: "/api/config",
  startup: "/api/startup",
  game: {
    pause: "/api/game/pause",
    nextWave: "/api/game/next-wave",
    gameOver: "/api/game/game-over",
    fillCore: "/api/game/fill-core",
    say: "/api/game/say",
    restart: "/api/game/restart",
  },
  maps: {
    list: "/api/maps",
    host: "/api/maps/host",
    next: "/api/maps/next",
    upload: "/api/maps/upload",
    delete: "/api/maps/delete",
    preview: "/api/maps/preview",
  },
  onlineMaps: {
    search: "/api/online/maps",
    preview: "/api/online/maps/preview",
    install: "/api/online/maps/install",
  },
  rules: {
    current: "/api/rules",
    reset: "/api/rules/reset",
  },
  saves: {
    list: "/api/saves",
    save: "/api/saves/save",
    load: "/api/saves/load",
    delete: "/api/saves/delete",
    upload: "/api/saves/upload",
    download: "/api/saves/download",
  },
  players: {
    online: "/api/players",
    bans: "/api/players/bans",
    kick: "/api/players/kick",
    ban: "/api/players/ban",
    unban: "/api/players/unban",
    admin: "/api/players/admin",
  },
  access: {
    status: "/api/access",
    password: "/api/access/password",
    forget: "/api/access/forget",
    whitelist: "/api/access/whitelist",
    approve: "/api/access/whitelist/approve",
    remove: "/api/access/whitelist/remove",
    dismiss: "/api/access/whitelist/dismiss",
  },
  stats: {
    leaderboard: "/api/stats",
    remove: "/api/stats/remove",
    reset: "/api/stats/reset",
  },
  mods: {
    list: "/api/mods",
    upload: "/api/mods/upload",
    delete: "/api/mods/delete",
  },
  onlineMods: {
    search: "/api/online/mods",
    install: "/api/online/mods/install",
  },
};

export function withQuery(path, params) {
  return `${path}?${new URLSearchParams(params)}`;
}

export function mapPreviewUrl(kind, name) {
  return withQuery(API.maps.preview, { kind, name });
}

export function onlineMapPreviewUrl(id) {
  return withQuery(API.onlineMaps.preview, { id });
}

export function saveDownloadUrl(name) {
  return withQuery(API.saves.download, { name });
}
