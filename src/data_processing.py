import pandas as pd
import os
from .config import (
    RAW_ACS_CSV, PROCESSED_ACS_PARQUET, 
    HIGHLY_EDUCATED_THRESHOLD, LOW_SKILL_OCC_THRESHOLD, IMMIGRANT_BPL_THRESHOLD,
    FIPS_TO_STATE
)

def generate_cleaned_parquet(force=False):
    """
    Processes the raw IPUMS ACS CSV in chunks and saves it as a cleaned Parquet file.
    Applies workforce proxy filters: positive income and valid occupation.
    """
    if not force and os.path.exists(PROCESSED_ACS_PARQUET):
        print(f"{PROCESSED_ACS_PARQUET} already exists. Use force=True to overwrite.")
        return PROCESSED_ACS_PARQUET

    print(f"Processing {RAW_ACS_CSV} into cleaned Parquet...")
    os.makedirs(os.path.dirname(PROCESSED_ACS_PARQUET), exist_ok=True)
    
    columns_to_keep = ['YEAR', 'STATEFIP', 'BPL', 'CITIZEN', 'EDUC', 'OCC', 'INCTOT', 'PERWT']
    chunks = []
    chunk_size = 1_000_000
    
    # Read in chunks to manage memory
    for i, chunk in enumerate(pd.read_csv(RAW_ACS_CSV, usecols=columns_to_keep, chunksize=chunk_size)):
        # Filter workforce proxy: Has occupation, has positive income (excluding 9999999 N/A code)
        filtered_chunk = chunk[
            (chunk['INCTOT'] > 0) & 
            (chunk['INCTOT'] < 9999999) & 
            (chunk['OCC'] > 0)
        ].copy()
        chunks.append(filtered_chunk)
        print(f"Processed chunk {i+1}")
    
    df_clean = pd.concat(chunks, ignore_index=True)
    
    # Apply feature engineering during processing to save time later
    df_clean['highly_educated'] = df_clean['EDUC'] >= HIGHLY_EDUCATED_THRESHOLD
    df_clean['low_skill_job'] = df_clean['OCC'] >= LOW_SKILL_OCC_THRESHOLD
    df_clean['is_brain_waste'] = df_clean['highly_educated'] & df_clean['low_skill_job']
    df_clean['is_immigrant'] = df_clean['BPL'] >= IMMIGRANT_BPL_THRESHOLD
    df_clean['state_name'] = df_clean['STATEFIP'].map(FIPS_TO_STATE)
    
    df_clean.to_parquet(PROCESSED_ACS_PARQUET, engine='pyarrow')
    print(f"Successfully saved {len(df_clean):,} rows to {PROCESSED_ACS_PARQUET}")
    return PROCESSED_ACS_PARQUET

def load_cleaned_data():
    """Loads the processed Parquet file."""
    if not os.path.exists(PROCESSED_ACS_PARQUET):
        generate_cleaned_parquet()
    return pd.read_parquet(PROCESSED_ACS_PARQUET)

def calculate_brain_waste_stats(df, top_states=None):
    """
    Calculates brain waste percentages grouped by state and immigrant status.
    """
    if top_states is None:
        top_states = ['California', 'Texas', 'New York', 'Florida', 'Illinois']
    
    # Filter for highly educated individuals
    educated_only = df[df['highly_educated']].copy()
    
    # Aggregate by state and immigrant status using person weights
    agg_df = educated_only.groupby(['state_name', 'is_immigrant']).apply(
        lambda x: pd.Series({
            'brain_waste_pct': (x[x['is_brain_waste']]['PERWT'].sum() / x['PERWT'].sum()) * 100,
            'total_pop': x['PERWT'].sum()
        }),
        include_groups=False
    ).reset_index()
    
    # Filter for selected states and add readable labels
    viz_df = agg_df[agg_df['state_name'].isin(top_states)].copy()
    viz_df['status'] = viz_df['is_immigrant'].map({True: 'Immigrant', False: 'Native'})
    
    return viz_df
