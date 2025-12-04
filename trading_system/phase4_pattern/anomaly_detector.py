"""Anomaly Detection - Cross-asset and Statistical Anomalies"""
import numpy as np
import pandas as pd
from scipy import stats


class AnomalyDetector:
    """
    Detect trading anomalies:
    - Statistical arbitrage opportunities
    - Pair deviations
    - Cross-asset anomalies
    - Liquidity anomalies (important for Vietnam market)
    - Sector rotation signals
    
    Vietnam Market Optimization:
    - Lower z-threshold (1.8) due to higher volatility
    - Sector-based anomaly detection (banking, real estate clusters)
    - Volume-based confirmation for low liquidity market
    """
    
    # Sector mapping for Vietnam market
    VN_SECTORS = {
        'banking': ['VCB', 'BID', 'CTG', 'TCB', 'MBB', 'ACB', 'VPB', 'HDB', 'TPB', 'STB'],
        'real_estate': ['VIC', 'VHM', 'NVL', 'KDH', 'DXG', 'PDR', 'NLG'],
        'retail': ['MWG', 'FRT', 'PNJ', 'DGW'],
        'tech': ['FPT', 'CMG'],
        'steel': ['HPG', 'HSG', 'NKG'],
        'energy': ['GAS', 'POW', 'PVD', 'PVS']
    }
    
    def __init__(self, z_threshold=1.8):  # Lowered for VN market volatility
        self.z_threshold = z_threshold
        
    def detect_pair_anomaly(self, series1, series2, window=60):
        """
        Detect pair trading anomaly (spread deviation)
        """
        s1 = np.array(series1)
        s2 = np.array(series2)
        
        # Calculate spread (ratio)
        spread = s1 / s2
        
        # Rolling mean and std
        if len(spread) < window:
            window = len(spread) // 2
            
        rolling_mean = pd.Series(spread).rolling(window).mean().values
        rolling_std = pd.Series(spread).rolling(window).std().values
        
        # Z-score
        z_score = (spread[-1] - rolling_mean[-1]) / rolling_std[-1]
        
        if abs(z_score) > self.z_threshold:
            if z_score > 0:
                action = 'SHORT_S1_LONG_S2'  # Spread too high
            else:
                action = 'LONG_S1_SHORT_S2'  # Spread too low
            is_anomaly = True
        else:
            action = 'NO_ACTION'
            is_anomaly = False
            
        return {
            'is_anomaly': is_anomaly,
            'z_score': float(z_score),
            'action': action,
            'spread': float(spread[-1]),
            'mean': float(rolling_mean[-1]),
            'std': float(rolling_std[-1])
        }
    
    def scan_pair_anomalies(self, prices_df):
        """
        Scan all pairs for anomalies
        """
        assets = prices_df.columns
        anomalies = []
        
        for i, a1 in enumerate(assets):
            for j, a2 in enumerate(assets):
                if i < j:
                    result = self.detect_pair_anomaly(
                        prices_df[a1].values,
                        prices_df[a2].values
                    )
                    if result['is_anomaly']:
                        anomalies.append({
                            'pair': (a1, a2),
                            **result
                        })
                        
        # Sort by z-score magnitude
        anomalies.sort(key=lambda x: abs(x['z_score']), reverse=True)
        return anomalies
    
    def detect_momentum_anomaly(self, returns_df, lookback=20):
        """
        Detect momentum anomalies (extreme recent performance)
        """
        recent_returns = returns_df.iloc[-lookback:].sum()
        
        # Z-score across assets
        mean_ret = recent_returns.mean()
        std_ret = recent_returns.std()
        z_scores = (recent_returns - mean_ret) / std_ret
        
        anomalies = []
        for asset in returns_df.columns:
            z = z_scores[asset]
            if abs(z) > self.z_threshold:
                anomalies.append({
                    'asset': asset,
                    'z_score': float(z),
                    'return': float(recent_returns[asset]),
                    'type': 'MOMENTUM_WINNER' if z > 0 else 'MOMENTUM_LOSER'
                })
                
        return anomalies
    
    def detect_volatility_anomaly(self, returns_df, window=20):
        """
        Detect volatility anomalies (unusual vol)
        """
        recent_vol = returns_df.iloc[-window:].std()
        historical_vol = returns_df.iloc[:-window].std()
        
        vol_ratio = recent_vol / historical_vol
        
        anomalies = []
        for asset in returns_df.columns:
            ratio = vol_ratio[asset]
            if ratio > 1.5:
                anomalies.append({
                    'asset': asset,
                    'vol_ratio': float(ratio),
                    'type': 'VOL_SPIKE',
                    'action': 'REDUCE_POSITION'
                })
            elif ratio < 0.5:
                anomalies.append({
                    'asset': asset,
                    'vol_ratio': float(ratio),
                    'type': 'VOL_COMPRESSION',
                    'action': 'PREPARE_FOR_BREAKOUT'
                })
                
        return anomalies
    
    def get_anomaly_signal(self, prices_df, returns_df, target_asset):
        """
        Generate signal from anomaly detection
        Optimized for Vietnam market with sector rotation and liquidity signals
        """
        signals = []
        signal_weights = []
        
        # Pair anomalies involving target
        pair_anomalies = self.scan_pair_anomalies(prices_df)
        for anom in pair_anomalies:
            if target_asset in anom['pair']:
                if anom['action'] == 'LONG_S1_SHORT_S2':
                    sig = 0.5 if anom['pair'][0] == target_asset else -0.5
                else:
                    sig = -0.5 if anom['pair'][0] == target_asset else 0.5
                signals.append(sig * min(abs(anom['z_score']) / 3, 1))
                signal_weights.append(1.0)
                
        # Momentum anomaly - with mean reversion for VN market
        mom_anomalies = self.detect_momentum_anomaly(returns_df)
        for anom in mom_anomalies:
            if anom['asset'] == target_asset:
                # Mean reversion: fade extreme momentum (stronger in VN)
                sig = -0.4 if anom['type'] == 'MOMENTUM_WINNER' else 0.4
                signals.append(sig)
                signal_weights.append(1.2)  # Higher weight for momentum in VN
                
        # Volatility anomaly
        vol_anomalies = self.detect_volatility_anomaly(returns_df)
        for anom in vol_anomalies:
            if anom['asset'] == target_asset:
                if anom['type'] == 'VOL_SPIKE':
                    signals.append(-0.3)  # Stronger reduce signal
                    signal_weights.append(1.5)  # High weight for vol spike
                elif anom['type'] == 'VOL_COMPRESSION':
                    signals.append(0.2)  # Prepare for breakout
                    signal_weights.append(0.8)
        
        # Sector rotation signal (VN-specific)
        sector_signal = self._detect_sector_rotation(returns_df, target_asset)
        if sector_signal['signal'] != 0:
            signals.append(sector_signal['signal'])
            signal_weights.append(1.0)
                    
        if not signals:
            return {'signal': 0, 'confidence': 0.5, 'anomalies': []}
        
        # Weighted average of signals
        total_weight = sum(signal_weights)
        composite = sum(s * w for s, w in zip(signals, signal_weights)) / total_weight
        confidence = min(len(signals) * 0.15 + 0.4, 1.0)
        
        return {
            'signal': float(composite),
            'confidence': float(confidence),
            'n_anomalies': len(signals),
            'pair_anomalies': [a for a in pair_anomalies if target_asset in a['pair']],
            'momentum_anomalies': [a for a in mom_anomalies if a['asset'] == target_asset],
            'vol_anomalies': [a for a in vol_anomalies if a['asset'] == target_asset],
            'sector_rotation': sector_signal
        }
    
    def _detect_sector_rotation(self, returns_df, target_asset, lookback=20):
        """
        Detect sector rotation signals for Vietnam market
        If sector is outperforming/underperforming, generate signal
        """
        # Find which sector the target belongs to
        target_sector = None
        sector_stocks = []
        
        for sector, stocks in self.VN_SECTORS.items():
            if target_asset in stocks:
                target_sector = sector
                sector_stocks = [s for s in stocks if s in returns_df.columns]
                break
        
        if not target_sector or len(sector_stocks) < 2:
            return {'signal': 0, 'sector': None, 'relative_strength': 0}
        
        # Calculate sector vs market performance
        recent_returns = returns_df.iloc[-lookback:]
        
        sector_return = recent_returns[sector_stocks].mean(axis=1).sum()
        market_return = recent_returns.mean(axis=1).sum()
        
        relative_strength = sector_return - market_return
        
        # Target vs sector
        target_return = recent_returns[target_asset].sum()
        target_vs_sector = target_return - sector_return
        
        # Generate signal
        signal = 0
        if relative_strength > 0.05:  # Sector outperforming
            if target_vs_sector < -0.03:  # Target lagging sector
                signal = 0.3  # Catch-up trade
            elif target_vs_sector > 0.05:  # Target leading
                signal = -0.2  # Take profit
        elif relative_strength < -0.05:  # Sector underperforming
            if target_vs_sector > 0.03:  # Target outperforming weak sector
                signal = -0.3  # Mean reversion
            elif target_vs_sector < -0.05:  # Target worst in weak sector
                signal = 0.2  # Oversold bounce
        
        return {
            'signal': float(signal),
            'sector': target_sector,
            'relative_strength': float(relative_strength),
            'target_vs_sector': float(target_vs_sector)
        }
