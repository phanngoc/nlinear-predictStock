"""Lead-Lag Relationship Detector"""
import numpy as np
import pandas as pd
from scipy import stats


class LeadLagDetector:
    """
    Detect lead-lag relationships between assets
    - Cross-correlation analysis
    - Granger-style lag detection
    
    Trading implication:
    - Trade lagging stocks based on leading stocks' signals
    """
    
    def __init__(self, max_lag=5):
        self.max_lag = max_lag
        
    def cross_correlation(self, series1, series2, max_lag=None):
        """
        Calculate cross-correlation at different lags
        Returns: dict {lag: correlation}
        """
        max_lag = max_lag or self.max_lag
        s1 = np.array(series1)
        s2 = np.array(series2)
        
        correlations = {}
        for lag in range(-max_lag, max_lag + 1):
            if lag < 0:
                corr = np.corrcoef(s1[:lag], s2[-lag:])[0, 1]
            elif lag > 0:
                corr = np.corrcoef(s1[lag:], s2[:-lag])[0, 1]
            else:
                corr = np.corrcoef(s1, s2)[0, 1]
            correlations[lag] = corr
            
        return correlations
    
    def find_optimal_lag(self, series1, series2):
        """
        Find lag with highest correlation
        Positive lag = series1 leads series2
        """
        corrs = self.cross_correlation(series1, series2)
        best_lag = max(corrs, key=lambda k: abs(corrs[k]))
        return {
            'optimal_lag': best_lag,
            'correlation': corrs[best_lag],
            'all_correlations': corrs
        }
    
    def build_lead_lag_matrix(self, returns_df):
        """
        Build matrix of lead-lag relationships
        Returns: DataFrame where [i,j] = optimal lag of i relative to j
        """
        assets = returns_df.columns
        n = len(assets)
        
        lag_matrix = np.zeros((n, n))
        corr_matrix = np.zeros((n, n))
        
        for i in range(n):
            for j in range(n):
                if i != j:
                    result = self.find_optimal_lag(
                        returns_df.iloc[:, i].values,
                        returns_df.iloc[:, j].values
                    )
                    lag_matrix[i, j] = result['optimal_lag']
                    corr_matrix[i, j] = result['correlation']
                    
        return {
            'lag_matrix': pd.DataFrame(lag_matrix, index=assets, columns=assets),
            'corr_matrix': pd.DataFrame(corr_matrix, index=assets, columns=assets)
        }
    
    def find_leaders_and_laggers(self, returns_df, threshold=0.3):
        """
        Identify leading and lagging stocks
        
        Returns:
            dict: {
                'leaders': [(stock, avg_lead_time)],
                'laggers': [(stock, avg_lag_time)],
                'pairs': [(leader, lagger, lag, corr)]
            }
        """
        result = self.build_lead_lag_matrix(returns_df)
        lag_matrix = result['lag_matrix']
        corr_matrix = result['corr_matrix']
        
        assets = lag_matrix.columns
        
        # Calculate average lead/lag for each stock
        lead_scores = {}
        for asset in assets:
            # Positive values in row = this asset leads others
            leads = lag_matrix.loc[asset]
            leads = leads[leads > 0]
            lead_scores[asset] = leads.mean() if len(leads) > 0 else 0
            
        # Find significant pairs
        pairs = []
        for i, a1 in enumerate(assets):
            for j, a2 in enumerate(assets):
                if i < j:
                    lag = lag_matrix.loc[a1, a2]
                    corr = corr_matrix.loc[a1, a2]
                    if abs(corr) > threshold and lag != 0:
                        if lag > 0:
                            pairs.append((a1, a2, lag, corr))  # a1 leads a2
                        else:
                            pairs.append((a2, a1, -lag, corr))  # a2 leads a1
                            
        # Sort by correlation strength
        pairs.sort(key=lambda x: abs(x[3]), reverse=True)
        
        # Identify leaders and laggers
        leaders = sorted(lead_scores.items(), key=lambda x: x[1], reverse=True)[:5]
        laggers = sorted(lead_scores.items(), key=lambda x: x[1])[:5]
        
        return {
            'leaders': leaders,
            'laggers': laggers,
            'pairs': pairs[:10]  # Top 10 pairs
        }
    
    def generate_lag_signals(self, returns_df, target_asset):
        """
        Generate trading signal for target based on leading assets
        """
        result = self.find_leaders_and_laggers(returns_df)
        
        # Find pairs where target is the lagger
        relevant_pairs = [p for p in result['pairs'] if p[1] == target_asset]
        
        if not relevant_pairs:
            return {'signal': 0, 'confidence': 0, 'leaders': []}
            
        signals = []
        for leader, _, lag, corr in relevant_pairs:
            # Get leader's recent return
            leader_return = returns_df[leader].iloc[-int(lag):].mean()
            # Expected target return based on correlation
            expected_return = leader_return * corr
            signals.append({
                'leader': leader,
                'lag': lag,
                'correlation': corr,
                'expected_return': expected_return
            })
            
        # Aggregate signal
        avg_expected = np.mean([s['expected_return'] for s in signals])
        signal = np.tanh(avg_expected * 100)  # Scale and bound
        confidence = np.mean([abs(s['correlation']) for s in signals])
        
        return {
            'signal': signal,
            'confidence': confidence,
            'leaders': signals
        }
