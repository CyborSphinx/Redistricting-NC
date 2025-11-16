import numpy as np
import networkx as nx
def create_network(data:np.ndarray, weights,window_size):
    # First add each data point as a node
    G = nx.Graph()
    for i in range(data.shape[0]):
        G.add_node(i)

    # For each dimension in the data, add edges between points within a certain window size
    
    for dim in range(data.shape[1]):
        weight=weights[dim]
        # Find the max of the current dimension
        dim_values = data[:, dim]
        max_value = np.max(dim_values)
        min_value = np.min(dim_values)
        
        n=int((max_value-min_value)/window_size) + 1
        
        # this add each marker in the dimesion as a node, so that data points close to it can connect to it
        markers = [window_size * i + min_value for i in range(n+1)]
        G.add_node(f'{dim},{markers[0]:.4f}', marker=True, dim=dim, value=markers[0])
        for i in range(1,n+1):
            G.add_node(f'{dim},{markers[i]:.4f}', marker=True, dim=dim, value=markers[i])
            G.add_edge(f'{dim},{markers[i-1]:.4f}',f'{dim},{markers[i]:.4f}', weight=weight)
        
        # Now connect data points to the nearest marker nodes within the window size
        for i, point in enumerate(data):
            point_value = point[dim]
            lower_marker = markers[int((point_value - min_value) / window_size)]
            G.add_edge(i, f'{dim},{lower_marker:.4f}', weight=weight)
        
    return G

from collections import defaultdict

def show_node_counts(G):
    """
    Display node count statistics for the network.
    
    Parameters:
    -----------
    G : nx.Graph
        NetworkX graph with data point and marker nodes
    """
    
    # Count data point nodes
    num_data = sum(1 for n, d in G.nodes(data=True) if not d.get('marker', False))
    
    # Count marker nodes by dimension
    markers_by_dim = defaultdict(int)
    for n, d in G.nodes(data=True):
        if d.get('marker', False):
            markers_by_dim[d['dim']] += 1
    
    # Total markers
    num_markers = sum(markers_by_dim.values())
    
    # Print results
    print("=" * 50)
    print("NODE COUNTS")
    print("=" * 50)
    print(f"Data point nodes: {num_data}")
    print(f"Marker nodes (total): {num_markers}")
    print(f"Total nodes: {G.number_of_nodes()}")
    
    print("\n" + "-" * 50)
    print("Marker nodes per dimension:")
    print("-" * 50)
    for dim in sorted(markers_by_dim.keys()):
        print(f"  Dimension {dim:2d}: {markers_by_dim[dim]:4d} markers")
    
    return {
        'data_nodes': num_data,
        'marker_nodes': num_markers,
        'markers_by_dim': dict(markers_by_dim)
    }

def prune_markers_minimal(G):
    """
    Remove marker nodes and create minimal ring structures.
    
    For each marker:
    1. Connect its data points in a ring (cycle)
    2. Connect this ring to the next ring with ONE edge
    """
    
    G_pruned = nx.Graph()
    
    # Add all data point nodes
    data_nodes = [n for n in G.nodes() if isinstance(n, int)]
    for node in data_nodes:
        G_pruned.add_node(node)
    
    # Organize markers by dimension and sort by value
    markers_by_dim = defaultdict(list)
    for n, d in G.nodes(data=True):
        if d.get('marker', False):
            markers_by_dim[d['dim']].append((n, d['value']))
    
    for dim in markers_by_dim:
        markers_by_dim[dim].sort(key=lambda x: x[1])
    
    # Process each dimension
    for dim, markers in markers_by_dim.items():
        
        for marker_idx, (marker_name, marker_value) in enumerate(markers):
            
            neighbors = [n for n in G.neighbors(marker_name) if isinstance(n, int)]
            
            if len(neighbors) == 0:
                continue
            
            weight = G[marker_name][neighbors[0]].get('weight', 1.0)
            
            # 1. Connect neighbors in a ring (cycle)
            for i in range(len(neighbors)):
                node1 = neighbors[i]
                node2 = neighbors[(i + 1) % len(neighbors)]
                
                if G_pruned.has_edge(node1, node2):
                    G_pruned[node1][node2]['weight'] += weight
                else:
                    G_pruned.add_edge(node1, node2, weight=weight)
            
            # 2. Connect to next ring with ONE edge only
            if marker_idx < len(markers) - 1:
                next_marker_name, _ = markers[marker_idx + 1]
                next_neighbors = [n for n in G.neighbors(next_marker_name) if isinstance(n, int)]
                
                if len(next_neighbors) > 0:
                    # Single edge: first node of current ring to first node of next ring
                    curr_node = neighbors[0]
                    next_node = next_neighbors[0]
                    
                    if G_pruned.has_edge(curr_node, next_node):
                        G_pruned[curr_node][next_node]['weight'] += weight
                    else:
                        G_pruned.add_edge(curr_node, next_node, weight=weight)
    
    return G_pruned
def construct_net(data,weights,window_size):
    G=create_network(data,weights,window_size)
    show_node_counts(G)
    G_pruned=prune_markers_minimal(G)
    return G_pruned
