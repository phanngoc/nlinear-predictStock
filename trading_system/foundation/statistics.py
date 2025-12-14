"""Statistical Analysis: Stationarity, PCA, Covariance Structure"""
import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller, kpss
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


class StationarityTest:
    """
    Test stationarity của time series
    - ADF (Augmented Dickey-Fuller): H0 = non-stationary
    - KPSS: H0 = stationary
    
    Trading implication:
    - Stationary: Mean reversion strategies work
    - Non-stationary: Trend following strategies
    """
    
    @staticmethod
    def adf_test(series, significance=0.05):
        """
        ADF Test
        Returns: dict with test results
        """
        series = np.array(series).flatten()
        result = adfuller(series, autolag='AIC')
        
        return {
            'test': 'ADF',
            'statistic': result[0],
            'p_value': result[1],
            'is_stationary': result[1] < significance,
            'critical_values': result[4],
            'lags_used': result[2]
        }
    
    @staticmethod
    def kpss_test(series, significance=0.05):
        """
        KPSS Test
        Returns: dict with test results
        """
        series = np.array(series).flatten()
        result = kpss(series, regression='c', nlags='auto')
        
        return {
            'test': 'KPSS',
            'statistic': result[0],
            'p_value': result[1],
            'is_stationary': result[1] > significance,  # Note: opposite of ADF
            'critical_values': result[3]
        }
    
    @staticmethod
    def full_test(series):
        """
        Run both tests and conclude
        Returns: dict with conclusion
        """
        adf = StationarityTest.adf_test(series)
        kpss = StationarityTest.kpss_test(series)
        
        # Interpretation
        if adf['is_stationary'] and kpss['is_stationary']:
            conclusion = 'STATIONARY'
            strategy = 'MEAN_REVERSION'
        elif not adf['is_stationary'] and not kpss['is_stationary']:
            conclusion = 'NON_STATIONARY'
            strategy = 'TREND_FOLLOWING'
        else:
            conclusion = 'INCONCLUSIVE'
            strategy = 'MIXED'
            
        return {
            'adf': adf,
            'kpss': kpss,
            'conclusion': conclusion,
            'recommended_strategy': strategy
        }


class PCAAnalyzer:
    """
    PCA để tìm hidden factors driving returns
    - Factor 1: Usually market factor
    - Factor 2-N: Sector/Style factors
    
    Trading implication:
    - High loading on factor = sensitive to that factor
    - Residual = idiosyncratic return = alpha opportunity
    """
    
    def __init__(self, n_components=5):
        self.n_components = n_components
        self.pca = None
        self.scaler = StandardScaler()
        
    def fit(self, returns_matrix):
        """
        Fit PCA on returns matrix
        Args:
            returns_matrix: DataFrame/array, rows=time, cols=assets
        """
        if isinstance(returns_matrix, pd.DataFrame):
            self.asset_names = returns_matrix.columns.tolist()
            returns_matrix = returns_matrix.values
        else:
            self.asset_names = [f'Asset_{i}' for i in range(returns_matrix.shape[1])]
            
        # Standardize
        scaled = self.scaler.fit_transform(returns_matrix)
        
        # PCA
        n_comp = min(self.n_components, scaled.shape[1])
        self.pca = PCA(n_components=n_comp)
        self.factors = self.pca.fit_transform(scaled)
        
        return self
    
    def get_loadings(self):
        """
        Get factor loadings (how each asset relates to each factor)
        """
        if self.pca is None:
            raise ValueError("Call fit() first")
            
        loadings = pd.DataFrame(
            self.pca.components_.T,
            index=self.asset_names,
            columns=[f'Factor_{i+1}' for i in range(self.pca.n_components_)]
        )
        return loadings
    
    def get_explained_variance(self):
        """Get variance explained by each factor"""
        return {
            'individual': self.pca.explained_variance_ratio_,
            'cumulative': np.cumsum(self.pca.explained_variance_ratio_)
        }
    
    def get_residuals(self, returns_matrix):
        """
        Get residuals (idiosyncratic returns)
        High residual = potential alpha
        """
        if isinstance(returns_matrix, pd.DataFrame):
            returns_matrix = returns_matrix.values
            
        scaled = self.scaler.transform(returns_matrix)
        reconstructed = self.pca.inverse_transform(self.pca.transform(scaled))
        residuals = scaled - reconstructed
        
        return residuals
    
    def detect_anomaly(self, returns_matrix, threshold=2.0):
        """
        Detect anomalies based on residuals
        Returns: dict with anomaly info
        """
        residuals = self.get_residuals(returns_matrix)
        
        # Z-score of residuals
        z_scores = np.abs(residuals[-1]) / np.std(residuals, axis=0)
        
        anomalies = {}
        for i, (name, z) in enumerate(zip(self.asset_names, z_scores)):
            if z > threshold:
                anomalies[name] = {
                    'z_score': float(z),
                    'residual': float(residuals[-1, i]),
                    'direction': 'OVERVALUED' if residuals[-1, i] > 0 else 'UNDERVALUED'
                }
                
        return anomalies


class CovarianceAnalyzer:
    """
    Analyze covariance structure of returns
    - Correlation matrix
    - Rolling correlation
    - Correlation breakdown detection
    """
    
    @staticmethod
    def correlation_matrix(returns_df):
        """Simple correlation matrix"""
        return returns_df.corr()
    
    @staticmethod
    def rolling_correlation(series1, series2, window=60):
        """Rolling correlation between two series"""
        return series1.rolling(window).corr(series2)
    
    @staticmethod
    def detect_correlation_breakdown(returns_df, window=60, threshold=0.3):
        """
        Detect when correlations break down (regime change signal)
        """
        corr_now = returns_df.iloc[-window:].corr()
        corr_prev = returns_df.iloc[-2*window:-window].corr()
        
        diff = np.abs(corr_now - corr_prev)
        
        # Find pairs with significant correlation change
        breakdowns = []
        n = len(diff.columns)
        for i in range(n):
            for j in range(i+1, n):
                if diff.iloc[i, j] > threshold:
                    breakdowns.append({
                        'pair': (diff.columns[i], diff.columns[j]),
                        'change': float(diff.iloc[i, j]),
                        'corr_now': float(corr_now.iloc[i, j]),
                        'corr_prev': float(corr_prev.iloc[i, j])
                    })
                    
        return {
            'breakdowns': breakdowns,
            'is_regime_change': len(breakdowns) > n * 0.1  # >10% pairs changed
        }
