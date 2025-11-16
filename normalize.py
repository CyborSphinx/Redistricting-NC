import pandas as pd
import io

# The raw CSV data provided by the user
csv_file = 'survey.csv'

# Read the CSV data into a pandas DataFrame
df = pd.read_csv(csv_file)

# CRITICAL FIX: Strip whitespace from column names to prevent KeyError
df.columns = df.columns.str.strip()

# --- 1. Filter for relevant years (2022 and 2023) and calculate totals ---
df_relevant = df[df['Year'].isin([2022, 2023])].copy()

# Calculate the total Raw_Score for each relevant year
annual_totals = df_relevant.groupby('Year')['Raw_Score'].sum().reset_index()
annual_totals.rename(columns={'Raw_Score': 'Annual_Total_Raw_Score'}, inplace=True)

# Merge the annual totals into the relevant DataFrame
df_relevant = pd.merge(df_relevant, annual_totals, on='Year')

# Calculate the new Normalized_Score (Share of Annual Total)
df_relevant['New_Normalized_Share (%)'] = (
    (df_relevant['Raw_Score'] / df_relevant['Annual_Total_Raw_Score']) * 100
).round(2)


# --- 2. Prepare for Merging back into the Original DataFrame ---

# Select only the new columns and the keys (Year, Metric) used for merging
df_merge_cols = df_relevant[['Year', 'Metric', 'Annual_Total_Raw_Score', 'New_Normalized_Share (%)']].copy()

# --- 3. Merge the new columns back into the original DataFrame (df) ---
# Use a left merge to preserve all rows from the original data (2019-2023)
# The new columns will have NaN values for 2019 and 2020 rows, which is expected.
df_merged = pd.merge(
    df,
    df_merge_cols,
    on=['Year', 'Metric'],
    how='left'
)

# Optional cleanup: Drop the old Normalized_Score column
# df_merged = df_merged.drop(columns=['Normalized_Score'])

print("--- Merged and Final Data (NaN in 2019/2020 rows are expected) ---")
print(df_merged)

# --- 4. Save the final merged data to a new CSV file ---
# The index=False prevents pandas from writing row numbers to the CSV
output_filename = 'merged_normalized_output.csv'
df_merged.to_csv(output_filename, index=False)

print(f"\nSuccessfully saved the merged data to: {output_filename}")