"""Network Metrics - Centrality, Clustering, Community Detection"""
import numpy as np
import networkx as nx
from collections import defaultdict


class NetworkMetrics:
    """
    Calculate network metrics for trading signals
    - Centrality: Find market leaders
    - Clustering: Find sector groups
    - Community: Detect market structure
    """
    
    def __init__(self, graph):
        self.G = graph
        
    def degree_centrality(self):
        """
        Degree centrality - số connections
        High degree = stock ảnh hưởng/bị ảnh hưởng bởi nhiều stocks khác
        """
        return nx.degree_centrality(self.G)
    
    def betweenness_centrality(self):
        """
        Betweenness - stock nằm trên nhiều shortest paths
        High betweenness = "bridge" giữa các sectors
        """
        return nx.betweenness_centrality(self.G, weight='weight')
    
    def eigenvector_centrality(self):
        """
        Eigenvector centrality - connected to important nodes
        High eigenvector = connected to other important stocks
        """
        try:
            return nx.eigenvector_centrality(self.G, weight='weight', max_iter=500)
        except:
            return self.degree_centrality()
    
    def pagerank(self, alpha=0.85):
        """
        PageRank - importance in network
        """
        return nx.pagerank(self.G, alpha=alpha, weight='weight')
    
    def clustering_coefficient(self):
        """
        Local clustering - how connected are neighbors
        High clustering = stock trong tight-knit group
        """
        return nx.clustering(self.G, weight='weight')
    
    def get_all_centralities(self):
        """Get all centrality measures"""
        return {
            'degree': self.degree_centrality(),
            'betweenness': self.betweenness_centrality(),
            'eigenvector': self.eigenvector_centrality(),
            'pagerank': self.pagerank(),
            'clustering': self.clustering_coefficient()
        }
    
    def find_leaders(self, top_n=5):
        """
        Find market leaders based on centrality
        Leaders = high centrality across multiple measures
        """
        centralities = self.get_all_centralities()
        
        # Composite score
        scores = defaultdict(float)
        for metric, values in centralities.items():
            if metric == 'clustering':
                continue
            if not values:
                continue
            # Normalize and sum
            max_val = max(values.values()) if values else 1
            if max_val == 0:
                max_val = 1
            for node, val in values.items():
                scores[node] += val / max_val
                
        # Sort by composite score
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return ranked[:top_n]
    
    def find_clusters(self):
        """
        Find clusters/communities in network
        Returns: dict {cluster_id: [nodes]}
        """
        try:
            from networkx.algorithms import community
            communities = community.louvain_communities(self.G, weight='weight')
            return {i: list(c) for i, c in enumerate(communities)}
        except:
            # Fallback: connected components
            components = list(nx.connected_components(self.G))
            return {i: list(c) for i, c in enumerate(components)}
    
    def network_density(self):
        """
        Network density - how connected is the network
        High density = high market correlation (risk-off)
        """
        return nx.density(self.G)
    
    def average_clustering(self):
        """Average clustering coefficient"""
        return nx.average_clustering(self.G, weight='weight')
    
    def get_network_stats(self):
        """Summary statistics of network"""
        return {
            'nodes': self.G.number_of_nodes(),
            'edges': self.G.number_of_edges(),
            'density': self.network_density(),
            'avg_clustering': self.average_clustering(),
            'is_connected': nx.is_connected(self.G) if self.G.number_of_nodes() > 0 else False
        }
