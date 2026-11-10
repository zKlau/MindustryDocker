import collections
import threading

from ..common.constants import TICKS_PER_SECOND

RATE_WINDOW_SECONDS = 30
MIN_RATE_SPAN_SECONDS = 2

CORE_JS = """(function(){
  var core = Vars.state.rules.defaultTeam.core();
  if (core == null) { return null; }
  var items = [];
  Vars.content.items().each(function(item){
    items.push({
      name: String(item.name),
      label: String(item.localizedName),
      color: String(item.color.toString()).substring(0, 6),
      amount: core.items.get(item)
    });
  });
  return {capacity: core.storageCapacity, items: items};
})()"""

POWER_JS = """(function(){
  var graphs = {};
  Vars.state.rules.defaultTeam.data().buildings.each(function(build){
    if (build.power != null) { graphs[build.power.graph.getID()] = build.power.graph; }
  });
  var num = function(x){ return isFinite(x) ? x : 0; };
  var r = {networks: 0, short: 0, produced: 0, needed: 0, balance: 0, stored: 0, capacity: 0};
  for (var id in graphs) {
    var g = graphs[id];
    if (g.producers.isEmpty() && g.consumers.isEmpty() && g.batteries.isEmpty()) { continue; }
    r.networks++;
    if (g.getLastPowerNeeded() > 0 && g.getSatisfaction() < 0.999) { r.short++; }
    r.produced += num(g.getLastScaledPowerIn());
    r.needed += num(g.getLastScaledPowerOut());
    r.balance += num(g.getPowerBalance());
    r.stored += num(g.getLastPowerStored());
    r.capacity += num(g.getLastCapacity());
  }
  return r.networks > 0 ? r : null;
})()"""

LIQUIDS_JS = """(function(){
  var totals = {};
  var any = false;
  var entry = function(liquid){
    var name = String(liquid.name);
    if (!totals[name]) { totals[name] = {stored: 0, produced: 0, used: 0}; }
    return totals[name];
  };
  var valid = function(x){ return isFinite(x) && x > 0; };
  var produce = function(liquid, amount){ if (valid(amount)) { entry(liquid).produced += amount; } };
  var consume = function(build, liquid, amount, consumer){
    if (consumer.optional && build.optionalEfficiency <= 0) { return; }
    var used = amount * build.efficiency * build.timeScale * consumer.multiplier.get(build);
    if (valid(used)) { entry(liquid).used += used; }
  };
  Vars.state.rules.defaultTeam.data().buildings.each(function(build){
    var block = build.block;
    if (build.liquids != null) {
      any = true;
      build.liquids.each(function(liquid, amount){ if (valid(amount)) { entry(liquid).stored += amount; } });
    }
    if (build.lastPump !== undefined) {
      produce(build.liquidDrop, build.lastPump);
    } else if (build.liquidDrop !== undefined && build.liquidDrop != null) {
      produce(build.liquidDrop, build.amount * block.pumpAmount * build.efficiency * build.timeScale);
    } else if (block.outputLiquids !== undefined && block.outputLiquids != null) {
      for (var i = 0; i < block.outputLiquids.length; i++) {
        var stack = block.outputLiquids[i];
        produce(stack.liquid, stack.amount * build.efficiency * build.timeScale);
      }
    } else if (block.outputLiquid !== undefined && block.outputLiquid != null) {
      produce(block.outputLiquid.liquid, block.outputLiquid.amount * build.productionEfficiency);
    }
    if (build.efficiency <= 0) { return; }
    for (var j = 0; j < block.consumers.length; j++) {
      var c = block.consumers[j];
      if (c.liquid !== undefined && c.liquid != null) {
        consume(build, c.liquid, c.amount, c);
      } else if (c.liquids !== undefined && c.liquids != null) {
        for (var k = 0; k < c.liquids.length; k++) {
          consume(build, c.liquids[k].liquid, c.liquids[k].amount, c);
        }
      }
    }
  });
  if (!any) { return null; }
  var result = [];
  Vars.content.liquids().each(function(liquid){
    var t = totals[String(liquid.name)];
    if (!t) { return; }
    result.push({
      name: String(liquid.name),
      label: String(liquid.localizedName),
      color: String(liquid.color.toString()).substring(0, 6),
      stored: t.stored,
      produced: t.produced,
      used: t.used
    });
  });
  return result;
})()"""

PER_TICK_FIELDS = ("produced", "needed", "balance")
PER_TICK_LIQUID_FIELDS = ("produced", "used")
MIN_SHOWN_AMOUNT = 0.5

_samples = collections.deque()
_lock = threading.Lock()


def _record(map_name, tick, amounts):
    with _lock:
        if _samples and (_samples[-1][0] != map_name or tick < _samples[-1][1]):
            _samples.clear()
        if not _samples or tick > _samples[-1][1]:
            _samples.append((map_name, tick, amounts))
        window_start = tick - RATE_WINDOW_SECONDS * TICKS_PER_SECOND
        while len(_samples) > 2 and _samples[1][1] <= window_start:
            _samples.popleft()

        return _samples[0], _samples[-1]


def _rates(oldest, newest):
    span = (newest[1] - oldest[1]) / TICKS_PER_SECOND
    if span < MIN_RATE_SPAN_SECONDS:
        return {}

    return {name: (amount - oldest[2].get(name, 0)) / span for name, amount in newest[2].items()}


def core_items(core, map_name, tick):
    if core is None:
        return None
    amounts = {item["name"]: item["amount"] for item in core["items"]}
    rates = _rates(*_record(map_name, tick, amounts))
    items = [{**item, "rate": rates.get(item["name"])} for item in core["items"]]

    return {"capacity": core["capacity"], "items": items}


def _per_second(per_tick):
    if per_tick is None:
        return 0

    return per_tick * TICKS_PER_SECOND


def power_totals(power):
    if power is None:
        return None

    return {**power, **{field: _per_second(power[field]) for field in PER_TICK_FIELDS}}


def liquid_totals(liquids):
    if liquids is None:
        return None
    totals = [
        {**liquid, **{field: _per_second(liquid[field]) for field in PER_TICK_LIQUID_FIELDS}}
        for liquid in liquids
    ]

    return [
        liquid
        for liquid in totals
        if max(liquid["stored"], liquid["produced"], liquid["used"]) >= MIN_SHOWN_AMOUNT
    ]
