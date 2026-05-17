import csv

with open("../data/processed/eurostat_insights.csv", "r") as f:
    reader = csv.DictReader(f)
    countries = set()
    for row in reader:
        try:
            year = int(row["Year"])
            if 2014 <= year <= 2024:
                countries.add(row["Country"])
        except:
            pass
    print("Countries present in 2014-2024:")
    print(sorted(countries))
