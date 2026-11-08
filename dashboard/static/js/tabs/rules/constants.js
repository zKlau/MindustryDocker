export const LABELS = {
  waves: ["Enemy waves", "Turn off for peaceful building."],
  waveTimer: ["Automatic wave timer", 'Off = waves only come when you press "Send next wave".'],
  waveSpacing: ["Time between waves (seconds)", ""],
  waitEnemies: ["Wait for enemies to die", "The next wave waits until the current one is cleared."],
  winWave: ["Win at wave", "0 = the game never ends by surviving waves."],
  infiniteResources: ["Infinite resources", "Build anything for free."],
  fog: ["Fog of war", ""],
  coreIncinerates: ["Core burns excess items", ""],
  unitCap: ["Extra unit cap", "Added to the normal unit limit."],
  buildSpeedMultiplier: ["Build speed ×", ""],
  buildCostMultiplier: ["Build cost ×", ""],
  unitBuildSpeedMultiplier: ["Unit production speed ×", ""],
  unitDamageMultiplier: ["Unit damage ×", ""],
  unitHealthMultiplier: ["Unit health ×", ""],
  blockHealthMultiplier: ["Block health ×", ""],
  blockDamageMultiplier: ["Block (turret) damage ×", ""],
  deconstructRefundMultiplier: ["Deconstruct refund ×", "1 = full refund."],
};

export const PRESETS = {
  endless: { winWave: 0 },
  manual: { waveTimer: false, winWave: 0 },
  peaceful: { waves: false, winWave: 0 },
  chill: {
    waves: true,
    waveTimer: true,
    waveSpacing: 300,
    waitEnemies: true,
    buildSpeedMultiplier: 2,
    winWave: 0,
  },
  creative: { infiniteResources: true },
};
