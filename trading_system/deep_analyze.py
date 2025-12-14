#!/usr/bin/env python
"""Deep Analysis - Detailed breakdown of all phases"""
import sys
import warnings
warnings.filterwarnings('ignore')

from data_loader import VNStockLoader
from foundation import FoundationSignals
from network import NetworkSignals
from multivariate import MultivariateSignals
from pattern import PatternSignals


def deep_analyze(target: str):
    """Deep analysis with all phase details"""
    
    loader = VNStockLoader()
    peers = ['VNM', 'FPT', 'VIC', 'VHM', 'HPG', 'MWG']
    
    if target not in peers:
        peers = [target] + peers[:5]
    
    print(f"\n📊 Deep Analysis: {target}")
    print("=" * 60)
    
    prices_df = loader.load_multiple(peers, days=365)
    returns_df = prices_df.pct_change().dropna()
    
    if len(prices_df) < 60:
        print("❌ Insufficient data")
        return
    
    target_prices = prices_df[target].values
    current_price = target_prices[-1]
    
    print(f"\nCurrent Price: {current_price:,.0f} VND")
    print(f"Data Points: {len(prices_df)}")
    
    # ========== FOUNDATION ==========
    print(f"\n{'='*60}")
    print("📈 FOUNDATION (Time Series)")
    print(f"{'='*60}")
    
    p1 = FoundationSignals()
    r1 = p1.generate(target_prices)
    
    print(f"\n🎯 Composite Signal: {r1['signal']:+.3f}")
    print(f"   Confidence: {r1['confidence']:.1%}")
    print(f"   Action: {r1['action']}")
    print(f"   Regime: {r1['regime']}")
    print(f"   Strategy: {r1['recommended_strategy']}")
    
    comp = r1['components']
    
    print(f"\n   ARIMA:")
    print(f"     Signal: {comp['arima']['signal']:+.3f}")
    print(f"     Direction: {'UP' if comp['arima']['direction'] > 0 else 'DOWN' if comp['arima']['direction'] < 0 else 'FLAT'}")
    print(f"     Expected Change: {comp['arima']['pct_change']*100:+.2f}%")
    
    print(f"\n   Kalman Filter:")
    print(f"     Signal: {comp['kalman']['signal']:+.3f}")
    print(f"     Z-Score: {comp['kalman']['z_score']:+.2f}")
    print(f"     Filtered vs Actual: {comp['kalman']['deviation']:+.2f}")
    
    print(f"\n   HMM Regime:")
    print(f"     Signal: {comp['hmm']['signal']:+.3f}")
    print(f"     Regime: {comp['hmm']['regime']}")
    print(f"     Transition: {comp['hmm']['transition']}")
    probs = comp['hmm']['probabilities']
    print(f"     Probabilities: Bull={probs['bull']:.1%}, Bear={probs['bear']:.1%}, Sideways={probs['sideways']:.1%}")
    
    # ========== NETWORK ==========
    print(f"\n{'='*60}")
    print("🕸️  NETWORK ANALYSIS")
    print(f"{'='*60}")
    
    p2 = NetworkSignals()
    r2 = p2.generate(returns_df, target)
    
    print(f"\n🎯 Composite Signal: {r2['signal']:+.3f}")
    print(f"   Confidence: {r2['confidence']:.1%}")
    
    stats = r2['network_stats']
    print(f"\n   Network Stats:")
    print(f"     Nodes: {stats['nodes']}")
    print(f"     Edges: {stats['edges']}")
    print(f"     Density: {stats['density']:.3f}")
    
    regime = r2['components']['regime']
    print(f"\n   Regime Signal:")
    print(f"     Status: {regime['regime']}")
    print(f"     Density Change: {regime.get('density_change', 0):+.3f}")
    
    print(f"\n   Market Leaders:")
    for leader, score in r2['leaders'][:3]:
        print(f"     {leader}: {score:.3f}")
    
    # ========== MULTIVARIATE ==========
    print(f"\n{'='*60}")
    print("📊 MULTIVARIATE ANALYSIS")
    print(f"{'='*60}")
    
    p3 = MultivariateSignals()
    r3 = p3.generate(returns_df, target)
    
    print(f"\n🎯 Composite Signal: {r3['signal']:+.3f}")
    print(f"   Confidence: {r3['confidence']:.1%}")
    print(f"   Risk Level: {r3['risk_level']}")
    
    var = r3['components']['var']
    print(f"\n   VAR Model:")
    print(f"     Signal: {var['signal']:+.3f}")
    print(f"     Cumulative Return: {var.get('cum_return', 0)*100:+.2f}%")
    
    granger = r3['components']['granger']
    print(f"\n   Granger Causality:")
    print(f"     Signal: {granger['signal']:+.3f}")
    if granger.get('leaders'):
        print(f"     Leading Indicators: {[l[0] for l in granger['leaders'][:3]]}")
    
    copula = r3['components']['copula']
    print(f"\n   Copula (Tail Risk):")
    print(f"     Signal: {copula['signal']:+.3f}")
    print(f"     Risk Level: {copula['risk_level']}")
    
    # ========== PATTERN ==========
    print(f"\n{'='*60}")
    print("🔍 PATTERN HUNTING")
    print(f"{'='*60}")
    
    p4 = PatternSignals()
    r4 = p4.generate(prices_df, returns_df, target)
    
    print(f"\n🎯 Composite Signal: {r4['signal']:+.3f}")
    print(f"   Confidence: {r4['confidence']:.1%}")
    print(f"   Regime: {r4['regime']}")
    print(f"   Action: {r4['regime_action']}")
    
    regime_comp = r4['components']['regime']
    print(f"\n   4-State Regime:")
    print(f"     Current: {regime_comp['regime']}")
    print(f"     Transition: {regime_comp['transition'].get('transition', 'N/A')}")
    
    factor = r4['components']['factor']
    print(f"\n   Factor Model:")
    print(f"     Signal: {factor['signal']:+.3f}")
    print(f"     Z-Score: {factor.get('z_score', 0):+.2f}")
    print(f"     Interpretation: {factor.get('interpretation', 'N/A')}")
    
    anomaly = r4['components']['anomaly']
    print(f"\n   Anomaly Detection:")
    print(f"     Signal: {anomaly['signal']:+.3f}")
    print(f"     Anomalies Found: {anomaly.get('n_anomalies', 0)}")
    
    # ========== SUMMARY ==========
    print(f"\n{'='*60}")
    print("📋 SUMMARY")
    print(f"{'='*60}")
    
    signals = {
        'Phase 1 (Foundation)': r1['signal'],
        'Phase 2 (Network)': r2['signal'],
        'Phase 3 (Multivariate)': r3['signal'],
        'Phase 4 (Pattern)': r4['signal']
    }
    
    print(f"\n   Phase Signals:")
    for name, sig in signals.items():
        bar = "█" * int(abs(sig) * 20) if sig != 0 else "░"
        direction = "+" if sig > 0 else "-" if sig < 0 else " "
        print(f"     {name:25}: {direction}{bar:20} ({sig:+.3f})")
    
    # Weighted average
    weights = [0.25, 0.20, 0.20, 0.35]
    composite = sum(s * w for s, w in zip(signals.values(), weights))
    
    print(f"\n   Final Composite: {composite:+.3f}")
    
    if composite > 0.3:
        recommendation = "🟢 BUY"
    elif composite < -0.3:
        recommendation = "🔴 SELL"
    else:
        recommendation = "⚪ HOLD"
    
    print(f"   Recommendation: {recommendation}")


if __name__ == '__main__':
    target = sys.argv[1].upper() if len(sys.argv) > 1 else 'VNM'
    deep_analyze(target)
