"""Demo: Full Trading System"""
import numpy as np
import pandas as pd
import sys
import warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '..')

from trading_engine import TradingEngine


def generate_sample_market(n_assets=5, n_days=300):
    """Generate sample market data"""
    np.random.seed(42)
    
    assets = ['VNM', 'FPT', 'VIC', 'VHM', 'HPG'][:n_assets]
    
    # Generate correlated returns
    correlation = np.array([
        [1.0, 0.6, 0.4, 0.5, 0.3],
        [0.6, 1.0, 0.5, 0.4, 0.4],
        [0.4, 0.5, 1.0, 0.7, 0.3],
        [0.5, 0.4, 0.7, 1.0, 0.4],
        [0.3, 0.4, 0.3, 0.4, 1.0]
    ])[:n_assets, :n_assets]
    
    # Cholesky decomposition for correlated returns
    L = np.linalg.cholesky(correlation)
    
    # Generate returns
    uncorrelated = np.random.normal(0.0005, 0.02, (n_days, n_assets))
    correlated_returns = uncorrelated @ L.T
    
    # Convert to prices
    prices = 100 * np.exp(np.cumsum(correlated_returns, axis=0))
    
    dates = pd.date_range(end='2024-01-01', periods=n_days, freq='D')
    
    return pd.DataFrame(prices, index=dates, columns=assets)


def demo_single_asset():
    """Demo: Generate signal for single asset"""
    print("=" * 60)
    print("DEMO: Single Asset Signal Generation")
    print("=" * 60)
    
    prices_df = generate_sample_market()
    engine = TradingEngine()
    
    target = 'VNM'
    result = engine.generate_signal(prices_df, target)
    
    print(f"\nAsset: {result['asset']}")
    print(f"Signal: {result['signal']:.3f}")
    print(f"Confidence: {result['confidence']:.3f}")
    print(f"Action: {result['action']}")
    print(f"Regime: {result['regime']}")
    
    print("\nModule Signals:")
    for phase, sig in result['phase_signals'].items():
        print(f"  {phase}: signal={sig['signal']:.3f}, conf={sig['confidence']:.3f}")
        
    print("\nPosition Sizing:")
    print(f"  Direction: {result['position']['direction']}")
    print(f"  Position %: {result['position']['position_pct']:.2%}")
    print(f"  Dollar Amount: ${result['position']['dollar_amount']:,.0f}")
    
    print("\nRisk Management:")
    print(f"  Stop Loss: ${result['risk']['stop_loss']:.2f}")
    print(f"  Take Profit: ${result['risk']['take_profit']:.2f}")
    print(f"  Risk/Reward: {result['risk']['risk_reward']:.1f}")


def demo_market_scan():
    """Demo: Scan market for opportunities"""
    print("\n" + "=" * 60)
    print("DEMO: Market Scan")
    print("=" * 60)
    
    prices_df = generate_sample_market()
    engine = TradingEngine()
    
    scan = engine.scan_market(prices_df, top_n=3)
    
    print("\nBuy Opportunities:")
    for opp in scan['buy_opportunities']:
        print(f"  {opp['asset']}: signal={opp['signal']:.3f}, "
              f"conf={opp['confidence']:.3f}, regime={opp['regime']}")
        
    print("\nSell Opportunities:")
    for opp in scan['sell_opportunities']:
        print(f"  {opp['asset']}: signal={opp['signal']:.3f}, "
              f"conf={opp['confidence']:.3f}, regime={opp['regime']}")
        
    print("\nAll Rankings:")
    for i, opp in enumerate(scan['all_rankings'][:5], 1):
        print(f"  {i}. {opp['asset']}: {opp['action']} "
              f"(score={opp['score']:.3f})")


def demo_backtest():
    """Demo: Simple backtest"""
    print("\n" + "=" * 60)
    print("DEMO: Backtest")
    print("=" * 60)
    
    prices_df = generate_sample_market(n_days=400)
    engine = TradingEngine()
    
    result = engine.backtest_signal(prices_df, 'VNM', lookback=200)
    
    if 'error' in result:
        print(f"Error: {result['error']}")
        return
        
    print(f"\nBacktest Results for VNM:")
    print(f"  Signals Generated: {result['n_signals']}")
    print(f"  Win Rate: {result['win_rate']:.1%}")
    print(f"  Avg Return: {result['avg_return']:.2%}")
    print(f"  Strategy Return: {result['strategy_return']:.2%}")
    print(f"  Sharpe Estimate: {result['sharpe_estimate']:.2f}")


def demo_module_details():
    """Demo: Detailed module analysis"""
    print("\n" + "=" * 60)
    print("DEMO: Detailed Module Analysis")
    print("=" * 60)
    
    prices_df = generate_sample_market()
    engine = TradingEngine()
    
    result = engine.generate_signal(prices_df, 'FPT')
    
    print("\n--- Foundation ---")
    p1 = result['details'].get('foundation', {})
    print(f"Signal: {p1.get('signal', 'N/A')}")
    print(f"Regime: {p1.get('regime', 'N/A')}")
    print(f"Strategy: {p1.get('recommended_strategy', 'N/A')}")
    
    print("\n--- Network ---")
    p2 = result['details'].get('network', {})
    print(f"Signal: {p2.get('signal', 'N/A')}")
    stats = p2.get('network_stats', {})
    print(f"Network Density: {stats.get('density', 'N/A')}")
    
    print("\n--- Multivariate ---")
    p3 = result['details'].get('multivariate', {})
    print(f"Signal: {p3.get('signal', 'N/A')}")
    print(f"Risk Level: {p3.get('risk_level', 'N/A')}")
    
    print("\n--- Pattern ---")
    p4 = result['details'].get('pattern', {})
    print(f"Signal: {p4.get('signal', 'N/A')}")
    print(f"Regime: {p4.get('regime', 'N/A')}")
    print(f"Action: {p4.get('regime_action', 'N/A')}")


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("ADVANCED TRADING SYSTEM - FULL DEMO")
    print("5 Modules Integration")
    print("=" * 60)
    
    demo_single_asset()
    demo_market_scan()
    demo_backtest()
    demo_module_details()
    
    print("\n" + "=" * 60)
    print("DEMO COMPLETED!")
    print("=" * 60)
