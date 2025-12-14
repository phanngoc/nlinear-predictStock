"""Granger Causality Analysis"""
import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import grangercausalitytests
import warnings
warnings.filterwarnings('ignore')


class GrangerCausalityAnalyzer:
    """
    Granger Causality để xác định:
    - Asset nào "cause" (predict) asset khác
    - Build causality network
    - Find leading indicators
    """
    
    def __init__(self, max_lag=5, significance=0.05):
        self.max_lag = max_lag
        self.significance = significance
        
    def test_pair(self, series1, series2):
        """
        Test if series1 Granger-causes series2
        
        Returns:
            dict: {lag: p_value} for each lag
        """
        data = pd.DataFrame({'y': series2, 'x': series1})
        
        try:
            result = grangercausalitytests(data[['y', 'x']], maxlag=self.max_lag, verbose=False)
            
            p_values = {}
            for lag in range(1, self.max_lag + 1):
                # Use F-test p-value
                p_values[lag] = result[lag][0]['ssr_ftest'][1]
                
            return p_values
        except:
            return {lag: 1.0 for lag in range(1, self.max_lag + 1)}
    
    def build_causality_matrix(self, returns_df):
        """
        Build matrix of Granger causality relationships
        
        Returns:
            DataFrame: [i,j] = 1 if asset i causes asset j
        """
        assets = returns_df.columns
        n = len(assets)
        
        causality = np.zeros((n, n))
        p_values = np.ones((n, n))
        
        for i in range(n):
            for j in range(n):
                if i != j:
                    pvals = self.test_pair(
                        returns_df.iloc[:, i].values,
                        returns_df.iloc[:, j].values
                    )
                    # Use minimum p-value across lags
                    min_p = min(pvals.values())
                    p_values[i, j] = min_p
                    causality[i, j] = 1 if min_p < self.significance else 0
                    
        return {
            'causality': pd.DataFrame(causality, index=assets, columns=assets),
            'p_values': pd.DataFrame(p_values, index=assets, columns=assets)
        }
    
    def find_leading_indicators(self, returns_df, target_asset):
        """
        Find assets that Granger-cause target
        
        Returns:
            list: [(asset, p_value)] sorted by significance
        """
        if target_asset not in returns_df.columns:
            return []
            
        leaders = []
        target_series = returns_df[target_asset].values
        
        for asset in returns_df.columns:
            if asset != target_asset:
                pvals = self.test_pair(returns_df[asset].values, target_series)
                min_p = min(pvals.values())
                if min_p < self.significance:
                    leaders.append((asset, min_p))
                    
        leaders.sort(key=lambda x: x[1])
        return leaders
    
    def get_causality_signal(self, returns_df, target_asset):
        """
        Generate signal based on leading indicators
        """
        leaders = self.find_leading_indicators(returns_df, target_asset)
        
        if not leaders:
            return {'signal': 0, 'confidence': 0, 'leaders': []}
            
        # Aggregate signal from leaders
        signals = []
        for leader, p_val in leaders[:5]:  # Top 5 leaders
            # Recent return of leader
            leader_return = returns_df[leader].iloc[-5:].mean()
            weight = 1 - p_val  # Lower p-value = higher weight
            signals.append(leader_return * weight)
            
        avg_signal = np.mean(signals)
        signal = np.tanh(avg_signal * 100)
        confidence = 1 - np.mean([p for _, p in leaders[:5]])
        
        return {
            'signal': float(signal),
            'confidence': float(confidence),
            'leaders': leaders[:5]
        }
    
    def get_network_structure(self, returns_df):
        """
        Get causality network structure
        """
        result = self.build_causality_matrix(returns_df)
        causality = result['causality']
        
        # Count outgoing (causes) and incoming (caused by)
        structure = {}
        for asset in causality.columns:
            structure[asset] = {
                'causes': int(causality.loc[asset].sum()),
                'caused_by': int(causality[asset].sum()),
                'net_influence': int(causality.loc[asset].sum() - causality[asset].sum())
            }
            
        return structure
