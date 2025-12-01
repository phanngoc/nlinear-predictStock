"""VAR (Vector AutoRegression) Model"""
import numpy as np
import pandas as pd
from statsmodels.tsa.api import VAR
from statsmodels.tsa.vector_ar.vecm import VECM, coint_johansen
import warnings
warnings.filterwarnings('ignore')


class VARModel:
    """
    VAR/VECM for multivariate time series forecasting
    - Capture cross-asset dynamics
    - Forecast multiple assets simultaneously
    - Impulse response analysis
    """
    
    def __init__(self, max_lags=10):
        self.max_lags = max_lags
        self.model = None
        self.fitted = None
        
    def fit(self, returns_df, auto_lag=True):
        """
        Fit VAR model
        
        Args:
            returns_df: DataFrame of returns
            auto_lag: auto-select optimal lag
        """
        self.columns = returns_df.columns.tolist()
        
        model = VAR(returns_df)
        
        if auto_lag:
            # Select optimal lag using AIC
            try:
                lag_order = model.select_order(maxlags=self.max_lags)
                optimal_lag = lag_order.aic
                # Ensure lag is at least 1
                if optimal_lag is None or optimal_lag < 1:
                    optimal_lag = 1
            except:
                optimal_lag = 1
        else:
            optimal_lag = 1
            
        self.fitted = model.fit(max(optimal_lag, 1))
        self.lag_order = max(optimal_lag, 1)
        
        return self
    
    def forecast(self, steps=5):
        """
        Forecast future returns
        
        Returns:
            DataFrame: forecasted returns for each asset
        """
        if self.fitted is None:
            raise ValueError("Model not fitted")
        
        # Ensure lag_order is valid
        lag = max(self.lag_order, 1)
        fc = self.fitted.forecast(self.fitted.endog[-lag:], steps=steps)
        
        return pd.DataFrame(fc, columns=self.columns)
    
    def impulse_response(self, periods=10):
        """
        Impulse Response Function
        - How does shock to one asset affect others?
        """
        irf = self.fitted.irf(periods=periods)
        return irf
    
    def variance_decomposition(self, periods=10):
        """
        Forecast Error Variance Decomposition
        - How much of asset's variance is explained by other assets?
        """
        fevd = self.fitted.fevd(periods=periods)
        return fevd
    
    def get_signal(self, returns_df, target_asset, steps=5):
        """
        Generate trading signal for target asset
        """
        self.fit(returns_df)
        forecast = self.forecast(steps=steps)
        
        if target_asset not in forecast.columns:
            return {'signal': 0, 'confidence': 0}
            
        # Cumulative expected return
        cum_return = forecast[target_asset].sum()
        
        # Signal based on expected return
        signal = np.tanh(cum_return * 50)  # Scale
        
        # Confidence from model fit
        r2 = 1 - (self.fitted.resid.var() / returns_df.var()).mean()
        confidence = max(0, min(r2, 1))
        
        return {
            'signal': float(signal),
            'confidence': float(confidence),
            'forecast': forecast[target_asset].tolist(),
            'cum_return': float(cum_return),
            'lag_order': self.lag_order
        }


class VECMModel:
    """
    VECM for cointegrated series
    - Better for price levels (not returns)
    - Captures long-run equilibrium relationships
    """
    
    def __init__(self, det_order=0, k_ar_diff=1):
        self.det_order = det_order
        self.k_ar_diff = k_ar_diff
        self.model = None
        
    def test_cointegration(self, prices_df, significance=0.05):
        """
        Johansen cointegration test
        """
        result = coint_johansen(prices_df, det_order=self.det_order, k_ar_diff=self.k_ar_diff)
        
        # Number of cointegrating relationships
        trace_stat = result.lr1
        crit_values = result.cvt[:, 1]  # 5% critical values
        
        n_coint = sum(trace_stat > crit_values)
        
        return {
            'n_cointegrating': n_coint,
            'trace_stats': trace_stat.tolist(),
            'critical_values': crit_values.tolist(),
            'is_cointegrated': n_coint > 0
        }
    
    def fit(self, prices_df):
        """Fit VECM model"""
        coint_test = self.test_cointegration(prices_df)
        
        if not coint_test['is_cointegrated']:
            return None
            
        self.model = VECM(prices_df, k_ar_diff=self.k_ar_diff, 
                          coint_rank=coint_test['n_cointegrating'])
        self.fitted = self.model.fit()
        
        return self
    
    def get_equilibrium_deviation(self, prices_df):
        """
        Calculate deviation from long-run equilibrium
        - Positive = overvalued relative to equilibrium
        - Negative = undervalued
        """
        if self.fitted is None:
            return None
            
        # Cointegrating vectors
        beta = self.fitted.beta
        
        # Current deviation
        deviation = prices_df.iloc[-1].values @ beta
        
        return deviation
