import pandas as pd
import numpy as np

# 1. Define the raw metric scores based on the aggregated poll data (Total Score).
# These are manually aggregated from the High Point University poll data.
raw_scores = {
    'ES_IncPovEmp': 248,     # Economic Security: Income, Poverty, Employment (Combined)
    'ES_Healthcare': 163,    # Economic Security: Healthcare costs
    'Education': 165,        # Education
    'LA_Transportation': 166, # Location Affordability: Transportation costs
    'LA_Housing': 135,       # Location Affordability: Housing costs (using Taxes/Inflation as proxy)
    'Cultural_Race': 122     # Cultural: Race/Civil Rights
}

# Define the groupings and baselines for the calculations
group_metrics = {
    'Economic Security': ['ES_IncPovEmp', 'ES_Healthcare'],
    'Education': ['Education'],
    'Location Affordability': ['LA_Transportation', 'LA_Housing'],
    'Cultural - Race': ['Cultural_Race']
}

GROUP_BASELINE = 0.25 # 25% for each of the 4 groups (0.25)

# 2. Calculate the Group Tilts and New Group Weights
group_data = {}
grand_total_score = sum(raw_scores.values())

for group, metrics in group_metrics.items():
    # Calculate the total score for the group
    group_score = sum(raw_scores[metric] for metric in metrics)
    
    # Calculate the Target Group Weight
    target_group_weight = group_score / grand_total_score
    
    # Calculate the Group Tilt
    group_tilt = target_group_weight - GROUP_BASELINE
    
    # Calculate the New Group Weight
    new_group_weight = GROUP_BASELINE + group_tilt
    
    group_data[group] = {
        'Group Total Score': group_score,
        'Target Group Weight': target_group_weight,
        'Group Tilt': group_tilt,
        'New Group Weight': new_group_weight,
        'Metrics': {}
    }

# 3. Calculate the Sub-Indicator Tilts and Final Metric Weights
results = []
for group, data in group_data.items():
    metrics = group_metrics[group]
    num_sub_metrics = len(metrics)
    group_score = data['Group Total Score']
    
    # Determine the Sub-Metric Baseline Weight
    SUB_METRIC_BASELINE_INTERNAL = 1.0 / num_sub_metrics

    for metric in metrics:
        metric_score = raw_scores[metric]
        
        # Calculate the Target Sub-Metric Weight (Internal to the group)
        target_sub_metric_weight_internal = metric_score / group_score
        
        # Calculate the Sub-Metric Tilt (Internal)
        sub_metric_tilt_internal = target_sub_metric_weight_internal - SUB_METRIC_BASELINE_INTERNAL

        # Calculate the New Sub-Metric Weight (Internal)
        new_sub_metric_weight_internal = SUB_METRIC_BASELINE_INTERNAL + sub_metric_tilt_internal

        # Calculate the Final Metric Weight (New Group Weight * New Sub-Metric Weight Internal)
        final_metric_weight = data['New Group Weight'] * new_sub_metric_weight_internal
        
        results.append({
            'Group': group,
            'Sub-Indicator': metric.split('_')[-1], # Use the last part of the key for readability
            'Group Baseline': GROUP_BASELINE * 100,
            'Group Tilt (%)': data['Group Tilt'] * 100,
            'New Group Weight (%)': data['New Group Weight'] * 100,
            'Sub-Indicator Baseline (Internal)': SUB_METRIC_BASELINE_INTERNAL * 100,
            'Sub-Indicator Tilt (Internal, %)': sub_metric_tilt_internal * 100,
            'New Sub-Indicator Weight (Internal, %)': new_sub_metric_weight_internal * 100,
            'Final Metric Weight (%)': final_metric_weight * 100
        })

# Create a DataFrame for clean presentation
df_results = pd.DataFrame(results)

# Clean up Sub-Indicator names for the final table
df_results['Sub-Indicator'] = df_results['Sub-Indicator'].replace({
    'IncPovEmp': 'Income/Poverty/Employment',
    'Healthcare': 'Healthcare costs',
    'Transportation': 'Transportation costs',
    'Housing': 'Housing costs (Proxy)',
    'Education': 'Education',
    'Race': 'Cultural - Race'
})

# Final reordering and sorting for readability
column_order = [
    'Group', 'Sub-Indicator', 'Group Baseline', 'Group Tilt (%)', 'New Group Weight (%)',
    'Sub-Indicator Baseline (Internal)', 'Sub-Indicator Tilt (Internal, %)', 
    'New Sub-Indicator Weight (Internal, %)', 'Final Metric Weight (%)'
]
df_results = df_results[column_order]

group_order = ['Economic Security', 'Education', 'Location Affordability', 'Cultural - Race']
df_results['Group_Sort'] = df_results['Group'].astype('category').cat.set_categories(group_order, ordered=True)
df_results = df_results.sort_values(by=['Group_Sort', 'Sub-Indicator']).drop(columns=['Group_Sort'])

# --- LINE ADDED TO CREATE CSV FILE ---
# The code below saves the final calculated DataFrame to a CSV file.
df_results.to_csv('metric_weights_and_tilts_final.csv', index=False)

# Load the data from the previously created CSV file
# csv_filename = 'metric_weights_and_tilts.csv'
# df_results = pd.read_csv(csv_filename)

# --- Output to TXT (Plain Text Table) ---

# Convert the DataFrame to a formatted plain text string
# Using to_string(index=False) preserves the table structure without the index
txt_content = df_results.to_string(index=False)

# Define the filename for the text file
txt_filename = 'metric_weights_and_tilts.txt'

# Write the content to the text file
with open(txt_filename, 'w') as f:
    f.write("Final Metric Weighting and Tilt Calculation\n\n")
    f.write(txt_content)

# Print confirmation of file creation
# print(f"Successfully created and saved the table to: {csv_filename}")
print(f"Successfully created and saved the table to: {txt_filename}")

# Print the content of the TXT file for review
print("\n--- Content of metric_weights_and_tilts.txt ---\n")
print(txt_content)