"""Correlation Network Builder"""
import numpy as np
import pandas as pd
import networkx as nx
from sklearn.covariance import GraphicalLassoCV


class CorrelationNetwork:
    """
    Build stock correlation network
    - Simple correlation
    - Partial correlation (Graphical Lasso)
    - Dynamic/Rolling networks
    """
    
    def __init__(self, threshold=0.5):
        self.threshold = threshold
        self.graph = None
        
    def build_from_returns(self, returns_df, method='correlation'):
        """
        Build network từ returns matrix
        
        Args:
            returns_df: DataFrame, rows=time, cols=assets
            method: 'correlation' or 'partial' (graphical lasso)
        """
        if method == 'correlation':
            adj_matrix = self._correlation_matrix(returns_df)
        else:
            adj_matrix = self._partial_correlation(returns_df)
            
        self.graph = self._matrix_to_graph(adj_matrix, returns_df.columns)
        return self.graph
    
    def _correlation_matrix(self, returns_df):
        """Simple Pearson correlation"""
        corr = returns_df.corr().values
        # Apply threshold
        corr[np.abs(corr) < self.threshold] = 0
        np.fill_diagonal(corr, 0)
        return corr
    
    def _partial_correlation(self, returns_df):
        """
        Graphical Lasso - Sparse partial correlation
        Removes spurious correlations, keeps only direct relationships
        """
        try:
            model = GraphicalLassoCV(cv=3, max_iter=500)
            model.fit(returns_df.values)
            precision = model.precision_
            
            # Convert precision to partial correlation
            d = np.sqrt(np.diag(precision))
            partial_corr = -precision / np.outer(d, d)
            np.fill_diagonal(partial_corr, 0)
            
            # Apply threshold
            partial_corr[np.abs(partial_corr) < self.threshold] = 0
            return partial_corr
        except:
            # Fallback to simple correlation
            return self._correlation_matrix(returns_df)
    
    def _matrix_to_graph(self, adj_matrix, labels):
        """Convert adjacency matrix to NetworkX graph"""
        G = nx.Graph()
        n = len(labels)
        
        for i in range(n):
            G.add_node(labels[i])
            
        for i in range(n):
            for j in range(i+1, n):
                if adj_matrix[i, j] != 0:
                    G.add_edge(labels[i], labels[j], weight=abs(adj_matrix[i, j]))
                    
        return G
    
    def build_rolling_networks(self, returns_df, window=60, step=20):
        """
        Build sequence of networks over time
        Returns: list of (timestamp, graph) tuples
        """
        networks = []
        n = len(returns_df)
        
        for start in range(0, n - window, step):
            end = start + window
            subset = returns_df.iloc[start:end]
            G = self.build_from_returns(subset)
            timestamp = returns_df.index[end-1]
            networks.append((timestamp, G.copy()))
            
        return networks
    
    def get_adjacency_matrix(self):
        """Get adjacency matrix from current graph"""
        if self.graph is None:
            return None
        return nx.to_numpy_array(self.graph)
    
    def get_edge_list(self):
        """Get list of edges with weights"""
        if self.graph is None:
            return []
        return [(u, v, d['weight']) for u, v, d in self.graph.edges(data=True)]
