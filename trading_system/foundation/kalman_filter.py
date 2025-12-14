"""Kalman Filter for noise filtering and true price estimation"""
import numpy as np


class KalmanFilter:
    """
    Kalman Filter for financial time series
    - Lọc noise từ price data
    - Estimate "true" underlying price
    - Detect deviation = trading opportunity
    """
    
    def __init__(self, process_variance=1e-5, measurement_variance=0.1):
        """
        Args:
            process_variance: Q - how much we expect price to change
            measurement_variance: R - how noisy is our measurement
        """
        self.Q = process_variance
        self.R = measurement_variance
        self.x = None  # State estimate
        self.P = 1.0   # Estimate uncertainty
        
    def reset(self, initial_value=None):
        """Reset filter state"""
        self.x = initial_value
        self.P = 1.0
        
    def update(self, measurement):
        """
        Single Kalman update step
        Returns: filtered value, uncertainty
        """
        if self.x is None:
            self.x = measurement
            return self.x, self.P
            
        # Predict
        x_pred = self.x
        P_pred = self.P + self.Q
        
        # Update
        K = P_pred / (P_pred + self.R)  # Kalman gain
        self.x = x_pred + K * (measurement - x_pred)
        self.P = (1 - K) * P_pred
        
        return self.x, self.P
    
    def filter_series(self, prices):
        """
        Filter entire price series
        Returns:
            dict: {
                'filtered': smoothed prices,
                'uncertainty': P values,
                'deviation': actual - filtered
            }
        """
        prices = np.array(prices).flatten()
        n = len(prices)
        
        filtered = np.zeros(n)
        uncertainty = np.zeros(n)
        
        self.reset(prices[0])
        
        for i, price in enumerate(prices):
            filtered[i], uncertainty[i] = self.update(price)
            
        deviation = prices - filtered
        
        return {
            'filtered': filtered,
            'uncertainty': uncertainty,
            'deviation': deviation
        }
    
    def get_signal(self, prices, lookback=20):
        """
        Generate trading signal từ Kalman deviation
        - Price > filtered + threshold: Overbought (sell signal)
        - Price < filtered - threshold: Oversold (buy signal)
        
        Returns: float [-1, 1]
        """
        result = self.filter_series(prices)
        
        recent_dev = result['deviation'][-lookback:]
        std_dev = np.std(recent_dev)
        current_dev = result['deviation'][-1]
        
        # Z-score of current deviation
        z_score = current_dev / std_dev if std_dev > 0 else 0
        
        # Signal: negative z = oversold = buy, positive z = overbought = sell
        signal = -np.tanh(z_score / 2)  # Normalize to [-1, 1]
        
        # Confidence based on uncertainty
        confidence = 1 - min(result['uncertainty'][-1], 1.0)
        
        return {
            'signal': signal * confidence,
            'z_score': z_score,
            'filtered_price': result['filtered'][-1],
            'actual_price': prices[-1],
            'deviation': current_dev,
            'confidence': confidence
        }


class AdaptiveKalmanFilter(KalmanFilter):
    """
    Adaptive Kalman với dynamic R adjustment
    - Tự điều chỉnh R dựa trên market volatility
    """
    
    def __init__(self, base_R=0.1, vol_window=20):
        super().__init__(measurement_variance=base_R)
        self.base_R = base_R
        self.vol_window = vol_window
        self.price_history = []
        
    def update(self, measurement):
        self.price_history.append(measurement)
        
        # Adapt R based on recent volatility
        if len(self.price_history) >= self.vol_window:
            recent = np.array(self.price_history[-self.vol_window:])
            returns = np.diff(recent) / recent[:-1]
            vol = np.std(returns)
            self.R = self.base_R * (1 + vol * 10)  # Higher vol = trust measurement less
            
        return super().update(measurement)
