"""Hidden Markov Model for Market Regime Detection"""
import numpy as np
from hmmlearn import hmm
import warnings
warnings.filterwarnings('ignore')


class HMMRegimeDetector:
    """
    HMM để detect market regimes:
    - State 0: Bear (downtrend, high vol)
    - State 1: Sideways (no trend, low vol)  
    - State 2: Bull (uptrend, moderate vol)
    
    Trading implication:
    - Bull: Long positions, higher allocation
    - Bear: Cash/Short, reduce exposure
    - Sideways: Mean reversion strategies
    
    Regime Smoothing:
    - Sử dụng rolling window để xác định regime ổn định
    - Chỉ chuyển regime khi confidence > threshold trong nhiều ngày liên tiếp
    - Tránh việc regime nhảy liên tục gây nhiễu signal
    """
    
    REGIMES = {0: 'BEAR', 1: 'SIDEWAYS', 2: 'BULL'}
    
    # Signal mapping cho từng regime (bao gồm cả SIDEWAYS với mean reversion)
    REGIME_BASE_SIGNALS = {
        0: -1.0,  # BEAR: full short/cash
        1: 0.0,   # SIDEWAYS: neutral (sẽ được điều chỉnh bởi mean reversion)
        2: 1.0    # BULL: full long
    }
    
    def __init__(self, n_states=3, n_iter=100, 
                 smoothing_window=5, 
                 confidence_threshold=0.6,
                 min_regime_duration=3):
        """
        Args:
            n_states: Số lượng regime states
            n_iter: Số lần iteration cho HMM
            smoothing_window: Số ngày để tính regime ổn định
            confidence_threshold: Ngưỡng xác suất tối thiểu để confirm regime
            min_regime_duration: Số ngày tối thiểu để confirm chuyển regime
        """
        self.n_states = n_states
        self.smoothing_window = smoothing_window
        self.confidence_threshold = confidence_threshold
        self.min_regime_duration = min_regime_duration
        
        self.model = hmm.GaussianHMM(
            n_components=n_states,
            covariance_type="full",
            n_iter=n_iter,
            random_state=42
        )
        self.fitted = False
        
    def _prepare_features(self, prices, window=20):
        """
        Tạo features cho HMM:
        - Returns
        - Volatility (rolling std)
        """
        prices = np.array(prices).flatten()
        returns = np.diff(prices) / prices[:-1]
        
        # Rolling volatility
        vol = np.array([
            np.std(returns[max(0, i-window):i+1]) 
            for i in range(len(returns))
        ])
        
        # Stack features
        features = np.column_stack([returns, vol])
        return features
    
    def fit(self, prices):
        """Fit HMM on historical prices"""
        features = self._prepare_features(prices)
        self.model.fit(features)
        self.fitted = True
        
        # Sort states by mean return (Bear < Sideways < Bull)
        means = self.model.means_[:, 0]  # Return means
        self.state_order = np.argsort(means)
        
        return self
    
    def predict_regime(self, prices):
        """
        Predict current regime
        Returns:
            dict: {
                'regime': int (0=Bear, 1=Sideways, 2=Bull),
                'regime_name': str,
                'probabilities': array of state probabilities,
                'history': array of historical regimes
            }
        """
        if not self.fitted:
            self.fit(prices)
            
        features = self._prepare_features(prices)
        
        # Predict states
        states = self.model.predict(features)
        probs = self.model.predict_proba(features)
        
        # Map to ordered states
        mapped_states = np.array([
            np.where(self.state_order == s)[0][0] for s in states
        ])
        
        current_state = mapped_states[-1]
        current_probs = probs[-1][self.state_order]
        
        # Map probabilities theo state_order cho toàn bộ history
        mapped_probs = probs[:, self.state_order]
        
        return {
            'regime': int(current_state),
            'regime_name': self.REGIMES[current_state],
            'probabilities': current_probs,
            'history': mapped_states,
            'probs_history': mapped_probs  # Đã được map theo state_order
        }
    
    def _get_smoothed_regime(self, history, probs_history):
        """
        Tính regime đã được làm mịn (smoothed) dựa trên:
        1. Rolling window voting
        2. Confidence threshold
        3. Minimum regime duration
        
        Returns:
            dict: {
                'regime': int,
                'regime_name': str,
                'confidence': float,
                'is_stable': bool,
                'raw_regime': int,
                'dominant_regime': int,
                'regime_consistency': float
            }
        """
        if len(history) < self.smoothing_window:
            # Không đủ data, trả về regime hiện tại
            return {
                'regime': int(history[-1]),
                'regime_name': self.REGIMES[int(history[-1])],
                'confidence': float(probs_history[-1].max()),
                'is_stable': False,
                'raw_regime': int(history[-1]),
                'dominant_regime': int(history[-1]),
                'regime_consistency': 0.0
            }
        
        # Lấy window gần nhất
        recent_regimes = history[-self.smoothing_window:]
        recent_probs = probs_history[-self.smoothing_window:]
        
        # Tính regime phổ biến nhất trong window (voting)
        unique, counts = np.unique(recent_regimes, return_counts=True)
        dominant_idx = np.argmax(counts)
        dominant_regime = int(unique[dominant_idx])
        regime_consistency = counts[dominant_idx] / self.smoothing_window
        
        # Tính average confidence cho dominant regime trong window
        avg_confidence = np.mean([
            probs[dominant_regime] for probs in recent_probs
        ])
        
        # Check stability conditions
        is_stable = (
            regime_consistency >= (self.min_regime_duration / self.smoothing_window) and
            avg_confidence >= self.confidence_threshold
        )
        
        # Nếu không stable, check xem có regime nào đủ mạnh không
        if not is_stable:
            # Tìm regime có confidence cao nhất trung bình
            avg_probs = np.mean(recent_probs, axis=0)
            best_regime = int(np.argmax(avg_probs))
            best_confidence = avg_probs[best_regime]
            
            if best_confidence >= self.confidence_threshold:
                dominant_regime = best_regime
                avg_confidence = best_confidence
                is_stable = True
        
        return {
            'regime': dominant_regime,
            'regime_name': self.REGIMES[dominant_regime],
            'confidence': float(avg_confidence),
            'is_stable': is_stable,
            'raw_regime': int(history[-1]),
            'dominant_regime': dominant_regime,
            'regime_consistency': float(regime_consistency)
        }
    
    def _calculate_mean_reversion_signal(self, prices, window=20):
        """
        Tính signal mean reversion cho SIDEWAYS regime.
        Khi thị trường đi ngang, có thể trade mean reversion:
        - Giá > MA → signal âm (bán)
        - Giá < MA → signal dương (mua)
        
        Returns:
            float: signal từ -1 đến 1
        """
        prices = np.array(prices).flatten()
        if len(prices) < window:
            return 0.0
        
        # Simple moving average
        ma = np.mean(prices[-window:])
        current_price = prices[-1]
        
        # Tính deviation từ MA (dạng z-score)
        std = np.std(prices[-window:])
        if std == 0:
            return 0.0
        
        z_score = (current_price - ma) / std
        
        # Chuyển z-score thành signal (-1 đến 1)
        # z_score > 0 → overvalued → sell signal (âm)
        # z_score < 0 → undervalued → buy signal (dương)
        signal = -np.tanh(z_score * 0.5)  # Dùng tanh để giới hạn trong [-1, 1]
        
        return float(signal)
    
    def get_signal(self, prices):
        """
        Generate trading signal từ regime với smoothing.
        
        Logic:
        - Sử dụng smoothed regime thay vì raw regime
        - BULL: signal dương (long)
        - BEAR: signal âm (short/cash)
        - SIDEWAYS: mean reversion signal (không còn = 0)
        
        Signal strength = base_signal * confidence
        """
        prices = np.array(prices).flatten()
        result = self.predict_regime(prices)
        
        # Lấy smoothed regime
        smoothed = self._get_smoothed_regime(
            result['history'], 
            result['probs_history']
        )
        
        regime = smoothed['regime']
        confidence = smoothed['confidence']
        is_stable = smoothed['is_stable']
        
        # Tính base signal dựa trên regime
        if regime == 2:  # Bull
            base_signal = 1.0
        elif regime == 0:  # Bear
            base_signal = -1.0
        else:  # Sideways
            # Sử dụng mean reversion signal thay vì 0
            base_signal = self._calculate_mean_reversion_signal(prices)
            # Scale down vì sideways nên ít aggressive hơn
            base_signal *= 0.5
        
        # Điều chỉnh signal dựa trên stability
        if is_stable:
            signal = base_signal * confidence
        else:
            # Regime không ổn định → giảm signal strength
            signal = base_signal * confidence * 0.5
        
        # Regime transition detection (dựa trên smoothed regime)
        history = result['history']
        if len(history) >= self.smoothing_window:
            # So sánh regime hiện tại với regime của window trước
            prev_window = history[-(self.smoothing_window*2):-self.smoothing_window]
            if len(prev_window) >= self.min_regime_duration:
                prev_dominant = np.bincount(prev_window.astype(int)).argmax()
                if prev_dominant != regime:
                    transition = 'REGIME_CHANGE'
                else:
                    transition = 'STABLE'
            else:
                transition = 'INSUFFICIENT_DATA'
        else:
            transition = 'INSUFFICIENT_DATA'
        
        return {
            'signal': float(signal),
            'regime': regime,
            'regime_name': smoothed['regime_name'],
            'confidence': confidence,
            'transition': transition,
            'is_stable': is_stable,
            'raw_regime': smoothed['raw_regime'],
            'regime_consistency': smoothed['regime_consistency'],
            'probabilities': {
                'bear': float(result['probabilities'][0]),
                'sideways': float(result['probabilities'][1]),
                'bull': float(result['probabilities'][2])
            },
            'smoothing_info': {
                'window': self.smoothing_window,
                'threshold': self.confidence_threshold,
                'min_duration': self.min_regime_duration
            }
        }
    
    def get_regime_stats(self, prices):
        """Thống kê về các regime"""
        result = self.predict_regime(prices)
        history = result['history']
        
        stats = {}
        for i, name in self.REGIMES.items():
            mask = history == i
            stats[name] = {
                'count': int(np.sum(mask)),
                'pct': float(np.mean(mask)),
                'avg_duration': self._avg_duration(history, i)
            }
        return stats
    
    def _avg_duration(self, history, state):
        """Tính average duration của một state"""
        durations = []
        count = 0
        for s in history:
            if s == state:
                count += 1
            elif count > 0:
                durations.append(count)
                count = 0
        if count > 0:
            durations.append(count)
        return np.mean(durations) if durations else 0
