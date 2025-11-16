import pandas as pd
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt

def plot_partition_geographically(data: np.ndarray, partition: list, shapefile_path: str):
    """
    Plots a geographic choropleth map of North Carolina, coloring
    census tracts based on a provided data partition.
    
    

    Args:
        data: The full NumPy data array. It's assumed that data[i, 0]
              is the GEOID for the i-th row.
        partition: A list of lists, where each inner list contains the
                   indices of the data points for a specific cluster.
                   Example: [[0, 1, 4], [2, 3, 5]]
        shapefile_path: The file path to the .shp file for
                        North Carolina census tracts.
    """
    
    print("Loading shapefile...")
    # 1. Load the North Carolina census tract shapefile
    try:
        gdf_nc = gpd.read_file(shapefile_path)
    except Exception as e:
        print(f"Error loading shapefile: {e}")
        print("Please ensure you have 'geopandas' installed (`pip install geopandas`)")
        print(f"And that the path '{shapefile_path}' is correct.")
        return

    # 2. Create a DataFrame from your partition data
    # We need to link GEOID (from data[i, 0]) to a cluster ID
    
    # First, link original_index to cluster_id
    partition_data = []
    for cluster_id, indices in enumerate(partition):
        for index in indices:
            partition_data.append({
                'original_index': index,
                'cluster': cluster_id
            })
    df_partition = pd.DataFrame(partition_data)

    # Next, link original_index to GEOID
    df_geoids = pd.DataFrame({
        'GEOID': data[:, 0], # Assumes GEOID is in column 0
        'original_index': np.arange(data.shape[0])
    })

    # Now, merge them so we have GEOID <-> cluster
    df_clusters = df_geoids.merge(df_partition, on='original_index')
    
    # 3. Standardize GEOID formats for merging
    # This is a critical step.
    # User's format: "1500000US370010201001" (string)
    # Shapefile format: "37001020100" (string)
    # We must extract the 11-digit tract ID from the user's string.
    
    # --- THIS IS THE FIX ---
    try:
        # Ensure it's a string, split at 'US', take the 2nd part, and keep 1st 11 chars
        df_clusters['GEOID'] = df_clusters['GEOID'].astype(str).str.split('US').str[1].str[:11]
    except Exception as e:
        print(f"Error processing your GEOIDs: {e}")
        print("The code expects the GEOID in data[:, 0] to be in a format like '...US370010201001'")
        print(f"First 5 GEOIDs in your data: {df_geoids['GEOID'].head().values}")
        return
    
    # Check if the split worked (it will be None if 'US' wasn't found)
    if df_clusters['GEOID'].isnull().any():
        print("Error: Some GEOIDs were not in the expected '...US...' format.")
        print("Could not extract 11-digit tract ID.")
        print(f"First 5 GEOIDs in your data: {df_geoids['GEOID'].head().values}")
        print(f"First 5 *processed* GEOIDs: {df_clusters['GEOID'].head().values}")
        return
    # --- END OF FIX ---

    # Ensure GEOID in shapefile is also a string
    # (The TIGER file GEOID column is named 'GEOID')
    gdf_nc['GEOID'] = gdf_nc['GEOID'].astype(str)

    # 4. Merge your cluster data with the GeoDataFrame
    print("Merging partition data with map...")
    merged_gdf = gdf_nc.merge(df_clusters, on='GEOID', how='left')
    
    # 'cluster' column will be NaN for tracts not in your data
    
    # 5. Plot the final map
    print("Generating plot...")
    fig, ax = plt.subplots(1, 1, figsize=(20, 12))
    
    # [This is the original plot call, now with linewidth=0]
    merged_gdf.plot(
        column='cluster',
        ax=ax,
        legend=True,
        categorical=True,
        # --- FIX ---
        # Remove all individual tract borders by setting linewidth to 0
        linewidth=0,
        # --- END OF FIX ---
        missing_kwds={
            "color": "lightgrey",
            "edgecolor": "#ffffff",
            "hatch": "///",
            "label": "Not in data"
        }
    )
    
    # --- NEW: Draw cluster-separating borders ---
    # Dissolve all tracts by their cluster ID into giant "super-polygons"
    dissolved_gdf = merged_gdf.dissolve(by='cluster')
    
    # Plot *only the boundaries* of these new super-polygons
    dissolved_gdf.boundary.plot(
        ax=ax,
        color="black",
        linewidth=0.5 # A thin black line
    )
    # --- END OF NEW ---
    
    ax.set_title(f"North Carolina Census Tracts by Cluster (k={len(partition)})", fontsize=20)
    ax.axis('off') # Remove lat/lon axes
    plt.tight_layout()
    print("Done. Showing plot.")
    plt.show()

# --- Example Usage (How to call this function) ---
if __name__ == "__main__":
    
    # 1. --- This is placeholder data. ---
    # In your real script, you will have your actual 'data' and 'partition'
    print("Creating mock data for demonstration...")
    
    # Create mock data with real NC GEOIDs (as strings)
    # (These are from Wake and Durham counties)
    mock_data = np.array([
        ['37183053517', 50000, 120, 2.5],
        ['37183053607', 80000, 80, 1.2],
        ['37183053521', 52000, 110, 2.8],
        ['37063002008', 120000, 40, 3.1],
        ['37063001815', 130000, 35, 4.0],
        ['37063001900', 115000, 50, 2.9]
    ])
    
    # Create a mock partition (list of lists of indices)
    # Cluster 0: Wake County (indices 0, 1, 2)
    # Cluster 1: Durham County (indices 3, 4, 5)
    mock_partition = [
        [0, 1, 2],
        [3, 4, 5]
    ]

    # 2. --- SET THIS PATH ---
    # This is the path to the unzipped shapefile on your computer.
    # You must download this file first (see instructions).
    # This example assumes it's in a subfolder "tl_2020_37_tract"
    SHAPEFILE_PATH = "tl_2020_37_tract/tl_2020_37_tract.shp"

    print("--- Running Geographic Plotting Demo ---")
    print("This will likely fail if 'geopandas' is not installed")
    print("or if the shapefile is not at the correct path.")
    
    # 3. --- This is how you call the function ---
    try:
        plot_partition_geographically(
            data=mock_data, 
            partition=mock_partition, 
            shapefile_path=SHAPEFILE_PATH
        )
    except Exception as e:
        print(f"\n--- DEMO FAILED ---")
        print(f"Error: {e}")
        print("\nPlease follow the setup instructions in the chat.")