export const USA_FILES = {
  brainGapPeriod: "/data/USA/brainwaste/brain_waste_gap_state_period.csv",
  brainYear: "/data/USA/brainwaste/brain_waste_state_year.csv",
  incGapPeriod: "/data/USA/incarceration/incarceration_gap_state_period.csv",
  incYear: "/data/USA/incarceration/incarceration_state_year.csv",
  healthGapPeriod: "/data/USA/healthcare/healthcare_gap_state_period.csv",
  healthYear: "/data/USA/healthcare/healthcare_state_year.csv",
  healthCitPeriod: "/data/USA/healthcare/healthcare_state_period_citizenship.csv",
  langPeriod: "/data/USA/language/language_state_period.csv",
  langYear: "/data/USA/language/language_state_year.csv"
} as const;

export const EUROSTAT_FILES = {
  countryYear: "/data/EU/employment/employment_country_year.csv",
  countryPeriod: "/data/EU/employment/employment_country_period.csv",
  gapYear: "/data/EU/employment/employment_gap_country_year.csv",
  gapPeriod: "/data/EU/employment/employment_gap_country_period.csv",
  outcomeYear: "/data/EU/outcomes/eu_outcomes_country_year.csv",
  outcomePeriod: "/data/EU/outcomes/eu_outcomes_country_period.csv",
  outcomeLatest: "/data/EU/outcomes/eu_outcomes_country_latest.csv"
} as const;

export type UsaFileKey = keyof typeof USA_FILES;
export type EurostatFileKey = keyof typeof EUROSTAT_FILES;
