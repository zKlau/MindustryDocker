// State shared between tabs.

export const store = {
  /** Latest /api/status response. */
  status: {},
  /** Map picked on the Map tab: { kind: "map" | "sector", name, label, planet, custom, width, height }. */
  selectedMap: null,
};
