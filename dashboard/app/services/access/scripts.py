INSTALL_JS = """(function(){
  if (typeof dashAccess !== "undefined") { return "already installed"; }
  dashAccess = {enabled: false, password: "", remembered: {}, timeout: TIMEOUT};

  dashAccess.allowed = function(player){
    if (!dashAccess.enabled || player == null || player.admin) { return true; }
    return dashAccess.remembered[player.uuid()] === true;
  };

  var name = function(player){ return Strings.stripColors(player.name); };

  var login = function(args, player){
    if (!dashAccess.enabled) { player.sendMessage("[accent]This server has no password."); return; }
    if (dashAccess.allowed(player)) { player.sendMessage("[accent]You are already logged in."); return; }
    if (args[0] == dashAccess.password) {
      dashAccess.remembered[player.uuid()] = true;
      Log.info("@@ACCESS:login:" + player.uuid() + ":" + name(player));
      player.sendMessage("[green]Logged in. Have fun!");
    } else {
      Log.info("@@ACCESS:failed:" + player.uuid() + ":" + name(player));
      player.sendMessage("[scarlet]Wrong password.");
    }
  };
  Vars.netServer.clientCommands.register("login", "<password>", "Log in with the server password",
    new CommandHandler.CommandRunner({accept: login}));

  Vars.netServer.admins.addChatFilter(function(player, text){
    if (dashAccess.allowed(player)) { return text; }
    player.sendMessage("[scarlet]Log in first: [white]/login <password>");
    return null;
  });
  Vars.netServer.admins.addActionFilter(function(action){ return dashAccess.allowed(action.player); });

  var kickIfStillLoggedOut = function(id){
    Core.app.post(function(){
      var player = Groups.player.find(function(p){ return p.uuid() == id; });
      if (player != null && !dashAccess.allowed(player)) {
        player.kick("Login timed out. Get the password from the host, then type /login <password>.", 0);
      }
    });
  };

  Events.on(EventType.PlayerJoin, function(event){
    var player = event.player;
    if (dashAccess.allowed(player)) { return; }
    var seconds = dashAccess.timeout;
    var text = "This server needs a password.\\n\\nType [accent]/login <password>[] in chat within ";
    Call.infoMessage(player.con, text + seconds + " seconds.");
    player.sendMessage("[accent]Type /login <password> to play.");
    var id = player.uuid();
    Timer.schedule(function(){ kickIfStillLoggedOut(id); }, seconds);
  });
  return "installed";
})()"""

CONFIGURE_JS = """(function(){
  dashAccess.enabled = ENABLED;
  dashAccess.password = PASSWORD;
  dashAccess.remembered = REMEMBERED;
  return true;
})()"""

WHITELIST_ENABLED_JS = "Administration.Config.whitelist.bool()"
