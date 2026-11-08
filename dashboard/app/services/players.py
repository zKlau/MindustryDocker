from ..common.js import fill, literal
from ..common.validation import uuid
from ..server import server

KICK_REASON = "Kicked by an admin"
MAX_BAN_ID_LENGTH = 64

FIND_PLAYER_JS = "var player = Groups.player.find(function(p){ return p.uuid() == ID; });"

PLAYERS_JS = """(function(){
  var list = [];
  Groups.player.each(function(p){
    var ip = "";
    if (p.con != null) { ip = p.con.address; }
    list.push({name: p.plainName(), uuid: p.uuid(), ip: ip, admin: p.admin, team: p.team().name});
  });
  return list;
})()"""

ONLINE_IDS_AND_NAMES_JS = """(function(){
  var list = [];
  Groups.player.each(function(p){ list.push({id: p.uuid(), name: Strings.stripColors(p.name)}); });
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
  FIND_PLAYER
  if (player == null) { return false; }
  player.kick(REASON);
  return true;
})()"""

MESSAGE_JS = """(function(){
  FIND_PLAYER
  if (player != null) { player.sendMessage(TEXT); }
  return true;
})()"""


def _find_player_js(player_id):
    return fill(FIND_PLAYER_JS, ID=literal(player_id))


def online():
    return server.query(PLAYERS_JS)


def online_brief():
    return server.query_or([], ONLINE_IDS_AND_NAMES_JS)


def bans():
    return server.query(BANS_JS)


def kick(player_id, reason=KICK_REASON):
    script = fill(KICK_JS, FIND_PLAYER=_find_player_js(uuid(player_id)), REASON=literal(reason))
    if not server.query(script):
        raise ValueError("Player is not online")


def message(player_id, text):
    script = fill(MESSAGE_JS, FIND_PLAYER=_find_player_js(player_id), TEXT=literal(text))
    server.query_or(None, script)


def ban(player_id):
    server.send(f"ban id {uuid(player_id)}")


def unban(value):
    value = str(value).strip()
    if not value or len(value) > MAX_BAN_ID_LENGTH or any(c.isspace() for c in value):
        raise ValueError("Invalid ID or IP")
    server.send(f"unban {value}")


def set_admin(player_id, on):
    action = "remove"
    if on:
        action = "add"
    server.send(f"admin {action} {uuid(player_id)}")
