import os

# Base directory for data
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
DATA_PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")

# Specific file paths
RAW_ACS_CSV = os.path.join(DATA_RAW_DIR, "ipums_acs", "usa_2014_plus.csv")
PROCESSED_ACS_PARQUET = os.path.join(DATA_PROCESSED_DIR, "acs_2014_cleaned.parquet")
FOUNDERS_STATS_CSV = os.path.join(DATA_RAW_DIR, "founders", "eu_tech_founders_stats.csv")

# State FIPS mappings
FIPS_TO_STATE = {
    1: 'Alabama', 2: 'Alaska', 4: 'Arizona', 5: 'Arkansas', 6: 'California', 
    8: 'Colorado', 9: 'Connecticut', 10: 'Delaware', 11: 'District of Columbia', 
    12: 'Florida', 13: 'Georgia', 15: 'Hawaii', 16: 'Idaho', 17: 'Illinois', 
    18: 'Indiana', 19: 'Iowa', 20: 'Kansas', 21: 'Kentucky', 22: 'Louisiana', 
    23: 'Maine', 24: 'Maryland', 25: 'Massachusetts', 26: 'Michigan', 27: 'Minnesota', 
    28: 'Mississippi', 29: 'Missouri', 30: 'Montana', 31: 'Nebraska', 32: 'Nevada', 
    33: 'New Hampshire', 34: 'New Jersey', 35: 'New Mexico', 36: 'New York', 
    37: 'North Carolina', 38: 'North Dakota', 39: 'Ohio', 40: 'Oklahoma', 41: 'Oregon', 
    42: 'Pennsylvania', 44: 'Rhode Island', 45: 'South Carolina', 46: 'South Dakota', 
    47: 'Tennessee', 48: 'Texas', 49: 'Utah', 50: 'Vermont', 51: 'Virginia', 
    53: 'Washington', 54: 'West Virginia', 55: 'Wisconsin', 56: 'Wyoming'
}

# Thresholds and criteria
HIGHLY_EDUCATED_THRESHOLD = 10  # Bachelor's or higher in IPUMS EDUC
LOW_SKILL_OCC_THRESHOLD = 3600  # Service/Labor in ACS 2010+
IMMIGRANT_BPL_THRESHOLD = 150   # Standard non-US-born threshold
