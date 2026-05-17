import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import os
from .config import FOUNDERS_STATS_CSV

def plot_brain_waste_comparison(viz_df, states_order=None):
    """
    Plots a bar chart comparing brain waste between immigrants and natives.
    """
    if states_order is None:
        states_order = ['California', 'Texas', 'New York', 'Florida', 'Illinois']
        
    sns.set_theme(style="whitegrid", palette="muted")
    plt.figure(figsize=(12, 6))
    
    ax = sns.barplot(
        data=viz_df, 
        x='state_name', 
        y='brain_waste_pct', 
        hue='status',
        order=states_order
    )

    plt.title('Brain Waste Comparison: Immigrants vs. Native-Born (Top States)', fontsize=15)
    plt.ylabel('Percentage of Highly Educated in Low-Skill Jobs (%)')
    plt.xlabel('State')
    plt.legend(title='Status')

    # Add percentage labels on top of bars
    for container in ax.containers:
        ax.bar_label(container, fmt='%.1f%%', padding=3)

    sns.despine()
    plt.tight_layout()
    plt.show()

def plot_innovation_dividend():
    """
    Plots the innovation dividend using tech founder statistics.
    """
    if not os.path.exists(FOUNDERS_STATS_CSV):
        print(f"Founders data not found at {FOUNDERS_STATS_CSV}")
        return

    founders_df = pd.read_csv(FOUNDERS_STATS_CSV)
    
    # Clean and filter for percentage metrics
    percent_df = founders_df[founders_df['unit'] == 'percent'].copy()
    percent_df['metric_clean'] = percent_df['metric'].str.replace('_', ' ').str.title()
    percent_df['label'] = percent_df['country_or_region'] + \" - \" + percent_df['metric_clean']
    percent_df = percent_df.sort_values(by='value', ascending=True)

    plt.figure(figsize=(12, 7))
    ax_f = sns.barplot(
        data=percent_df,
        x='value',
        y='label',
        color='#2ca02c' # Green for \"Dividend\"
    )
    
    plt.title('The Innovation Dividend:\\nImmigrant Contributions to Tech & Entrepreneurship')
    plt.xlabel('Percentage (%)')
    plt.ylabel('')
    plt.xlim(0, 100)
    
    for container in ax_f.containers:
        ax_f.bar_label(container, fmt='%.0f%%', padding=5)
    
    sns.despine(left=True)
    plt.tight_layout()
    plt.show()
