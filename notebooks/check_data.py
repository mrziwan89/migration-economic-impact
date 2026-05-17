import pandas as pd
df = pd.read_csv("../data/processed/eurostat_insights.csv")
df = df[(df["Year"] >= 2014) & (df["Year"] <= 2024)]
print(df.groupby("Country").size())
print(df[["Country", "Gap_ExtraEU_vs_Native_PP", "Metric"]].dropna().head(10))
