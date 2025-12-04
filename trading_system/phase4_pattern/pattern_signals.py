"""Pattern Signals - Aggregate Phase 4"""
import numpy as np
from .regime_detector import AdvancedRegimeDetector
from .factor_model import FactorModel
from .anomaly_detector import AnomalyDetector


class PatternSignals:
    """
    Aggregate signals từ pattern hunting:
    - Regime detection (4-state: Bull/Bear x High/Low Vol)
    - Factor alpha
    - Anomaly detection
    
    Vietnam Market Optimization:
    - Higher regime weight (retail-dominated → clear trends)
    - Sector rotation detection
    - Mean reversion for sideways market
    """
    
    # Regime-specific component weights for Vietnam market
    REGIME_COMPONENT_WEIGHTS = {
        'BULL_LOW_VOL': {'regime': 0.40, 'factor': 0.35, 'anomaly': 0.25},
        'BULL_HIGH_VOL': {'regime': 0.50, 'factor': 0.25, 'anomaly': 0.25},
        'BEAR_HIGH_VOL': {'regime': 0.55, 'factor': 0.20, 'anomaly': 0.25},
        'BEAR_LOW_VOL': {'regime': 0.45, 'factor': 0.30, 'anomaly': 0.25},
        'SIDEWAYS': {'regime': 0.35, 'factor': 0.30, 'anomaly': 0.35},  # Anomaly more useful
        'UNKNOWN': {'regime': 0.45, 'factor': 0.30, 'anomaly': 0.25}
    }
    
    def __init__(self):
        self.regime = AdvancedRegimeDetector(n_regimes=4)
        self.factor = FactorModel(n_factors=5)
        self.anomaly = AnomalyDetector(z_threshold=2.0)
        
    def generate(self, prices_df, returns_df, target_asset):
        """
        Generate composite pattern signal with adaptive weights
        """
        if target_asset not in prices_df.columns:
            return {'error': f'{target_asset} not found'}
            
        # Regime signal (use target prices)
        regime_signal = self.regime.get_signal(prices_df[target_asset].values)
        current_regime = regime_signal.get('regime', 'UNKNOWN')
        
        # Factor alpha signal
        factor_signal = self.factor.get_alpha_signal(returns_df, target_asset)
        
        # Anomaly signal
        anomaly_signal = self.anomaly.get_anomaly_signal(prices_df, returns_df, target_asset)
        
        # Get adaptive weights based on current regime
        weights = self.REGIME_COMPONENT_WEIGHTS.get(
            current_regime, 
            self.REGIME_COMPONENT_WEIGHTS['UNKNOWN']
        )
        
        composite = (
            weights['regime'] * regime_signal['signal'] +
            weights['factor'] * factor_signal['signal'] +
            weights['anomaly'] * anomaly_signal['signal']
        )
        
        confidence = (
            weights['regime'] * regime_signal['confidence'] +
            weights['factor'] * factor_signal['confidence'] +
            weights['anomaly'] * anomaly_signal['confidence']
        )
        
        # Regime override with gradual adjustment
        if current_regime == 'BEAR_HIGH_VOL':
            # Strong bearish override - limit long exposure
            composite = min(composite, -0.2)
        elif current_regime == 'BULL_LOW_VOL':
            # Strong bullish override - limit short exposure  
            composite = max(composite, 0.2)
        elif current_regime == 'SIDEWAYS':
            # In sideways, amplify mean reversion signals
            if abs(composite) < 0.3:
                composite *= 1.5  # Boost weak signals for mean reversion
            
        return {
            'signal': float(composite),
            'confidence': float(confidence),
            'regime': current_regime,
            'regime_action': regime_signal['action'],
            'component_weights': weights,
            'components': {
                'regime': regime_signal,
                'factor': factor_signal,
                'anomaly': anomaly_signal
            }
        }
    
    def scan_opportunities(self, prices_df, returns_df):
        """
        Scan all assets for opportunities
        """
        opportunities = []
        
        for asset in prices_df.columns:
            try:
                result = self.generate(prices_df, returns_df, asset)
                if 'error' not in result:
                    opportunities.append({
                        'asset': asset,
                        'signal': result['signal'],
                        'confidence': result['confidence'],
                        'regime': result['regime']
                    })
            except:
                continue
                
        # Sort by signal strength
        opportunities.sort(key=lambda x: abs(x['signal'] * x['confidence']), reverse=True)
        
        return {
            'buy_candidates': [o for o in opportunities if o['signal'] > 0.3][:5],
            'sell_candidates': [o for o in opportunities if o['signal'] < -0.3][:5],
            'all': opportunities
        }
