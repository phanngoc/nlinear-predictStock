"""Factor Model - Hidden Factor Discovery"""
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA, FactorAnalysis
from sklearn.preprocessing import StandardScaler


class FactorModel:
    """
    Statistical Factor Model
    - Extract hidden factors driving returns
    - Calculate factor exposures
    - Generate alpha from residuals
    """
    
    def __init__(self, n_factors=5):
        self.n_factors = n_factors
        self.pca = None
        self.scaler = StandardScaler()
        
    def fit(self, returns_df):
        """
        Fit factor model
        """
        self.asset_names = returns_df.columns.tolist()
        
        # Standardize
        scaled = self.scaler.fit_transform(returns_df)
        
        # PCA
        n_comp = min(self.n_factors, len(self.asset_names))
        self.pca = PCA(n_components=n_comp)
        self.factors = self.pca.fit_transform(scaled)
        
        return self
    
    def get_factor_loadings(self):
        """
        Get factor loadings (beta to each factor)
        """
        loadings = pd.DataFrame(
            self.pca.components_.T,
            index=self.asset_names,
            columns=[f'F{i+1}' for i in range(self.pca.n_components_)]
        )
        return loadings
    
    def get_factor_returns(self):
        """Get factor return series"""
        return pd.DataFrame(
            self.factors,
            columns=[f'F{i+1}' for i in range(self.pca.n_components_)]
        )
    
    def get_explained_variance(self):
        """Variance explained by each factor"""
        return {
            'individual': self.pca.explained_variance_ratio_.tolist(),
            'cumulative': np.cumsum(self.pca.explained_variance_ratio_).tolist()
        }
    
    def get_residuals(self, returns_df):
        """
        Get idiosyncratic returns (alpha potential)
        """
        scaled = self.scaler.transform(returns_df)
        reconstructed = self.pca.inverse_transform(self.pca.transform(scaled))
        residuals = scaled - reconstructed
        
        return pd.DataFrame(residuals, columns=self.asset_names)
    
    def get_factor_exposure(self, asset):
        """Get factor exposure for specific asset"""
        loadings = self.get_factor_loadings()
        if asset not in loadings.index:
            return None
        return loadings.loc[asset].to_dict()
    
    def predict_return(self, factor_forecasts):
        """
        Predict asset returns given factor forecasts
        
        Args:
            factor_forecasts: dict {factor_name: expected_return}
        """
        loadings = self.get_factor_loadings()
        
        predictions = {}
        for asset in self.asset_names:
            pred = 0
            for factor, forecast in factor_forecasts.items():
                if factor in loadings.columns:
                    pred += loadings.loc[asset, factor] * forecast
            predictions[asset] = pred
            
        return predictions
    
    def get_alpha_signal(self, returns_df, target_asset):
        """
        Generate alpha signal from residuals
        - Large negative residual = undervalued = buy
        - Large positive residual = overvalued = sell
        """
        self.fit(returns_df)
        residuals = self.get_residuals(returns_df)
        
        if target_asset not in residuals.columns:
            return {'signal': 0, 'confidence': 0}
            
        target_resid = residuals[target_asset].values
        
        # Z-score of recent residual
        z_score = target_resid[-1] / np.std(target_resid)
        
        # Signal: negative z = undervalued = buy
        signal = -np.tanh(z_score / 2)
        
        # Confidence from explained variance
        exp_var = sum(self.pca.explained_variance_ratio_)
        confidence = exp_var
        
        return {
            'signal': float(signal),
            'confidence': float(confidence),
            'z_score': float(z_score),
            'residual': float(target_resid[-1]),
            'interpretation': 'UNDERVALUED' if z_score < -1 else 'OVERVALUED' if z_score > 1 else 'FAIR'
        }
    
    def rank_by_alpha(self, returns_df):
        """
        Rank all assets by alpha potential
        """
        self.fit(returns_df)
        residuals = self.get_residuals(returns_df)
        
        # Z-scores of latest residuals
        z_scores = residuals.iloc[-1] / residuals.std()
        
        rankings = []
        for asset in self.asset_names:
            z = z_scores[asset]
            rankings.append({
                'asset': asset,
                'z_score': float(z),
                'signal': float(-np.tanh(z / 2)),
                'interpretation': 'UNDERVALUED' if z < -1 else 'OVERVALUED' if z > 1 else 'FAIR'
            })
            
        rankings.sort(key=lambda x: x['signal'], reverse=True)
        return rankings
