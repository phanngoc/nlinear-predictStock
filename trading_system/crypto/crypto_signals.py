"""Crypto-specific Signals"""
import numpy as np
from typing import Dict, Optional


class CryptoSignals:
    """
    Crypto-specific analysis:
    - On-chain metrics simulation
    - Exchange flow
    - Social sentiment
    
    Note: Real implementation would need API connections
    to on-chain data providers (Glassnode, etc.)
    """
    
    def __init__(self):
        self.exchange_flow_weight = 0.4
        self.whale_activity_weight = 0.3
        self.social_sentiment_weight = 0.3
        
    def analyze_exchange_flow(self, flow_data: Optional[Dict] = None):
        """
        Analyze exchange inflow/outflow
        - Net inflow to exchanges = selling pressure
        - Net outflow = accumulation
        
        Args:
            flow_data: {'inflow': float, 'outflow': float}
        """
        if flow_data is None:
            return {'signal': 0, 'confidence': 0.5, 'status': 'NO_DATA'}
            
        net_flow = flow_data.get('outflow', 0) - flow_data.get('inflow', 0)
        
        # Normalize
        total = flow_data.get('inflow', 1) + flow_data.get('outflow', 1)
        flow_ratio = net_flow / total
        
        signal = np.tanh(flow_ratio * 2)
        
        if flow_ratio > 0.1:
            status = 'ACCUMULATION'
        elif flow_ratio < -0.1:
            status = 'DISTRIBUTION'
        else:
            status = 'NEUTRAL'
            
        return {
            'signal': float(signal),
            'confidence': 0.7,
            'status': status,
            'net_flow': net_flow
        }
    
    def analyze_whale_activity(self, whale_data: Optional[Dict] = None):
        """
        Analyze whale wallet movements
        
        Args:
            whale_data: {'large_txs': int, 'direction': 'buy'/'sell'}
        """
        if whale_data is None:
            return {'signal': 0, 'confidence': 0.5, 'status': 'NO_DATA'}
            
        direction = whale_data.get('direction', 'neutral')
        intensity = min(whale_data.get('large_txs', 0) / 10, 1.0)
        
        if direction == 'buy':
            signal = intensity * 0.8
            status = 'WHALE_ACCUMULATION'
        elif direction == 'sell':
            signal = -intensity * 0.8
            status = 'WHALE_DISTRIBUTION'
        else:
            signal = 0
            status = 'NEUTRAL'
            
        return {
            'signal': float(signal),
            'confidence': intensity,
            'status': status
        }
    
    def analyze_social_sentiment(self, sentiment_data: Optional[Dict] = None):
        """
        Analyze social media sentiment
        
        Args:
            sentiment_data: {'score': float (-1 to 1), 'volume': int}
        """
        if sentiment_data is None:
            return {'signal': 0, 'confidence': 0.5, 'status': 'NO_DATA'}
            
        score = sentiment_data.get('score', 0)
        volume = sentiment_data.get('volume', 0)
        
        # High volume + extreme sentiment = stronger signal
        volume_factor = min(volume / 1000, 1.0)
        
        # Contrarian at extremes
        if abs(score) > 0.8:
            signal = -score * 0.5  # Fade extreme sentiment
            status = 'EXTREME_CONTRARIAN'
        else:
            signal = score * volume_factor * 0.3
            status = 'FOLLOWING_SENTIMENT'
            
        return {
            'signal': float(signal),
            'confidence': volume_factor,
            'status': status
        }
    
    def generate(self, flow_data=None, whale_data=None, sentiment_data=None):
        """
        Generate composite crypto signal
        """
        flow = self.analyze_exchange_flow(flow_data)
        whale = self.analyze_whale_activity(whale_data)
        sentiment = self.analyze_social_sentiment(sentiment_data)
        
        # Weighted composite
        composite = (
            self.exchange_flow_weight * flow['signal'] +
            self.whale_activity_weight * whale['signal'] +
            self.social_sentiment_weight * sentiment['signal']
        )
        
        confidence = (
            self.exchange_flow_weight * flow['confidence'] +
            self.whale_activity_weight * whale['confidence'] +
            self.social_sentiment_weight * sentiment['confidence']
        )
        
        # Check for conflicting signals
        signals = [flow['signal'], whale['signal'], sentiment['signal']]
        if np.std(signals) > 0.5:
            confidence *= 0.7  # Reduce confidence on conflict
            
        return {
            'signal': float(composite),
            'confidence': float(confidence),
            'components': {
                'exchange_flow': flow,
                'whale_activity': whale,
                'social_sentiment': sentiment
            }
        }
    
    def get_placeholder_signal(self):
        """
        Return neutral signal when no crypto data available
        """
        return {
            'signal': 0,
            'confidence': 0,
            'components': {},
            'note': 'Crypto analysis requires external data APIs'
        }
