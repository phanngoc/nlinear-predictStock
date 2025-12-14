"""Advanced Regime Detection"""
import numpy as np
from sklearn.mixture import GaussianMixture
import warnings
warnings.filterwarnings('ignore')


class AdvancedRegimeDetector:
    """
    Multi-dimensional regime detection using GMM (more stable than HMM):
    - 4 states: Bull-Low Vol, Bull-High Vol, Bear-Low Vol, Bear-High Vol
    - Uses returns + volatility + momentum
    """
    
    REGIMES = {
        0: {'name': 'BEAR_HIGH_VOL', 'action': 'HEDGE', 'position': -0.5},
        1: {'name': 'BEAR_LOW_VOL', 'action': 'CASH', 'position': 0},
        2: {'name': 'BULL_LOW_VOL', 'action': 'FULL_LONG', 'position': 1.0},
        3: {'name': 'BULL_HIGH_VOL', 'action': 'REDUCE', 'position': 0.5}
    }
    
    def __init__(self, n_regimes=4):
        self.n_regimes = n_regimes
        self.model = GaussianMixture(
            n_components=n_regimes,
            covariance_type='diag',
            n_init=3,
            random_state=42
        )
        self.state_mapping = None
        
    def _extract_features(self, prices, vol_window=20, mom_window=10):
        """Extract features: returns, volatility, momentum"""
        prices = np.array(prices).flatten()
        returns = np.diff(prices) / prices[:-1]
        
        # Rolling volatility
        vol = np.array([
            np.std(returns[max(0, i-vol_window):i+1])
            for i in range(len(returns))
        ])
        
        # Momentum (cumulative return over window)
        momentum = np.array([
            np.sum(returns[max(0, i-mom_window):i+1])
            for i in range(len(returns))
        ])
        
        features = np.column_stack([returns, vol, momentum])
        return features
    
    def fit(self, prices):
        """Fit regime model"""
        features = self._extract_features(prices)
        
        # Handle NaN/Inf
        features = np.nan_to_num(features, nan=0, posinf=0, neginf=0)
        
        self.model.fit(features)
        
        # Order states by mean return
        means = self.model.means_[:, 0]
        vols = self.model.means_[:, 1]
        
        # Create state mapping based on return and vol
        state_scores = []
        median_ret = np.median(means)
        median_vol = np.median(vols)
        
        for i in range(self.n_regimes):
            ret_score = 1 if means[i] > median_ret else 0
            vol_score = 1 if vols[i] > median_vol else 0
            state_scores.append((i, ret_score * 2 + vol_score))
            
        state_scores.sort(key=lambda x: x[1])
        self.state_mapping = {old: new for new, (old, _) in enumerate(state_scores)}
        
        return self
    
    def predict(self, prices):
        """Predict current regime"""
        features = self._extract_features(prices)
        features = np.nan_to_num(features, nan=0, posinf=0, neginf=0)
        
        states = self.model.predict(features)
        probs = self.model.predict_proba(features)
        
        # Map to ordered states
        mapped_states = np.array([self.state_mapping.get(s, 0) for s in states])
        
        current = mapped_states[-1]
        current_probs = probs[-1]
        
        regime_info = self.REGIMES.get(current, self.REGIMES[0])
        
        return {
            'regime': current,
            'regime_name': regime_info['name'],
            'action': regime_info['action'],
            'suggested_position': regime_info['position'],
            'probabilities': {
                self.REGIMES[i]['name']: float(current_probs[list(self.state_mapping.keys())[list(self.state_mapping.values()).index(i)]])
                for i in range(self.n_regimes) if i in self.state_mapping.values()
            },
            'history': mapped_states
        }
    
    def detect_transition(self, prices, lookback=10):
        """Detect regime transitions"""
        result = self.predict(prices)
        history = result['history']
        
        if len(history) < lookback:
            return {'transition': 'INSUFFICIENT_DATA'}
            
        recent = history[-lookback:]
        
        if recent[-1] != recent[-2]:
            from_regime = self.REGIMES.get(recent[-2], {}).get('name', 'UNKNOWN')
            to_regime = self.REGIMES.get(recent[-1], {}).get('name', 'UNKNOWN')
            return {
                'transition': 'REGIME_CHANGE',
                'from': from_regime,
                'to': to_regime,
                'urgency': 'HIGH'
            }
            
        unique_regimes = len(set(recent))
        if unique_regimes > 2:
            return {
                'transition': 'UNSTABLE',
                'unique_regimes': unique_regimes,
                'urgency': 'MEDIUM'
            }
            
        return {
            'transition': 'STABLE',
            'current_regime': result['regime_name'],
            'urgency': 'LOW'
        }
    
    def get_signal(self, prices):
        """Generate trading signal from regime"""
        try:
            self.fit(prices)
            result = self.predict(prices)
            transition = self.detect_transition(prices)
            
            signal = result['suggested_position']
            
            if transition['transition'] == 'REGIME_CHANGE':
                signal *= 0.7
            elif transition['transition'] == 'UNSTABLE':
                signal *= 0.5
                
            confidence = max(result['probabilities'].values()) if result['probabilities'] else 0.5
            
            return {
                'signal': float(signal),
                'confidence': float(confidence),
                'regime': result['regime_name'],
                'action': result['action'],
                'transition': transition
            }
        except Exception as e:
            return {
                'signal': 0,
                'confidence': 0.5,
                'regime': 'UNKNOWN',
                'action': 'HOLD',
                'transition': {'transition': 'ERROR', 'error': str(e)}
            }
