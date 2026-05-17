import sys
import os

# Add the current directory to the path so we can import from src
sys.path.append(os.path.abspath("."))

from src.data_processing import generate_cleaned_parquet

if __name__ == "__main__":
    print("Starting preprocessing of IPUMS ACS data...")
    try:
        output_path = generate_cleaned_parquet(force=True)
        print(f"Preprocessing complete! Cleaned data saved to: {output_path}")
    except Exception as e:
        print(f"An error occurred during preprocessing: {e}")
        sys.exit(1)
