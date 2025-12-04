"""Signal Aggregator - Combine signals from all phases"""
import numpy as np
from typing import Dict, Optional


class SignalAggregator:
    """
    Aggregate signals từ tất cả 5 phases
    - Weighted combination with adaptive weights based on regime
    - Confirmation logic
    - Final trading decision
    
    Vietnam Market Optimization:
    - Higher Pattern weight for regime detection (retail-dominated market)
    - Higher Network weight for lead-lag relationships (low liquidity)
    - Lower Multivariate weight (VAR less effective in VN)
    """
    
    # Regime-adaptive weights for Vietnam market
    REGIME_WEIGHTS = {
        'BULL_LOW_VOL': {
            'foundation': 0.20,
            'network': 0.30,      # Lead-lag very useful in trending market
            'multivariate': 0.10,
            'pattern': 0.40
        },
        'BULL_HIGH_VOL': {
            'foundation': 0.25,
            'network': 0.25,
            'multivariate': 0.15,
            'pattern': 0.35
        },
        'BEAR_HIGH_VOL': {
            'foundation': 0.35,   # Risk management critical
            'network': 0.15,
            'multivariate': 0.20, # Tail risk important
            'pattern': 0.30
        },
        'BEAR_LOW_VOL': {
            'foundation': 0.30,
            'network': 0.20,
            'multivariate': 0.20,
            'pattern': 0.30
        },
        'SIDEWAYS': {
            'foundation': 0.30,   # Mean reversion signals
            'network': 0.20,
            'multivariate': 0.15,
            'pattern': 0.35       # Anomaly detection useful
        },
        'UNKNOWN': {
            'foundation': 0.25,
            'network': 0.25,
            'multivariate': 0.15,
            'pattern': 0.35
        }
    }
    
    def __init__(self, phase_weights: Optional[Dict] = None, adaptive: bool = True):
        self.adaptive = adaptive
        self.default_weights = phase_weights or {
            'foundation': 0.25,
            'network': 0.25,
            'multivariate': 0.15,
            'pattern': 0.35
        }
        self.phase_weights = self.default_weights.copy()
    
    def get_adaptive_weights(self, regime: str) -> Dict:
        """Get weights adapted to current market regime"""
        if not self.adaptive:
            return self.default_weights
        return self.REGIME_WEIGHTS.get(regime, self.REGIME_WEIGHTS['UNKNOWN'])
        
    def aggregate(self, signals: Dict, regime: str = 'UNKNOWN') -> Dict:
        """
        Aggregate signals từ multiple phases with adaptive weights
        
        Args:
            signals: dict {phase_name: {'signal': float, 'confidence': float}}
            regime: current market regime for adaptive weighting
            
        Returns:
            dict: {
                'composite_signal': float,
                'confidence': float,
                'action': str,
                'weights_used': dict
            }
        """
        # Get adaptive weights based on regime
        weights = self.get_adaptive_weights(regime)
        
        total_weight = 0
        weighted_signal = 0
        weighted_confidence = 0
        
        for phase, weight in weights.items():
            if phase in signals and 'signal' in signals[phase]:
                sig = signals[phase]['signal']
                conf = signals[phase].get('confidence', 0.5)
                
                weighted_signal += weight * sig
                weighted_confidence += weight * conf
                total_weight += weight
                
        if total_weight == 0:
            return {'error': 'No valid signals'}
            
        composite = weighted_signal / total_weight
        confidence = weighted_confidence / total_weight
        
        # Confirmation bonus
        agreement_count = sum(
            1 for p in signals.values() 
            if 'signal' in p and np.sign(p['signal']) == np.sign(composite)
        )
        
        if agreement_count >= 3:
            confidence = min(confidence * 1.2, 1.0)
            
        # Action
        # Regime-adjusted thresholds for Vietnam market
        # Lower threshold in trending markets, higher in volatile
        buy_threshold = 0.25 if regime in ['BULL_LOW_VOL', 'BULL_HIGH_VOL'] else 0.30
        sell_threshold = -0.25 if regime in ['BEAR_LOW_VOL', 'BEAR_HIGH_VOL'] else -0.30
        
        if composite > buy_threshold and confidence > 0.5:
            action = 'BUY'
        elif composite < sell_threshold and confidence > 0.5:
            action = 'SELL'
        else:
            action = 'HOLD'
        
        # Strong signal detection
        if abs(composite) > 0.6 and confidence > 0.7:
            action = 'STRONG_' + action.replace('HOLD', 'HOLD')
            
        return {
            'composite_signal': float(composite),
            'confidence': float(confidence),
            'action': action,
            'agreement_count': agreement_count,
            'phases_used': list(signals.keys()),
            'weights_used': weights,
            'regime': regime
        }
