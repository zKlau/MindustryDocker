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
  var r = {networks: 0, short: 0, produced: 0, needed: 0, balance: 0, stored: 0, capacity: 0};
  for (var id in graphs) {
    var g = graphs[id];
    if (g.producers.isEmpty() && g.consumers.isEmpty() && g.batteries.isEmpty()) { continue; }
    r.networks++;
    if (g.getLastPowerNeeded() > 0 && g.getSatisfaction() < 0.999) { r.short++; }
    r.produced += g.getLastScaledPowerIn();
    r.needed += g.getLastScaledPowerOut();
    r.balance += g.getPowerBalance();
    r.stored += g.getLastPowerStored();
    r.capacity += g.getLastCapacity();
  }
  return r.networks > 0 ? r : null;
})()"""

PER_TICK_FIELDS = ("produced", "needed", "balance")

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


def power_totals(power):
    if power is None:
        return None

    return {**power, **{field: power[field] * TICKS_PER_SECOND for field in PER_TICK_FIELDS}}
