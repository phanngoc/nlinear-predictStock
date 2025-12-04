"""Network Signals - Aggregate Phase 2 signals"""
import numpy as np
from .correlation_network import CorrelationNetwork
from .network_metrics import NetworkMetrics
from .lead_lag_detector import LeadLagDetector


class NetworkSignals:
    """
    Generate trading signals từ network analysis
    
    Signals:
    1. Regime shift: Network density change
    2. Leader following: Trade laggers based on leaders
    3. Centrality: Focus on high-centrality stocks
    
    Vietnam Market Optimization:
    - Higher lead-lag weight (70%) due to low liquidity → stronger lead-lag effects
    - Sector clustering important (banking, real estate move together)
    - Density changes signal risk-off earlier in VN market
    """
    
    # Regime-adaptive weights for Vietnam market
    REGIME_WEIGHTS = {
        'BULL': {'regime': 0.25, 'lag': 0.75},   # Follow leaders in uptrend
        'BEAR': {'regime': 0.50, 'lag': 0.50},   # Equal weight in downtrend
        'SIDEWAYS': {'regime': 0.35, 'lag': 0.65},
        'UNKNOWN': {'regime': 0.30, 'lag': 0.70}
    }
    
    def __init__(self, correlation_threshold=0.4):
        self.network_builder = CorrelationNetwork(threshold=correlation_threshold)
        self.lead_lag = LeadLagDetector(max_lag=5)
        
    def generate(self, returns_df, target_asset=None):
        """
        Generate network-based signals
        
        Args:
            returns_df: DataFrame of returns
            target_asset: specific asset to generate signal for
            
        Returns:
            dict with signals and analysis
        """
        # Build network
        G = self.network_builder.build_from_returns(returns_df, method='partial')
        metrics = NetworkMetrics(G)
        
        # Network stats
        stats = metrics.get_network_stats()
        
        # Regime signal from density
        regime_signal = self._density_regime_signal(returns_df)
        
        # Leader signal
        leaders = metrics.find_leaders(top_n=5)
        
        # Lead-lag signal for target
        if target_asset and target_asset in returns_df.columns:
            lag_signal = self.lead_lag.generate_lag_signals(returns_df, target_asset)
            centrality = metrics.get_all_centralities()
            target_centrality = {
                k: v.get(target_asset, 0) for k, v in centrality.items()
            }
        else:
            lag_signal = {'signal': 0, 'confidence': 0}
            target_centrality = {}
            
        # Composite signal
        composite = self._aggregate_signals(regime_signal, lag_signal)
        
        return {
            'signal': composite['signal'],
            'confidence': composite['confidence'],
            'components': {
                'regime': regime_signal,
                'lead_lag': lag_signal
            },
            'network_stats': stats,
            'leaders': leaders,
            'target_centrality': target_centrality,
            'clusters': metrics.find_clusters()
        }
    
    def _density_regime_signal(self, returns_df, window=60):
        """
        Detect regime from network density changes
        High density increase = risk-off (correlations rising)
        """
        if len(returns_df) < window * 2:
            return {'signal': 0, 'confidence': 0.5, 'regime': 'UNKNOWN'}
            
        # Recent vs previous network
        recent = returns_df.iloc[-window:]
        previous = returns_df.iloc[-2*window:-window]
        
        G_recent = self.network_builder.build_from_returns(recent)
        G_prev = self.network_builder.build_from_returns(previous)
        
        density_recent = NetworkMetrics(G_recent).network_density()
        density_prev = NetworkMetrics(G_prev).network_density()
        
        density_change = density_recent - density_prev
        
        # Interpretation
        if density_change > 0.1:
            regime = 'RISK_OFF'
            signal = -0.5  # Reduce exposure
        elif density_change < -0.1:
            regime = 'RISK_ON'
            signal = 0.3  # Increase exposure
        else:
            regime = 'NORMAL'
            signal = 0
            
        return {
            'signal': signal,
            'confidence': min(abs(density_change) * 5, 1.0),
            'regime': regime,
            'density_current': density_recent,
            'density_previous': density_prev,
            'density_change': density_change
        }
    
    def _aggregate_signals(self, regime_signal, lag_signal, market_regime='UNKNOWN'):
        """
        Combine regime and lead-lag signals with adaptive weights
        Vietnam market: higher lead-lag weight due to low liquidity
        """
        # Get simplified regime for weight selection
        if 'BULL' in market_regime:
            regime_key = 'BULL'
        elif 'BEAR' in market_regime:
            regime_key = 'BEAR'
        elif market_regime == 'SIDEWAYS':
            regime_key = 'SIDEWAYS'
        else:
            regime_key = 'UNKNOWN'
            
        weights = self.REGIME_WEIGHTS.get(regime_key, self.REGIME_WEIGHTS['UNKNOWN'])
        
        signal = (
            weights['regime'] * regime_signal['signal'] +
            weights['lag'] * lag_signal['signal']
        )
        
        confidence = (
            weights['regime'] * regime_signal['confidence'] +
            weights['lag'] * lag_signal['confidence']
        )
        
        return {
            'signal': signal, 
            'confidence': confidence,
            'weights_used': weights
        }
    
    def detect_regime_shift(self, returns_df, windows=[30, 60, 90]):
        """
        Multi-timeframe regime shift detection
        """
        shifts = []
        for w in windows:
            if len(returns_df) >= w * 2:
                result = self._density_regime_signal(returns_df, window=w)
                shifts.append({
                    'window': w,
                    'regime': result['regime'],
                    'density_change': result['density_change']
                })
                
        # Consensus
        regimes = [s['regime'] for s in shifts]
        if regimes.count('RISK_OFF') >= 2:
            consensus = 'RISK_OFF'
        elif regimes.count('RISK_ON') >= 2:
            consensus = 'RISK_ON'
        else:
            consensus = 'MIXED'
            
        return {
            'consensus': consensus,
            'details': shifts
        }
