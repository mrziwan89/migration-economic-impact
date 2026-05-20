export const STATE_NAMES: Record<string, string> = {
  AL: "Alabama", AK: "Alaska", AZ: "Arizona", AR: "Arkansas", CA: "California",
  CO: "Colorado", CT: "Connecticut", DE: "Delaware", DC: "District of Columbia",
  FL: "Florida", GA: "Georgia", HI: "Hawaii", ID: "Idaho", IL: "Illinois",
  IN: "Indiana", IA: "Iowa", KS: "Kansas", KY: "Kentucky", LA: "Louisiana",
  ME: "Maine", MD: "Maryland", MA: "Massachusetts", MI: "Michigan",
  MN: "Minnesota", MS: "Mississippi", MO: "Missouri", MT: "Montana",
  NE: "Nebraska", NV: "Nevada", NH: "New Hampshire", NJ: "New Jersey",
  NM: "New Mexico", NY: "New York", NC: "North Carolina", ND: "North Dakota",
  OH: "Ohio", OK: "Oklahoma", OR: "Oregon", PA: "Pennsylvania",
  RI: "Rhode Island", SC: "South Carolina", SD: "South Dakota",
  TN: "Tennessee", TX: "Texas", UT: "Utah", VT: "Vermont", VA: "Virginia",
  WA: "Washington", WV: "West Virginia", WI: "Wisconsin", WY: "Wyoming"
};

export const FIPS_TO_STATE: Record<number, string> = {
  1: "AL", 2: "AK", 4: "AZ", 5: "AR", 6: "CA", 8: "CO", 9: "CT", 10: "DE",
  11: "DC", 12: "FL", 13: "GA", 15: "HI", 16: "ID", 17: "IL", 18: "IN",
  19: "IA", 20: "KS", 21: "KY", 22: "LA", 23: "ME", 24: "MD", 25: "MA",
  26: "MI", 27: "MN", 28: "MS", 29: "MO", 30: "MT", 31: "NE", 32: "NV",
  33: "NH", 34: "NJ", 35: "NM", 36: "NY", 37: "NC", 38: "ND", 39: "OH",
  40: "OK", 41: "OR", 42: "PA", 44: "RI", 45: "SC", 46: "SD", 47: "TN",
  48: "TX", 49: "UT", 50: "VT", 51: "VA", 53: "WA", 54: "WV", 55: "WI",
  56: "WY"
};

export const CITIZEN_ORDER = [
  "total",
  "reporting_country",
  "foreign_country",
  "non_eu",
  "eu_mobile",
  "eu27_total",
  "stateless",
  "no_response"
];

export const EU_TREND_GROUPS = ["reporting_country", "foreign_country", "non_eu", "eu_mobile"];

export const PERIODS = {
  usa: ["2008-2013", "2014-2019", "2020-2024"],
  eurostat: ["2014-2019", "2020-2024"]
} as const;

// All known period buckets for mapping year → period (sorted earliest-first)
export const PERIOD_BUCKETS = [
  { label: "1995-2007", start: 1995, end: 2007 },
  { label: "2008-2013", start: 2008, end: 2013 },
  { label: "2014-2019", start: 2014, end: 2019 },
  { label: "2020-2024", start: 2020, end: 2024 }
];

/** Map a single year to its parent period bucket. Falls back to latest. */
export function yearToPeriod(year: number, allowedPeriods: readonly string[]): string {
  for (const bucket of PERIOD_BUCKETS) {
    if (year >= bucket.start && year <= bucket.end && allowedPeriods.includes(bucket.label)) {
      return bucket.label;
    }
  }
  // If "Latest available" is an option, use it as final fallback
  if (allowedPeriods.includes("Latest available")) return "Latest available";
  return allowedPeriods[allowedPeriods.length - 1] || "2020-2024";
}

export const MAX_SELECTIONS = 3;

export const DEFAULTS = {
  usa: { topic: "brain", period: "2020-2024", places: ["CA"] as readonly string[] },
  eurostat: {
    topic: "brain_waste_gap",
    period: "Latest available",
    places: ["DEU"] as readonly string[],
    sex: "Total",
    age: "From 15 to 64 years"
  }
} as const;

export type Region = "usa" | "eurostat";
