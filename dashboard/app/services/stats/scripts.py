INSTALL_JS = """(function(){
  if (typeof dashStats !== "undefined") { return "already installed"; }
  dashStats = {built: {}, broken: {}, waves: {}};
  var name = function(player){ return Strings.stripColors(player.name); };
  var counts = function(player){
    return typeof dashAccess === "undefined" || dashAccess.allowed(player);
  };
  var add = function(table, id){ table[id] = (table[id] || 0) + 1; };

  Events.on(EventType.PlayerJoin, function(event){
    Log.info("@@STATS:join:" + event.player.uuid() + ":" + name(event.player));
  });
  Events.on(EventType.BlockBuildEndEvent, function(event){
    if (event.unit == null) { return; }
    var player = event.unit.getPlayer();
    if (player == null || !counts(player)) { return; }
    if (event.breaking) {
      add(dashStats.broken, player.uuid());
    } else {
      add(dashStats.built, player.uuid());
    }
  });
  Events.on(EventType.WaveEvent, function(event){
    Groups.player.each(function(p){ if (counts(p)) { add(dashStats.waves, p.uuid()); } });
  });

  var register = function(text, params, description, kind){
    Vars.netServer.clientCommands.register(text, params, description, new CommandHandler.CommandRunner({
      accept: function(args, player){
        var parts = [];
        for (var i = 0; i < args.length; i++) { parts.push(String(args[i])); }
        Log.info("@@STATS:" + kind + ":" + player.uuid() + ":" + parts.join(" "));
      }
    }));
  };
  register("stats", "[player...]", "Show your stats, or another player's", "stats");
  register("top", "[playtime/built/broken/waves/sessions]", "Show the server leaderboard", "top");
  return "installed";
})()"""

COLLECT_AND_RESET_COUNTERS_JS = """(function(){
  var online = [];
  Groups.player.each(function(p){
    if (typeof dashAccess === "undefined" || dashAccess.allowed(p)) {
      online.push({id: p.uuid(), name: Strings.stripColors(p.name)});
    }
  });
  var result = {online: online, built: dashStats.built, broken: dashStats.broken, waves: dashStats.waves};
  dashStats.built = {};
  dashStats.broken = {};
  dashStats.waves = {};
  return result;
})()"""
