import { USA_FILES, EUROSTAT_FILES, type UsaFileKey, type EurostatFileKey } from "./files";
import { FIPS_TO_STATE, STATE_NAMES } from "./lookups";
import { loadCsv, type CsvRow } from "./csv";

export type LoadedData = {
  usa: Record<UsaFileKey, CsvRow[]>;
  eurostat: Record<EurostatFileKey, CsvRow[]>;
};

function decorateUsaRow(row: CsvRow): void {
  if (row.state == null && row.STATEFIP != null) {
    const fips = Number(row.STATEFIP);
    if (Number.isFinite(fips) && FIPS_TO_STATE[fips]) {
      row.state = FIPS_TO_STATE[fips];
    }
  }
  if (row.state_name == null && typeof row.state === "string") {
    const name = STATE_NAMES[row.state];
    if (name) {
      row.state_name = name;
    }
  }
}

export async function loadAllData(): Promise<LoadedData> {
  const usa = {} as Record<UsaFileKey, CsvRow[]>;
  const eurostat = {} as Record<EurostatFileKey, CsvRow[]>;

  await Promise.all(
    (Object.entries(USA_FILES) as [UsaFileKey, string][]).map(async ([key, path]) => {
      usa[key] = await loadCsv(path);
    })
  );
  await Promise.all(
    (Object.entries(EUROSTAT_FILES) as [EurostatFileKey, string][]).map(async ([key, path]) => {
      eurostat[key] = await loadCsv(path);
    })
  );

  Object.values(usa).forEach((rows) => rows.forEach(decorateUsaRow));

  return { usa, eurostat };
}
