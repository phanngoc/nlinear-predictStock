"""Trading Engine - Integrate all 5 phases"""
import numpy as np
import pandas as pd
from typing import Dict, Optional

try:
    from .foundation import FoundationSignals
    from .network import NetworkSignals
    from .multivariate import MultivariateSignals
    from .pattern import PatternSignals
    from .crypto import CryptoSignals
    from .core import SignalAggregator, RiskManager
except ImportError:
    from foundation import FoundationSignals
    from network import NetworkSignals
    from multivariate import MultivariateSignals
    from pattern import PatternSignals
    from crypto import CryptoSignals
    from core import SignalAggregator, RiskManager


class TradingEngine:
    """
    Main Trading Engine - Integrates all 5 phases
    
    Target: >30% annual return through:
    - Multi-signal confirmation
    - Regime-aware position sizing
    - Risk management
    
    Vietnam Market Optimization:
    - Adaptive weights based on market regime
    - Higher emphasis on regime detection (retail-dominated)
    - Enhanced lead-lag analysis (low liquidity market)
    - Mean reversion signals for sideways markets
    """
    
    def __init__(self, phase_weights: Optional[Dict] = None, adaptive: bool = True):
        # Signal modules
        self.foundation = FoundationSignals()
        self.network = NetworkSignals()
        self.multivariate = MultivariateSignals()
        self.pattern = PatternSignals()
        self.crypto = CryptoSignals()
        
        # Core modules with adaptive weights
        self.aggregator = SignalAggregator(phase_weights, adaptive=adaptive)
        self.risk_manager = RiskManager()
        self.adaptive = adaptive
        
        # Default weights optimized for Vietnam market
        self.phase_weights = phase_weights or {
            'foundation': 0.25,
            'network': 0.25,
            'multivariate': 0.15,
            'pattern': 0.35
        }
        
    def prepare_data(self, prices_df: pd.DataFrame) -> Dict:
        """
        Prepare data for analysis
        """
        # Calculate returns
        returns_df = prices_df.pct_change().dropna()
        
        return {
            'prices': prices_df,
            'returns': returns_df
        }
    
    def generate_signal(self, prices_df: pd.DataFrame, target_asset: str,
                        include_crypto: bool = False) -> Dict:
        """
        Generate comprehensive trading signal for target asset
        
        Args:
            prices_df: DataFrame with price data for multiple assets
            target_asset: Asset to generate signal for
            include_crypto: Include crypto-specific analysis
            
        Returns:
            Complete trading recommendation
        """
        if target_asset not in prices_df.columns:
            return {'error': f'{target_asset} not in data'}
            
        data = self.prepare_data(prices_df)
        prices = data['prices']
        returns = data['returns']
        
        signals = {}
        
        # Foundation Module
        try:
            signals['foundation'] = self.foundation.generate(
                prices[target_asset].values
            )
        except Exception as e:
            signals['foundation'] = {'signal': 0, 'confidence': 0, 'error': str(e)}
            
        # Network Module
        try:
            signals['network'] = self.network.generate(returns, target_asset)
        except Exception as e:
            signals['network'] = {'signal': 0, 'confidence': 0, 'error': str(e)}
            
        # Multivariate Module
        try:
            signals['multivariate'] = self.multivariate.generate(returns, target_asset)
        except Exception as e:
            signals['multivariate'] = {'signal': 0, 'confidence': 0, 'error': str(e)}
            
        # Pattern Module
        try:
            signals['pattern'] = self.pattern.generate(prices, returns, target_asset)
        except Exception as e:
            signals['pattern'] = {'signal': 0, 'confidence': 0, 'error': str(e)}
            
        # Crypto Module (optional)
        if include_crypto:
            signals['crypto'] = self.crypto.get_placeholder_signal()
        
        # Get regime for adaptive weights
        regime = signals.get('pattern', {}).get('regime', 'UNKNOWN')
        
        # Aggregate signals with adaptive weights based on regime
        aggregated = self.aggregator.aggregate(signals, regime=regime)
        
        # Risk management
        current_price = prices[target_asset].iloc[-1]
        volatility = returns[target_asset].std()
        
        position = self.risk_manager.calculate_position_size(
            aggregated['composite_signal'],
            aggregated['confidence'],
            current_price
        )
        
        stop_loss = self.risk_manager.calculate_stop_loss(
            current_price, volatility
        )
        
        # Get regime for context
        regime = signals.get('pattern', {}).get('regime', 'UNKNOWN')
        
        return {
            'asset': target_asset,
            'signal': aggregated['composite_signal'],
            'confidence': aggregated['confidence'],
            'action': aggregated['action'],
            'regime': regime,
            'position': position,
            'risk': stop_loss,
            'weights_used': aggregated.get('weights_used', self.phase_weights),
            'phase_signals': {
                phase: {
                    'signal': s.get('signal', 0),
                    'confidence': s.get('confidence', 0)
                }
                for phase, s in signals.items()
            },
            'details': signals
        }
    
    def scan_market(self, prices_df: pd.DataFrame, top_n: int = 5) -> Dict:
        """
        Scan all assets and rank by opportunity
        """
        opportunities = []
        
        for asset in prices_df.columns:
            try:
                result = self.generate_signal(prices_df, asset)
                if 'error' not in result:
                    opportunities.append({
                        'asset': asset,
                        'signal': result['signal'],
                        'confidence': result['confidence'],
                        'action': result['action'],
                        'regime': result['regime'],
                        'score': abs(result['signal'] * result['confidence'])
                    })
            except:
                continue
                
        # Sort by score
        opportunities.sort(key=lambda x: x['score'], reverse=True)
        
        return {
            'buy_opportunities': [o for o in opportunities if o['signal'] > 0.3][:top_n],
            'sell_opportunities': [o for o in opportunities if o['signal'] < -0.3][:top_n],
            'all_rankings': opportunities
        }
    
    def backtest_signal(self, prices_df: pd.DataFrame, target_asset: str,
                        lookback: int = 252) -> Dict:
        """
        Simple backtest of signal quality
        """
        if len(prices_df) < lookback + 60:
            return {'error': 'Insufficient data for backtest'}
            
        results = []
        
        for i in range(lookback, len(prices_df) - 5):
            # Generate signal at time i
            subset = prices_df.iloc[:i]
            signal_result = self.generate_signal(subset, target_asset)
            
            if 'error' in signal_result:
                continue
                
            signal = signal_result['signal']
            
            # Actual return over next 5 days
            future_return = (
                prices_df[target_asset].iloc[i+5] / 
                prices_df[target_asset].iloc[i] - 1
            )
            
            # Check if signal was correct
            correct = (signal > 0 and future_return > 0) or (signal < 0 and future_return < 0)
            
            results.append({
                'signal': signal,
                'actual_return': future_return,
                'correct': correct
            })
            
        if not results:
            return {'error': 'No valid signals generated'}
            
        # Calculate metrics
        win_rate = np.mean([r['correct'] for r in results])
        avg_return = np.mean([r['actual_return'] for r in results])
        
        # Signal-weighted returns
        weighted_returns = [
            r['signal'] * r['actual_return'] for r in results
        ]
        strategy_return = np.sum(weighted_returns)
        
        return {
            'n_signals': len(results),
            'win_rate': float(win_rate),
            'avg_return': float(avg_return),
            'strategy_return': float(strategy_return),
            'sharpe_estimate': float(np.mean(weighted_returns) / np.std(weighted_returns)) if np.std(weighted_returns) > 0 else 0
        }


def create_engine(weights: Optional[Dict] = None) -> TradingEngine:
    """Factory function to create trading engine"""
    return TradingEngine(weights)
