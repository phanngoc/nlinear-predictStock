"""Multivariate Signals - Aggregate Phase 3"""
import numpy as np
from .var_model import VARModel
from .granger_causality import GrangerCausalityAnalyzer
from .copula_model import CopulaModel


class MultivariateSignals:
    """
    Aggregate signals từ multivariate analysis:
    - VAR forecast
    - Granger causality
    - Copula risk
    """
    
    def __init__(self):
        self.var = VARModel(max_lags=5)
        self.granger = GrangerCausalityAnalyzer(max_lag=5)
        self.copula = CopulaModel()
        
    def generate(self, returns_df, target_asset, forecast_steps=5):
        """
        Generate composite multivariate signal
        """
        if target_asset not in returns_df.columns:
            return {'error': f'{target_asset} not in data'}
            
        # VAR signal
        var_signal = self.var.get_signal(returns_df, target_asset, steps=forecast_steps)
        
        # Granger signal
        granger_signal = self.granger.get_causality_signal(returns_df, target_asset)
        
        # Copula risk signal
        copula_signal = self.copula.get_risk_signal(returns_df, target_asset)
        
        # Weighted composite
        weights = {'var': 0.4, 'granger': 0.35, 'copula': 0.25}
        
        composite = (
            weights['var'] * var_signal['signal'] +
            weights['granger'] * granger_signal['signal'] +
            weights['copula'] * copula_signal['signal']
        )
        
        confidence = (
            weights['var'] * var_signal['confidence'] +
            weights['granger'] * granger_signal['confidence'] +
            weights['copula'] * copula_signal.get('confidence', 0.5)
        )
        
        # Risk adjustment
        if copula_signal['risk_level'] == 'HIGH_CRASH_RISK':
            composite *= 0.5  # Reduce signal in high risk
            
        return {
            'signal': float(composite),
            'confidence': float(confidence),
            'components': {
                'var': var_signal,
                'granger': granger_signal,
                'copula': copula_signal
            },
            'risk_level': copula_signal['risk_level'],
            'leading_indicators': granger_signal.get('leaders', [])
        }
    
    def get_cross_asset_forecast(self, returns_df, steps=5):
        """
        Forecast all assets simultaneously
        """
        self.var.fit(returns_df)
        forecast = self.var.forecast(steps=steps)
        
        # Rank by expected return
        cum_returns = forecast.sum()
        rankings = cum_returns.sort_values(ascending=False)
        
        return {
            'forecast': forecast.to_dict(),
            'rankings': rankings.to_dict(),
            'top_picks': rankings.head(3).index.tolist(),
            'avoid': rankings.tail(3).index.tolist()
        }
    
    def get_causality_network(self, returns_df):
        """
        Get full causality network structure
        """
        return self.granger.get_network_structure(returns_df)
