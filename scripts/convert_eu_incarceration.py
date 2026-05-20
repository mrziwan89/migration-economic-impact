"""
convert_eu_incarceration.py
Converts the EU incarceration unit in all three eu_outcomes_country_*.csv
files from "ratio" to "%". The foreign-citizen share of the prison population
is already stored in extra_eu_migrant_value (0-100 scale), so only the unit
label needs to change for the front-end to render it as a percentage.

Updates both copies of each CSV (svelte-app/static/data/EU and website/data/EU).
Idempotent: re-running after conversion is a no-op.

Run with:  python scripts/convert_eu_incarceration.py
"""
import csv
import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA_DIRS = [
    REPO_ROOT / "svelte-app" / "static" / "data" / "EU" / "outcomes",
    REPO_ROOT / "website" / "data" / "EU" / "outcomes",
]
FILES = [
    "eu_outcomes_country_latest.csv",
    "eu_outcomes_country_period.csv",
    "eu_outcomes_country_year.csv",
]


def convert(path: pathlib.Path) -> int:
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    updated = 0
    for row in rows:
        if row.get("metric_key") == "incarceration" and row.get("unit") == "ratio":
            row["unit"] = "%"
            updated += 1

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return updated


def main() -> None:
    for data_dir in DATA_DIRS:
        for filename in FILES:
            path = data_dir / filename
            if not path.exists():
                print(f"SKIP  {path} (not found)")
                continue
            n = convert(path)
            print(f"{path}  ->  {n} rows updated")


if __name__ == "__main__":
    main()
