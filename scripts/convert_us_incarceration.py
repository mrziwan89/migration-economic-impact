"""
convert_us_incarceration.py
Converts the four US incarceration CSVs from per-100,000 to percentage:

  Rate files (incarceration_state_year.csv, incarceration_state_period.csv):
    - rename `incarceration_rate_per_100k` -> `incarceration_rate_pct`
    - divide each value by 1000  (1142.66 per 100k -> 1.14266%)

  Gap files (incarceration_gap_state_year.csv, incarceration_gap_state_period.csv):
    - rename `incarceration_rate_per_100k_gap_foreign_minus_us`
             -> `incarceration_rate_pct_gap_foreign_minus_us`
    - divide each value (and the `Foreign-born`/`US-born` rate columns) by 1000

Updates both copies of each CSV (svelte-app/static/data/USA and website/data/USA).
Idempotent: re-running after conversion is a no-op for any file already converted.

Run with:  python scripts/convert_us_incarceration.py
"""
import csv
import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA_DIRS = [
    REPO_ROOT / "svelte-app" / "static" / "data" / "USA" / "incarceration",
    REPO_ROOT / "website" / "data" / "USA" / "incarceration",
]

# (filename, [(old_column, new_column), ...], [column_to_rescale_in_place, ...])
JOBS = [
    (
        "incarceration_state_year.csv",
        [("incarceration_rate_per_100k", "incarceration_rate_pct")],
        [],
    ),
    (
        "incarceration_state_period.csv",
        [("incarceration_rate_per_100k", "incarceration_rate_pct")],
        [],
    ),
    (
        "incarceration_gap_state_year.csv",
        [(
            "incarceration_rate_per_100k_gap_foreign_minus_us",
            "incarceration_rate_pct_gap_foreign_minus_us",
        )],
        ["Foreign-born", "US-born"],
    ),
    (
        "incarceration_gap_state_period.csv",
        [(
            "incarceration_rate_per_100k_gap_foreign_minus_us",
            "incarceration_rate_pct_gap_foreign_minus_us",
        )],
        ["Foreign-born", "US-born"],
    ),
]


def divide_by_1000(value: str) -> str | float:
    if value is None or value == "":
        return ""
    return float(value) / 1000.0


def convert(path: pathlib.Path, renames: list, rescale_in_place: list) -> int:
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    pending_renames = [(old, new) for old, new in renames if old in fieldnames]
    if not pending_renames:
        return 0  # already converted

    name_map = {old: new for old, new in pending_renames}
    fieldnames = [name_map.get(name, name) for name in fieldnames]

    updated = 0
    for row in rows:
        for old, new in pending_renames:
            row[new] = divide_by_1000(row.pop(old, ""))
        for col in rescale_in_place:
            if col in row:
                row[col] = divide_by_1000(row[col])
        updated += 1

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return updated


def main() -> None:
    for data_dir in DATA_DIRS:
        for filename, renames, rescale_in_place in JOBS:
            path = data_dir / filename
            if not path.exists():
                print(f"SKIP  {path} (not found)")
                continue
            n = convert(path, renames, rescale_in_place)
            print(f"{path}  ->  {n} rows updated")


if __name__ == "__main__":
    main()
