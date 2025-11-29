import pandas as pd
import numpy as np

# ==========================================
# 1. DEFINE INPUTS AND CONFIGURATION
# ==========================================

# A. The Raw Metric Scores (Aggregated Poll Data)
# NOTE: 'ES_Healthcare' is REMOVED. 
# NOTE: 'ES_Occupation' is NOT here because it is not polled.
raw_poll_scores = {
    'ES_IncPovEmp': 248,      # Economic Security: Income, Poverty
    'Education': 165,         # Education
    'LA_Transportation': 166, # Location Affordability: Transportation
    'LA_Housing': 135,        # Location Affordability: Housing
    'Cultural_Race': 122      # Cultural: Race/Civil Rights
}

# B. The Groupings and Type Configuration
# 'Fixed': Weight is hardcoded (0.125). 
# 'Polled': Weight is calculated dynamically based on raw_poll_scores.
metric_config = {
    'Economic Security': {
        'ES_IncPovEmp': {'type': 'Polled'},
        'ES_Occupation': {'type': 'Fixed', 'value': 0.125} # Locked at 12.5% (0 Tilt)
    },
    'Education': {
        'Education': {'type': 'Polled'}
    },
    'Location Affordability': {
        'LA_Transportation': {'type': 'Polled'},
        'LA_Housing': {'type': 'Polled'}
    },
    'Cultural - Race': {
        'Cultural_Race': {'type': 'Polled'}
    }
}

GROUP_BASELINE = 0.25 # 25% Baseline for each of the 4 groups

# ==========================================
# 2. PERFORM CALCULATIONS
# ==========================================

# Step A: Determine the "Available Weight" for polled items
# We sum up all 'Fixed' weights to see what is left for the polled items.
total_fixed_weight = sum(m['value'] for g in metric_config.values() for m in g.values() if m['type'] == 'Fixed')
available_poll_weight = 1.0 - total_fixed_weight # Should be 0.875 (87.5%)

# Step B: Sum the raw scores of the polled items
grand_total_poll_score = sum(raw_poll_scores.values())

results = []

# Step C: Iterate through groups to calculate weights and tilts
for group, metrics in metric_config.items():
    
    # --- Phase 1: Calculate Final Weights first (Hybrid Approach) ---
    group_final_weight_sum = 0
    temp_metric_data = []
    
    for metric_name, config in metrics.items():
        if config['type'] == 'Fixed':
            # It gets its fixed value exactly
            final_metric_weight = config['value']
        else:
            # It gets a share of the remaining 87.5% based on popularity
            raw_share = raw_poll_scores[metric_name] / grand_total_poll_score
            final_metric_weight = raw_share * available_poll_weight
        
        group_final_weight_sum += final_metric_weight
        temp_metric_data.append((metric_name, final_metric_weight))

    # --- Phase 2: Reverse-Engineer the Tilts for Reporting ---
    
    # 1. Group Calculations
    # How far is the calculated group weight from the 0.25 baseline?
    group_tilt = group_final_weight_sum - GROUP_BASELINE
    
    # 2. Sub-Metric Calculations
    num_sub_metrics = len(metrics)
    internal_baseline = 1.0 / num_sub_metrics # e.g., 0.50 for EconSec, 1.0 for Education
    
    for metric_name, final_metric_weight in temp_metric_data:
        
        # Calculate Internal Weight (How much of the Group does this metric take up?)
        # Formula: Metric Weight / Total Group Weight
        internal_weight_actual = final_metric_weight / group_final_weight_sum
        
        # Calculate Internal Tilt
        internal_tilt = internal_weight_actual - internal_baseline
        
        results.append({
            'Group': group,
            'Sub-Indicator': metric_name,
            'Group Baseline': GROUP_BASELINE * 100,
            'Group Tilt (%)': group_tilt * 100,
            'New Group Weight (%)': group_final_weight_sum * 100,
            'Sub-Indicator Baseline (Internal)': internal_baseline * 100,
            'Sub-Indicator Tilt (Internal, %)': internal_tilt * 100,
            'New Sub-Indicator Weight (Internal, %)': internal_weight_actual * 100,
            'Final Metric Weight (%)': final_metric_weight * 100
        })

# ==========================================
# 3. FORMATTING AND EXPORT
# ==========================================

df_results = pd.DataFrame(results)

# Clean up names
df_results['Sub-Indicator'] = df_results['Sub-Indicator'].replace({
    'ES_IncPovEmp': 'Income/Poverty/Employment',
    'ES_Occupation': 'Occupation (Fixed)',
    'LA_Transportation': 'Transportation costs',
    'LA_Housing': 'Housing costs',
    'Cultural_Race': 'Cultural - Race',
    'Education': 'Education'
})

# Reorder columns to match original script
column_order = [
    'Group', 'Sub-Indicator', 'Group Baseline', 'Group Tilt (%)', 'New Group Weight (%)',
    'Sub-Indicator Baseline (Internal)', 'Sub-Indicator Tilt (Internal, %)', 
    'New Sub-Indicator Weight (Internal, %)', 'Final Metric Weight (%)'
]
df_results = df_results[column_order]

# Sort by Group
group_order = ['Economic Security', 'Education', 'Location Affordability', 'Cultural - Race']
df_results['Group_Sort'] = df_results['Group'].astype('category').cat.set_categories(group_order, ordered=True)
df_results = df_results.sort_values(by=['Group_Sort', 'Sub-Indicator']).drop(columns=['Group_Sort'])

# --- OUTPUT TO CSV ---
csv_filename = 'metric_weights_and_tilts_final.csv'
df_results.to_csv(csv_filename, index=False)

# --- OUTPUT TO TXT ---
txt_content = df_results.to_string(index=False)
txt_filename = 'metric_weights_and_tilts.txt'

with open(txt_filename, 'w') as f:
    f.write("Final Metric Weighting (Hybrid: Fixed Occupation + Polled Others)\n")
    f.write("=================================================================\n\n")
    f.write(txt_content)

print(f"Success! Files created: {csv_filename} and {txt_filename}")
print("\n--- Preview of Final Weights ---\n")
print(txt_content)