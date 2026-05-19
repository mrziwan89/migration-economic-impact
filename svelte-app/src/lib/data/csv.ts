export type CsvRow = Record<string, string | number | null>;

function coerceValue(key: string, value: string): string | number | null {
  if (value === "") {
    return null;
  }
  const numeric =
    key === "YEAR" ||
    key === "year_start" ||
    key === "year_end" ||
    key === "STATEFIP" ||
    key === "is_aggregate" ||
    key === "years_observed" ||
    key === "source_rows" ||
    key.includes("weighted_") ||
    key.includes("_value") ||
    key.includes("_rate") ||
    key.includes("_pct") ||
    key.includes("_gap") ||
    key.startsWith("gap_") ||
    key.startsWith("ratio_") ||
    key.includes("_per_100k");
  if (!numeric) {
    return value;
  }
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

export function parseCsv(text: string): CsvRow[] {
  const rows: string[][] = [];
  let row: string[] = [];
  let field = "";
  let inQuotes = false;

  for (let i = 0; i < text.length; i += 1) {
    const char = text[i];
    const next = text[i + 1];

    if (char === '"') {
      if (inQuotes && next === '"') {
        field += '"';
        i += 1;
      } else {
        inQuotes = !inQuotes;
      }
    } else if (char === "," && !inQuotes) {
      row.push(field);
      field = "";
    } else if ((char === "\n" || char === "\r") && !inQuotes) {
      if (char === "\r" && next === "\n") {
        i += 1;
      }
      row.push(field);
      if (row.some((value) => value !== "")) {
        rows.push(row);
      }
      row = [];
      field = "";
    } else {
      field += char;
    }
  }

  if (field.length || row.length) {
    row.push(field);
    if (row.some((value) => value !== "")) {
      rows.push(row);
    }
  }

  const headers = rows.shift() ?? [];
  return rows.map((values) => {
    const output: CsvRow = {};
    headers.forEach((header, index) => {
      output[header] = coerceValue(header, values[index] ?? "");
    });
    return output;
  });
}

export async function loadCsv(path: string): Promise<CsvRow[]> {
  const response = await fetch(path);
  if (!response.ok) {
    throw new Error(`Failed to load ${path}: ${response.status}`);
  }
  return parseCsv(await response.text());
}
