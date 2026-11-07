"""Online players, admins and bans."""

from ..server import server
from ..validation import js_string, uuid

PLAYERS_JS = """(function(){
  var list = [];
  Groups.player.each(function(p){
    var ip = "";
    if (p.con != null) { ip = p.con.address; }
    list.push({name: p.plainName(), uuid: p.uuid(), ip: ip, admin: p.admin, team: p.team().name});
  });
  return list;
})()"""

BANS_JS = """(function(){
  var ids = [];
  var ips = [];
  Vars.netServer.admins.getBanned().each(function(info){
    ids.push({id: info.id, name: Strings.stripColors(info.lastName)});
  });
  Vars.netServer.admins.getBannedIPs().each(function(ip){ ips.push(ip); });
  return {ids: ids, ips: ips};
})()"""

KICK_JS = """(function(){
  var p = Groups.player.find(function(p){ return p.uuid() == ID; });
  if (p == null) { return false; }
  p.kick(REASON);
  return true;
})()"""


def online():
    return server.query(PLAYERS_JS)


def bans():
    return server.query(BANS_JS)


def kick(player_id, reason="Kicked by an admin"):
    script = KICK_JS.replace("ID", js_string(uuid(player_id))).replace("REASON", js_string(reason))
    if not server.query(script):
        raise ValueError("Player is not online")


def ban(player_id):
    server.send(f"ban id {uuid(player_id)}")


def unban(value):
    value = str(value).strip()
    if not value or len(value) > 64 or any(c.isspace() for c in value):
        raise ValueError("Invalid ID or IP")
    server.send(f"unban {value}")


def set_admin(player_id, on):
    if on:
        server.send(f"admin add {uuid(player_id)}")
    else:
        server.send(f"admin remove {uuid(player_id)}")
