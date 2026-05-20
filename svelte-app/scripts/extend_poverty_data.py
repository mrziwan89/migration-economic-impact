#!/usr/bin/env python3
"""
Extend EU poverty risk data (2015-2024) by fetching Eurostat ilc_li32 dataset.

Reads the existing eu_outcomes_country_year.csv / period file,
fetches fresh data from the Eurostat SDMX REST API,
and appends rows for the "poverty" metric for years missing in the current file.
"""
import csv
import io
import json
import os
import re
import sys
import urllib.request

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "..", "static", "data", "EU", "outcomes")
YEAR_FILE = os.path.join(DATA_DIR, "eu_outcomes_country_year.csv")
PERIOD_FILE = os.path.join(DATA_DIR, "eu_outcomes_country_period.csv")

# Country code (2-letter) -> iso3 mapping used in the project
CC_TO_ISO3 = {
    "AT": "AUT", "BE": "BEL", "BG": "BGR", "CH": "CHE", "CY": "CYP",
    "CZ": "CZE", "DE": "DEU", "DK": "DNK", "EE": "EST", "EL": "GRC",
    "ES": "ESP", "FI": "FIN", "FR": "FRA", "HR": "HRV", "HU": "HUN",
    "IE": "IRL", "IS": "ISL", "IT": "ITA", "LT": "LTU", "LU": "LUX",
    "LV": "LVA", "MK": "MKD", "MT": "MLT", "NL": "NLD", "NO": "NOR",
    "PL": "POL", "PT": "PRT", "RO": "ROU", "SE": "SWE", "SI": "SVN",
    "SK": "SVK", "RS": "SRB", "ME": "MNE", "AL": "ALB", "BA": "BIH",
    "TR": "TUR", "XK": "XKX", "GB": "GBR", "UK": "GBR", "LI": "LIE",
}

ISO3_TO_NAME = {
    "AUT": "Austria", "BEL": "Belgium", "BGR": "Bulgaria", "CHE": "Switzerland",
    "CYP": "Cyprus", "CZE": "Czechia", "DEU": "Germany", "DNK": "Denmark",
    "EST": "Estonia", "GRC": "Greece", "ESP": "Spain", "FIN": "Finland",
    "FRA": "France", "HRV": "Croatia", "HUN": "Hungary", "IRL": "Ireland",
    "ISL": "Iceland", "ITA": "Italy", "LTU": "Lithuania", "LUX": "Luxembourg",
    "LVA": "Latvia", "MKD": "North Macedonia", "MLT": "Malta", "NLD": "Netherlands",
    "NOR": "Norway", "POL": "Poland", "PRT": "Portugal", "ROU": "Romania",
    "SWE": "Sweden", "SVN": "Slovenia", "SVK": "Slovakia", "SRB": "Serbia",
    "MNE": "Montenegro", "ALB": "Albania", "BIH": "Bosnia and Herzegovina",
    "TUR": "Turkey", "XKX": "Kosovo", "GBR": "United Kingdom", "LIE": "Liechtenstein",
}

AGGREGATES = {"EU27_2020", "EA20", "EA21", "EU28", "EA19", "EA21_2026", "EU"}

PERIOD_MAP = {
    range(1995, 2008): "1995-2007",
    range(2008, 2014): "2008-2013",
    range(2014, 2020): "2014-2019",
    range(2020, 2026): "2020-2024",
}

def year_to_period(y: int) -> str:
    for rng, label in PERIOD_MAP.items():
        if y in rng:
            return label
    return "2020-2024"


def fetch_eurostat_tsv(url: str) -> str:
    """Fetch TSV data from Eurostat API."""
    print(f"  Fetching: {url[:120]}...")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read()
    return raw.decode("utf-8", errors="replace")


def parse_eurostat_tsv(tsv_text: str):
    """
    Parse Eurostat TSV format into {(c_birth, geo): {year: value}}.
    Lines look like:
      A,MED_EI,B_60,NAT,TOTAL,T,PC,AT\t13.3 \t12.9 \t...
    Header:
      freq,statinfo,rskpovth,c_birth,age,sex,unit,geo\TIME_PERIOD\t2015 \t2016 ...
    """
    lines = tsv_text.strip().split("\n")
    if not lines:
        return {}, []

    # Parse header to get years
    header_line = lines[0].replace("\r", "")
    header_parts = header_line.split("\t")
    years = []
    for part in header_parts[1:]:
        part = part.strip()
        if part.isdigit():
            years.append(int(part))

    data = {}  # (c_birth, geo_cc) -> {year: float}
    for line in lines[1:]:
        line = line.replace("\r", "")
        parts = line.split("\t")
        if len(parts) < 2:
            continue

        dims = parts[0].split(",")
        if len(dims) < 8:
            continue

        c_birth = dims[3].strip()
        sex = dims[5].strip()
        geo = dims[7].strip()

        # Only total sex
        if sex != "T":
            continue
        # Only age TOTAL
        age = dims[4].strip()
        if age != "TOTAL":
            continue

        key = (c_birth, geo)
        if key not in data:
            data[key] = {}

        for i, val_str in enumerate(parts[1:]):
            if i >= len(years):
                break
            val_str = val_str.strip()
            # Remove flags like 'u', 'p', 'b', 'e', 'd'
            val_clean = re.sub(r'[a-z ]', '', val_str)
            if val_clean == ":" or val_clean == "":
                continue
            try:
                data[key][years[i]] = float(val_clean)
            except ValueError:
                continue

    return data, years


def main():
    print("=== Extending EU Poverty Risk Data ===\n")

    # 1. Read existing year file to find which poverty rows already exist
    existing_poverty_years = set()  # (iso3, year) pairs
    existing_rows = []
    with open(YEAR_FILE, "r", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            existing_rows.append(row)
            if row.get("metric_key") == "poverty":
                iso3 = row.get("iso3", "")
                year = row.get("YEAR", "")
                if iso3 and year:
                    existing_poverty_years.add((iso3, int(year)))

    print(f"  Existing poverty data points: {len(existing_poverty_years)}")
    if existing_poverty_years:
        years_found = sorted(set(y for _, y in existing_poverty_years))
        print(f"  Year range: {min(years_found)}-{max(years_found)}")

    # 2. Fetch Eurostat ilc_li32 data
    # NAT = native-born, EU27_2020_FOR = born outside EU27
    url = (
        "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/ilc_li32"
        "?format=TSV"
        "&c_birth=NAT,EU27_2020_FOR"
        "&age=TOTAL"
        "&sex=T"
        "&unit=PC"
        "&sinceTimePeriod=2008"
        "&untilTimePeriod=2025"
    )
    tsv_text = fetch_eurostat_tsv(url)
    data, api_years = parse_eurostat_tsv(tsv_text)
    print(f"  API returned {len(data)} dimension combinations, years: {api_years}")

    # 3. Build rows for missing years
    # Group by geo to get native + foreign for each country
    geos = set()
    for (c_birth, geo) in data:
        if geo not in AGGREGATES:
            geos.add(geo)

    new_rows = []
    for geo in sorted(geos):
        iso3 = CC_TO_ISO3.get(geo)
        if not iso3:
            continue
        country_name = ISO3_TO_NAME.get(iso3, geo)
        cc = geo  # 2-letter country code

        native_data = data.get(("NAT", geo), {})
        foreign_data = data.get(("EU27_2020_FOR", geo), {})

        for year in sorted(set(list(native_data.keys()) + list(foreign_data.keys()))):
            if (iso3, year) in existing_poverty_years:
                continue  # Already have this data point

            native_val = native_data.get(year)
            foreign_val = foreign_data.get(year)

            # Need at least native value to include
            if native_val is None:
                continue

            gap = None
            if native_val is not None and foreign_val is not None:
                gap = round(foreign_val - native_val, 2)

            period = year_to_period(year)

            new_row = {
                "YEAR": str(year),
                "period": period,
                "country": country_name,
                "country_code": cc,
                "country_key": iso3,
                "iso3": iso3,
                "is_aggregate": "0",
                "metric_key": "poverty",
                "metric_label": "Poverty risk rate",
                "unit": "percentage points",
                "native_value": str(round(native_val, 2)) if native_val is not None else "",
                "eu_migrant_value": "",
                "extra_eu_migrant_value": str(round(foreign_val, 2)) if foreign_val is not None else "",
                "gap_extra_eu_vs_native_pp": str(gap) if gap is not None else "",
                "ratio_foreign_vs_native": "",
            }
            new_rows.append(new_row)

    print(f"\n  New poverty rows to add: {len(new_rows)}")
    if new_rows:
        new_years = sorted(set(int(r["YEAR"]) for r in new_rows))
        print(f"  New year range: {min(new_years)}-{max(new_years)}")
        countries_covered = sorted(set(r["iso3"] for r in new_rows))
        print(f"  Countries: {len(countries_covered)} ({', '.join(countries_covered[:10])}...)")

    # 4. Append to year file
    if new_rows:
        all_rows = existing_rows + new_rows
        # Sort by metric_key, YEAR, country_key
        all_rows.sort(key=lambda r: (r.get("metric_key", ""), int(r.get("YEAR", 0)), r.get("country_key", "")))

        with open(YEAR_FILE, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_rows)
        print(f"\n  ✅ Updated {YEAR_FILE}")

    # 5. Rebuild period file from year data
    print("\n  Rebuilding period aggregations...")
    period_data = {}  # (period, iso3, metric_key) -> lists of values
    with open(YEAR_FILE, "r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            period = row.get("period", "")
            iso3 = row.get("iso3", "")
            metric = row.get("metric_key", "")
            if not period or not iso3 or not metric:
                continue

            key = (period, iso3, metric)
            if key not in period_data:
                period_data[key] = {
                    "period": period,
                    "country": row["country"],
                    "country_code": row["country_code"],
                    "country_key": iso3,
                    "iso3": iso3,
                    "is_aggregate": row["is_aggregate"],
                    "metric_key": metric,
                    "metric_label": row["metric_label"],
                    "unit": row["unit"],
                    "native_values": [],
                    "eu_values": [],
                    "extra_eu_values": [],
                    "gap_values": [],
                    "ratio_values": [],
                }
            entry = period_data[key]

            def safe_float(s):
                try:
                    return float(s) if s else None
                except ValueError:
                    return None

            nv = safe_float(row.get("native_value", ""))
            ev = safe_float(row.get("eu_migrant_value", ""))
            xv = safe_float(row.get("extra_eu_migrant_value", ""))
            gv = safe_float(row.get("gap_extra_eu_vs_native_pp", ""))
            rv = safe_float(row.get("ratio_foreign_vs_native", ""))

            if nv is not None: entry["native_values"].append(nv)
            if ev is not None: entry["eu_values"].append(ev)
            if xv is not None: entry["extra_eu_values"].append(xv)
            if gv is not None: entry["gap_values"].append(gv)
            if rv is not None: entry["ratio_values"].append(rv)

    def avg(lst):
        return round(sum(lst) / len(lst), 2) if lst else None

    # Compute year_start, year_end from period label
    def period_years(p):
        parts = p.split("-")
        if len(parts) == 2:
            return parts[0], parts[1]
        return p, p

    period_rows = []
    period_fieldnames = [
        "period", "year_start", "year_end", "country", "country_code",
        "country_key", "iso3", "is_aggregate", "metric_key", "metric_label",
        "unit", "years_observed", "native_value", "eu_migrant_value",
        "extra_eu_migrant_value", "gap_extra_eu_vs_native_pp", "ratio_foreign_vs_native"
    ]

    for key, entry in sorted(period_data.items()):
        ys, ye = period_years(entry["period"])
        n_years = max(len(entry["native_values"]), len(entry["extra_eu_values"]), 1)
        row = {
            "period": entry["period"],
            "year_start": ys,
            "year_end": ye,
            "country": entry["country"],
            "country_code": entry["country_code"],
            "country_key": entry["country_key"],
            "iso3": entry["iso3"],
            "is_aggregate": entry["is_aggregate"],
            "metric_key": entry["metric_key"],
            "metric_label": entry["metric_label"],
            "unit": entry["unit"],
            "years_observed": str(n_years),
            "native_value": str(avg(entry["native_values"])) if entry["native_values"] else "",
            "eu_migrant_value": str(avg(entry["eu_values"])) if entry["eu_values"] else "",
            "extra_eu_migrant_value": str(avg(entry["extra_eu_values"])) if entry["extra_eu_values"] else "",
            "gap_extra_eu_vs_native_pp": str(avg(entry["gap_values"])) if entry["gap_values"] else "",
            "ratio_foreign_vs_native": str(avg(entry["ratio_values"])) if entry["ratio_values"] else "",
        }
        period_rows.append(row)

    with open(PERIOD_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=period_fieldnames)
        writer.writeheader()
        writer.writerows(period_rows)
    print(f"  ✅ Updated {PERIOD_FILE}")

    # Summary
    poverty_years_after = set()
    with open(YEAR_FILE, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("metric_key") == "poverty":
                poverty_years_after.add(int(row["YEAR"]))

    print(f"\n=== Done! Poverty data now covers: {min(poverty_years_after)}-{max(poverty_years_after)} ({len(poverty_years_after)} years) ===")


if __name__ == "__main__":
    main()
