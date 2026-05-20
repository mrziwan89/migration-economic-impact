import pandas as pd
import nbformat as nbf

# Define the URL
url = "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/ilc_peps05n?format=SDMX-CSV&citizen=NEU27_2020_FOR&citizen=NAT&citizen=EU27_2020_FOR&age=Y_GE18&sex=T&unit=PC&compressed=false"

# Add a cell to test connectivity in the notebook
nb_path = "/Users/razormac/Desktop/Work/Information Visualization/The Project/notebooks/test.ipynb"
with open(nb_path, "r", encoding="utf-8") as f:
    nb = nbf.read(f, as_version=4)

test_cell_code = f"""
import pandas as pd
import requests

url = "{url}"
print("Testing connectivity to Eurostat...")
try:
    # Try reading just the first 5 lines to check connectivity
    df_test = pd.read_csv(url, nrows=5)
    print("Success! Notebook can reach Eurostat.")
    print(df_test.head())
except Exception as e:
    print(f"Failed to reach Eurostat from notebook: {{e}}")
"""

nb.cells.append(nbf.v4.new_code_cell(test_cell_code))

with open(nb_path, "w", encoding="utf-8") as f:
    nbf.write(nb, f)

print("Test cell added to notebooks/test.ipynb")
