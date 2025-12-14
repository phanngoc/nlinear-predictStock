"""ARIMA Model for short-term price forecasting"""
import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller
import warnings
warnings.filterwarnings('ignore')


class ARIMAModel:
    """
    ARIMA (AutoRegressive Integrated Moving Average)
    - Dự đoán trend ngắn hạn (1-5 ngày)
    - Auto-select best (p,d,q) parameters
    """
    
    def __init__(self, max_p=5, max_d=2, max_q=5):
        self.max_p = max_p
        self.max_d = max_d
        self.max_q = max_q
        self.model = None
        self.order = None
        
    def _find_d(self, series):
        """Tìm d (differencing order) để đạt stationarity"""
        for d in range(self.max_d + 1):
            diff_series = series if d == 0 else np.diff(series, n=d)
            if len(diff_series) < 20:
                return d
            adf_result = adfuller(diff_series, autolag='AIC')
            if adf_result[1] < 0.05:  # p-value < 0.05 = stationary
                return d
        return self.max_d
    
    def _grid_search(self, series, d):
        """Grid search tìm best (p,q)"""
        best_aic = float('inf')
        best_order = (1, d, 1)
        
        for p in range(self.max_p + 1):
            for q in range(self.max_q + 1):
                if p == 0 and q == 0:
                    continue
                try:
                    model = ARIMA(series, order=(p, d, q))
                    fitted = model.fit()
                    if fitted.aic < best_aic:
                        best_aic = fitted.aic
                        best_order = (p, d, q)
                except:
                    continue
        return best_order
    
    def fit(self, prices, auto_order=True):
        """
        Fit ARIMA model
        Args:
            prices: array-like, historical prices
            auto_order: bool, auto-select (p,d,q) if True
        """
        series = np.array(prices).flatten()
        
        if auto_order:
            d = self._find_d(series)
            self.order = self._grid_search(series, d)
        else:
            self.order = (1, 1, 1)  # default
            
        self.model = ARIMA(series, order=self.order)
        self.fitted = self.model.fit()
        return self
    
    def predict(self, steps=5):
        """
        Dự đoán giá tương lai
        Returns:
            dict: {
                'forecast': array of predicted prices,
                'conf_int': confidence intervals,
                'direction': 1 (up), -1 (down), 0 (sideways)
            }
        """
        if self.fitted is None:
            raise ValueError("Model not fitted. Call fit() first.")
            
        forecast = self.fitted.forecast(steps=steps)
        conf_int = self.fitted.get_forecast(steps=steps).conf_int()
        
        # Direction signal
        fv = self.fitted.fittedvalues
        current = fv.iloc[-1] if hasattr(fv, 'iloc') else fv[-1]
        future = forecast.iloc[-1] if hasattr(forecast, 'iloc') else forecast[-1]
        pct_change = (future - current) / current
        
        if pct_change > 0.01:
            direction = 1  # Bullish
        elif pct_change < -0.01:
            direction = -1  # Bearish
        else:
            direction = 0  # Sideways
            
        return {
            'forecast': np.array(forecast),
            'conf_int': np.array(conf_int),
            'direction': direction,
            'pct_change': pct_change,
            'order': self.order
        }
    
    def get_signal(self, prices, pred_days=5):
        """
        Generate trading signal từ ARIMA
        Returns: float [-1, 1], negative = bearish, positive = bullish
        """
        self.fit(prices)
        result = self.predict(steps=pred_days)
        
        # Signal strength based on confidence
        conf_width = np.mean(result['conf_int'][:, 1] - result['conf_int'][:, 0])
        price_level = np.mean(result['forecast'])
        confidence = 1 - (conf_width / price_level)  # Higher = more confident
        
        signal = result['direction'] * min(confidence, 1.0)
        return {
            'signal': signal,
            'direction': result['direction'],
            'confidence': confidence,
            'forecast': result['forecast'],
            'pct_change': result['pct_change']
        }
