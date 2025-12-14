"""Foundation Signals - Aggregate all Phase 1 signals"""
import numpy as np
from .arima_model import ARIMAModel
from .kalman_filter import KalmanFilter, AdaptiveKalmanFilter
from .hmm_regime import HMMRegimeDetector
from .statistics import StationarityTest, PCAAnalyzer


class FoundationSignals:
    """
    Aggregate signals từ tất cả Phase 1 components:
    - ARIMA: Direction forecast
    - Kalman: Noise-filtered deviation
    - HMM: Market regime
    - Statistics: Strategy recommendation
    
    Output: Composite signal [-1, 1] với confidence
    """
    
    def __init__(self, weights=None):
        # Optimized for Vietnam market: HMM regime detection is critical
        # due to high retail participation and momentum patterns
        self.weights = weights or {
            'arima': 0.25,   # Reduced: less effective in volatile VN market
            'kalman': 0.20,  # Reduced: noise filtering less critical
            'hmm': 0.55      # Increased: regime detection crucial for VN
        }
        
        self.arima = ARIMAModel()
        self.kalman = AdaptiveKalmanFilter()
        self.hmm = HMMRegimeDetector()
        
    def generate(self, prices, pred_days=5):
        """
        Generate composite signal từ all Phase 1 models
        
        Args:
            prices: array-like, historical prices
            pred_days: int, forecast horizon
            
        Returns:
            dict: {
                'signal': float [-1, 1],
                'confidence': float [0, 1],
                'action': str (BUY/SELL/HOLD),
                'components': dict of individual signals,
                'regime': str,
                'analysis': dict
            }
        """
        prices = np.array(prices).flatten()
        
        # Get individual signals
        arima_result = self.arima.get_signal(prices, pred_days)
        kalman_result = self.kalman.get_signal(prices)
        hmm_result = self.hmm.get_signal(prices)
        
        # Stationarity test for strategy recommendation
        stat_result = StationarityTest.full_test(prices)
        
        # Weighted composite signal
        composite = (
            self.weights['arima'] * arima_result['signal'] +
            self.weights['kalman'] * kalman_result['signal'] +
            self.weights['hmm'] * hmm_result['signal']
        )
        
        # Confidence = weighted average of individual confidences
        confidence = (
            self.weights['arima'] * arima_result['confidence'] +
            self.weights['kalman'] * kalman_result['confidence'] +
            self.weights['hmm'] * hmm_result['confidence']
        )
        
        # Regime adjustment
        regime = hmm_result['regime_name']
        if regime == 'BEAR' and composite > 0:
            composite *= 0.5  # Reduce bullish signal in bear market
        elif regime == 'BULL' and composite < 0:
            composite *= 0.5  # Reduce bearish signal in bull market
            
        # Action determination
        if composite > 0.3:
            action = 'BUY'
        elif composite < -0.3:
            action = 'SELL'
        else:
            action = 'HOLD'
            
        # Signal agreement check
        signals = [arima_result['signal'], kalman_result['signal'], hmm_result['signal']]
        agreement = np.sign(signals)
        if np.all(agreement == agreement[0]) and agreement[0] != 0:
            signal_quality = 'STRONG_AGREEMENT'
            confidence *= 1.2  # Boost confidence
        elif np.sum(agreement == np.sign(composite)) >= 2:
            signal_quality = 'MAJORITY_AGREEMENT'
        else:
            signal_quality = 'MIXED_SIGNALS'
            confidence *= 0.8  # Reduce confidence
            
        confidence = min(confidence, 1.0)
        
        return {
            'signal': float(composite),
            'confidence': float(confidence),
            'action': action,
            'signal_quality': signal_quality,
            'regime': regime,
            'recommended_strategy': stat_result['recommended_strategy'],
            'components': {
                'arima': {
                    'signal': arima_result['signal'],
                    'direction': arima_result['direction'],
                    'pct_change': arima_result['pct_change'],
                    'forecast': arima_result['forecast'].tolist()
                },
                'kalman': {
                    'signal': kalman_result['signal'],
                    'z_score': kalman_result['z_score'],
                    'filtered_price': kalman_result['filtered_price'],
                    'deviation': kalman_result['deviation']
                },
                'hmm': {
                    'signal': hmm_result['signal'],
                    'regime': hmm_result['regime_name'],
                    'regime_name': hmm_result['regime_name'],
                    'is_stable': hmm_result.get('is_stable', False),
                    'regime_consistency': hmm_result.get('regime_consistency', 0),
                    'transition': hmm_result['transition'],
                    'probabilities': hmm_result['probabilities']
                }
            },
            'analysis': {
                'stationarity': stat_result['conclusion'],
                'regime_transition': hmm_result['transition']
            }
        }
    
    def generate_multi_asset(self, prices_dict, pred_days=5):
        """
        Generate signals cho multiple assets
        
        Args:
            prices_dict: dict {symbol: prices_array}
            
        Returns:
            dict: {symbol: signal_result}
        """
        results = {}
        for symbol, prices in prices_dict.items():
            try:
                results[symbol] = self.generate(prices, pred_days)
            except Exception as e:
                results[symbol] = {'error': str(e)}
        return results
    
    def rank_assets(self, prices_dict, pred_days=5):
        """
        Rank assets by signal strength
        Returns: sorted list of (symbol, signal, confidence)
        """
        results = self.generate_multi_asset(prices_dict, pred_days)
        
        rankings = []
        for symbol, result in results.items():
            if 'error' not in result:
                rankings.append({
                    'symbol': symbol,
                    'signal': result['signal'],
                    'confidence': result['confidence'],
                    'action': result['action'],
                    'regime': result['regime']
                })
                
        # Sort by signal * confidence (strongest signals first)
        rankings.sort(key=lambda x: abs(x['signal'] * x['confidence']), reverse=True)
        
        return rankings
