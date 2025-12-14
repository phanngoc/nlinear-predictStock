"""Copula Models for Dependency Structure"""
import numpy as np
from scipy import stats
from scipy.optimize import minimize


class CopulaModel:
    """
    Copula models để capture tail dependencies
    - Gaussian Copula: Normal dependency
    - Clayton Copula: Lower tail dependency (crashes)
    - Gumbel Copula: Upper tail dependency (rallies)
    
    Trading implication:
    - High tail dependency = diversification fails in extremes
    """
    
    def __init__(self, copula_type='gaussian'):
        self.copula_type = copula_type
        self.params = None
        
    def _to_uniform(self, data):
        """Transform data to uniform [0,1] using empirical CDF"""
        n = len(data)
        ranks = stats.rankdata(data)
        return ranks / (n + 1)
    
    def fit(self, series1, series2):
        """
        Fit copula to two series
        """
        u1 = self._to_uniform(series1)
        u2 = self._to_uniform(series2)
        
        if self.copula_type == 'gaussian':
            self.params = self._fit_gaussian(u1, u2)
        elif self.copula_type == 'clayton':
            self.params = self._fit_clayton(u1, u2)
        elif self.copula_type == 'gumbel':
            self.params = self._fit_gumbel(u1, u2)
            
        return self
    
    def _fit_gaussian(self, u1, u2):
        """Fit Gaussian copula - estimate correlation"""
        z1 = stats.norm.ppf(u1)
        z2 = stats.norm.ppf(u2)
        rho = np.corrcoef(z1, z2)[0, 1]
        return {'rho': rho}
    
    def _fit_clayton(self, u1, u2):
        """Fit Clayton copula - lower tail dependency"""
        def neg_log_likelihood(theta):
            if theta <= 0:
                return 1e10
            c = (1 + theta) * (u1 * u2) ** (-1 - theta)
            c *= (u1 ** (-theta) + u2 ** (-theta) - 1) ** (-2 - 1/theta)
            return -np.sum(np.log(np.maximum(c, 1e-10)))
        
        result = minimize(neg_log_likelihood, x0=1.0, method='Nelder-Mead')
        theta = max(result.x[0], 0.01)
        
        # Lower tail dependency coefficient
        lambda_l = 2 ** (-1/theta)
        
        return {'theta': theta, 'lower_tail_dep': lambda_l}
    
    def _fit_gumbel(self, u1, u2):
        """Fit Gumbel copula - upper tail dependency"""
        def neg_log_likelihood(theta):
            if theta < 1:
                return 1e10
            lu1 = -np.log(u1)
            lu2 = -np.log(u2)
            A = (lu1 ** theta + lu2 ** theta) ** (1/theta)
            return -np.sum(-A + (theta - 1) * np.log(lu1 * lu2))
        
        result = minimize(neg_log_likelihood, x0=2.0, method='Nelder-Mead')
        theta = max(result.x[0], 1.01)
        
        # Upper tail dependency coefficient
        lambda_u = 2 - 2 ** (1/theta)
        
        return {'theta': theta, 'upper_tail_dep': lambda_u}
    
    def get_tail_dependency(self, series1, series2):
        """
        Estimate both lower and upper tail dependencies
        """
        # Fit Clayton for lower tail
        self.copula_type = 'clayton'
        self.fit(series1, series2)
        lower = self.params.get('lower_tail_dep', 0)
        
        # Fit Gumbel for upper tail
        self.copula_type = 'gumbel'
        self.fit(series1, series2)
        upper = self.params.get('upper_tail_dep', 0)
        
        return {
            'lower_tail': lower,
            'upper_tail': upper,
            'asymmetry': upper - lower
        }
    
    def get_risk_signal(self, returns_df, target_asset):
        """
        Generate risk signal based on tail dependencies
        High lower tail dep = high crash risk
        """
        if target_asset not in returns_df.columns:
            return {'signal': 0, 'risk_level': 'UNKNOWN'}
            
        target = returns_df[target_asset].values
        
        tail_deps = []
        for col in returns_df.columns:
            if col != target_asset:
                td = self.get_tail_dependency(target, returns_df[col].values)
                tail_deps.append(td)
                
        if not tail_deps:
            return {'signal': 0, 'risk_level': 'UNKNOWN'}
            
        avg_lower = np.mean([t['lower_tail'] for t in tail_deps])
        avg_upper = np.mean([t['upper_tail'] for t in tail_deps])
        
        # Risk signal
        if avg_lower > 0.5:
            risk_level = 'HIGH_CRASH_RISK'
            signal = -0.5  # Reduce exposure
        elif avg_lower > 0.3:
            risk_level = 'MODERATE_CRASH_RISK'
            signal = -0.2
        else:
            risk_level = 'LOW_CRASH_RISK'
            signal = 0
            
        return {
            'signal': signal,
            'risk_level': risk_level,
            'avg_lower_tail': avg_lower,
            'avg_upper_tail': avg_upper,
            'confidence': min(avg_lower + avg_upper, 1.0)
        }
