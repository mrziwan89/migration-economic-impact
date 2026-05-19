import type { UsaFileKey, EurostatFileKey } from "./files";

export interface UsaTopic {
  label: string;
  title: string;
  units: string;
  mapKey: UsaFileKey;
  trendKey: UsaFileKey;
  value: string;
  trendValue: string;
  foreign?: string;
  us?: string;
  isGap: boolean;
  note: string;
}

export interface EurostatTopic {
  label: string;
  title: string;
  source: "outcomes" | "employment";
  units: string;
  note: string;
  isGap?: boolean;
  metricKey?: string;
  value: string;
  componentUnit?: string;
  rankDirection?: "ascending" | "descending";
  reversescale?: boolean;
  colorscale?: string;
  periods: string[];
  usesDemographicFilters?: boolean;
  kind?: "gap" | "rate";
  comparisonGroup?: string;
  citizenGroup?: string;
}

export const USA_TOPICS: Record<string, UsaTopic> = {
  brain: {
    label: "Brain waste gap",
    title: "Brain waste gap",
    units: "percentage points",
    mapKey: "brainGapPeriod",
    trendKey: "brainYear",
    value: "brain_waste_rate_pct_gap_foreign_minus_us",
    trendValue: "brain_waste_rate_pct",
    foreign: "Foreign-born",
    us: "US-born",
    isGap: true,
    note: "Highly educated employed adults aged 25-64 whose occupation is outside selected high-skill SOC major groups."
  },
  inc: {
    label: "Incarceration proxy gap",
    title: "Incarceration proxy gap",
    units: "per 100,000",
    mapKey: "incGapPeriod",
    trendKey: "incYear",
    value: "incarceration_rate_per_100k_gap_foreign_minus_us",
    trendValue: "incarceration_rate_per_100k",
    foreign: "Foreign-born",
    us: "US-born",
    isGap: true,
    note: "Men aged 18-40. ACS institutionalization is used as an incarceration proxy, not a direct crime rate."
  },
  health: {
    label: "Uninsured gap",
    title: "Uninsured gap",
    units: "percentage points",
    mapKey: "healthGapPeriod",
    trendKey: "healthYear",
    value: "uninsured_rate_pct_gap_foreign_minus_us",
    trendValue: "uninsured_rate_pct",
    foreign: "Foreign-born",
    us: "US-born",
    isGap: true,
    note: "Descriptive comparison of health-insurance access by nativity group."
  },
  lang: {
    label: "Limited English proficiency",
    title: "Limited English proficiency",
    units: "%",
    mapKey: "langPeriod",
    trendKey: "langYear",
    value: "limited_english_rate_pct",
    trendValue: "limited_english_rate_pct",
    isGap: false,
    note: "Foreign-born residents aged 5+ who speak English less than very well."
  }
};

export const EUROSTAT_TOPICS: Record<string, EurostatTopic> = {
  brain_waste_gap: {
    label: "Highly educated employment gap",
    title: "Highly educated employment gap",
    source: "outcomes",
    metricKey: "brain_waste",
    value: "gap_extra_eu_vs_native_pp",
    units: "percentage points",
    componentUnit: "%",
    isGap: true,
    rankDirection: "ascending",
    reversescale: false,
    periods: ["Latest available", "2020-2024", "2014-2019", "2008-2013", "1995-2007"],
    note: "Extra-EU migrants minus native-born residents. Negative gaps mean highly educated extra-EU migrants have lower employment rates."
  },
  temporary_contract_gap: {
    label: "Temporary contract gap",
    title: "Temporary contract gap",
    source: "outcomes",
    metricKey: "temporary_contract",
    value: "gap_extra_eu_vs_native_pp",
    units: "percentage points",
    componentUnit: "%",
    isGap: true,
    rankDirection: "descending",
    reversescale: true,
    periods: ["Latest available", "2020-2024", "2014-2019", "2008-2013", "1995-2007"],
    note: "Extra-EU migrants minus native-born residents. Positive gaps mean extra-EU migrants are more often in temporary contracts."
  },
  poverty_gap: {
    label: "Poverty risk gap",
    title: "Poverty risk gap",
    source: "outcomes",
    metricKey: "poverty",
    value: "gap_extra_eu_vs_native_pp",
    units: "percentage points",
    componentUnit: "%",
    isGap: true,
    rankDirection: "descending",
    reversescale: true,
    periods: ["Latest available", "2014-2019", "2008-2013", "1995-2007"],
    note: "Extra-EU migrants minus native-born residents. Poverty visual rows are capped at 2014 because later rows in this processed file mix rates and counts."
  },
  incarceration_ratio: {
    label: "Foreign prison representation",
    title: "Foreign prison representation",
    source: "outcomes",
    metricKey: "incarceration",
    value: "ratio_foreign_vs_native",
    units: "ratio",
    componentUnit: "%",
    isGap: false,
    rankDirection: "descending",
    colorscale: "YlOrRd",
    periods: ["Latest available", "2020-2024", "2014-2019", "2008-2013"],
    note: "Foreign-to-national prison-population representation ratio. Values above 1 mean foreign citizens are over-represented in the prison-population count."
  },
  foreign_gap: {
    label: "Foreign-country employment gap",
    title: "Foreign-country employment gap",
    source: "employment",
    usesDemographicFilters: true,
    kind: "gap",
    comparisonGroup: "foreign_country",
    value: "employment_rate_gap_pp",
    units: "percentage points",
    periods: ["2014-2019", "2020-2024"],
    note: "Employment rate of foreign-country citizens minus reporting-country citizens in the same country."
  },
  non_eu_gap: {
    label: "Non-EU employment gap",
    title: "Non-EU employment gap",
    source: "employment",
    usesDemographicFilters: true,
    kind: "gap",
    comparisonGroup: "non_eu",
    value: "employment_rate_gap_pp",
    units: "percentage points",
    periods: ["2014-2019", "2020-2024"],
    note: "Employment rate of non-EU27 citizens minus reporting-country citizens."
  },
  eu_mobile_gap: {
    label: "EU-mobile employment gap",
    title: "EU-mobile employment gap",
    source: "employment",
    usesDemographicFilters: true,
    kind: "gap",
    comparisonGroup: "eu_mobile",
    value: "employment_rate_gap_pp",
    units: "percentage points",
    periods: ["2014-2019", "2020-2024"],
    note: "Employment rate of EU27 citizens living outside their reporting country minus reporting-country citizens."
  },
  foreign_rate: {
    label: "Foreign-country employment rate",
    title: "Foreign-country employment rate",
    source: "employment",
    usesDemographicFilters: true,
    kind: "rate",
    citizenGroup: "foreign_country",
    value: "employment_rate_pct",
    units: "%",
    periods: ["2014-2019", "2020-2024"],
    note: "Eurostat LFS employment rate for foreign-country citizens."
  }
};
