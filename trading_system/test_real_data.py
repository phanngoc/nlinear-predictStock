"""Test Trading System with Real VN Stock Data"""
import sys
import warnings
warnings.filterwarnings('ignore')

from data_loader import VNStockLoader, BLUECHIP_SYMBOLS
from trading_engine import TradingEngine


def test_single_stock():
    """Test signal generation for single stock"""
    print("=" * 60)
    print("TEST: Single Stock Analysis (VNM)")
    print("=" * 60)
    
    loader = VNStockLoader()
    
    # Load VNM with 1 year data
    print("\nLoading VNM data...")
    df = loader.load_single('VNM', days=365)
    
    if df is None or len(df) == 0:
        print("Failed to load data")
        return
        
    print(f"Loaded {len(df)} days of data")
    print(f"Date range: {df.index[0]} to {df.index[-1]}")
    print(f"Price range: {df['close'].min():.0f} - {df['close'].max():.0f}")
    
    # Create engine and generate signal
    engine = TradingEngine()
    
    # Need multiple stocks for network analysis
    print("\nLoading additional stocks for network analysis...")
    symbols = ['VNM', 'FPT', 'VIC', 'VHM', 'HPG']
    prices_df = loader.load_multiple(symbols, days=365)
    
    if len(prices_df) < 100:
        print(f"Insufficient data: {len(prices_df)} rows")
        return
        
    print(f"\nGenerating signal for VNM...")
    result = engine.generate_signal(prices_df, 'VNM')
    
    print(f"\n{'='*40}")
    print(f"TRADING SIGNAL FOR VNM")
    print(f"{'='*40}")
    print(f"Signal:     {result['signal']:.3f}")
    print(f"Confidence: {result['confidence']:.3f}")
    print(f"Action:     {result['action']}")
    print(f"Regime:     {result['regime']}")
    
    print(f"\nPhase Signals:")
    for phase, sig in result['phase_signals'].items():
        print(f"  {phase:15}: signal={sig['signal']:+.3f}, conf={sig['confidence']:.3f}")
    
    print(f"\nPosition Recommendation:")
    pos = result['position']
    print(f"  Direction:    {pos['direction']}")
    print(f"  Position %:   {pos['position_pct']:.2%}")
    print(f"  Dollar Amount: ${pos['dollar_amount']:,.0f}")
    
    print(f"\nRisk Management:")
    risk = result['risk']
    current_price = prices_df['VNM'].iloc[-1]
    print(f"  Current Price: {current_price:,.0f} VND")
    print(f"  Stop Loss:     {risk['stop_loss']:,.0f} VND ({(risk['stop_loss']/current_price-1)*100:+.1f}%)")
    print(f"  Take Profit:   {risk['take_profit']:,.0f} VND ({(risk['take_profit']/current_price-1)*100:+.1f}%)")


def test_market_scan():
    """Scan multiple stocks for opportunities"""
    print("\n" + "=" * 60)
    print("TEST: Market Scan")
    print("=" * 60)
    
    loader = VNStockLoader()
    symbols = ['VNM', 'FPT', 'VIC', 'VHM', 'HPG', 'MWG', 'PNJ', 'REE']
    
    print(f"\nLoading {len(symbols)} stocks...")
    prices_df = loader.load_multiple(symbols, days=365)
    
    if len(prices_df) < 100:
        print("Insufficient data")
        return
        
    print(f"Data: {len(prices_df)} days, {len(prices_df.columns)} stocks")
    
    engine = TradingEngine()
    scan = engine.scan_market(prices_df, top_n=5)
    
    print(f"\n{'='*40}")
    print("BUY OPPORTUNITIES")
    print(f"{'='*40}")
    if scan['buy_opportunities']:
        for opp in scan['buy_opportunities']:
            print(f"  {opp['asset']:5} | Signal: {opp['signal']:+.3f} | "
                  f"Conf: {opp['confidence']:.2f} | Regime: {opp['regime']}")
    else:
        print("  No strong buy signals")
    
    print(f"\n{'='*40}")
    print("SELL OPPORTUNITIES")
    print(f"{'='*40}")
    if scan['sell_opportunities']:
        for opp in scan['sell_opportunities']:
            print(f"  {opp['asset']:5} | Signal: {opp['signal']:+.3f} | "
                  f"Conf: {opp['confidence']:.2f} | Regime: {opp['regime']}")
    else:
        print("  No strong sell signals")
    
    print(f"\n{'='*40}")
    print("ALL RANKINGS")
    print(f"{'='*40}")
    for i, opp in enumerate(scan['all_rankings'], 1):
        print(f"  {i}. {opp['asset']:5} | {opp['action']:4} | "
              f"Score: {opp['score']:.3f} | Regime: {opp['regime']}")


def test_detailed_analysis():
    """Detailed analysis of a single stock"""
    print("\n" + "=" * 60)
    print("TEST: Detailed Phase Analysis (FPT)")
    print("=" * 60)
    
    loader = VNStockLoader()
    symbols = ['VNM', 'FPT', 'VIC', 'VHM', 'HPG']
    
    print("\nLoading data...")
    prices_df = loader.load_multiple(symbols, days=365)
    
    if len(prices_df) < 100:
        print("Insufficient data")
        return
    
    engine = TradingEngine()
    result = engine.generate_signal(prices_df, 'FPT')
    
    details = result['details']
    
    # Phase 1
    print(f"\n--- Foundation ---")
    p1 = details.get('foundation', {})
    if 'components' in p1:
        comp = p1['components']
        print(f"ARIMA:  signal={comp.get('arima', {}).get('signal', 0):.3f}")
        print(f"Kalman: signal={comp.get('kalman', {}).get('signal', 0):.3f}")
        print(f"HMM:    signal={comp.get('hmm', {}).get('signal', 0):.3f}, "
              f"regime={comp.get('hmm', {}).get('regime', 'N/A')}")
    
    # Phase 2
    print(f"\n--- Network ---")
    p2 = details.get('network', {})
    stats = p2.get('network_stats', {})
    print(f"Network Density: {stats.get('density', 0):.3f}")
    print(f"Nodes: {stats.get('nodes', 0)}, Edges: {stats.get('edges', 0)}")
    
    # Phase 3
    print(f"\n--- Multivariate ---")
    p3 = details.get('multivariate', {})
    print(f"Risk Level: {p3.get('risk_level', 'N/A')}")
    leaders = p3.get('leading_indicators', [])
    if leaders:
        print(f"Leading Indicators: {[l[0] for l in leaders[:3]]}")
    
    # Phase 4
    print(f"\n--- Pattern ---")
    p4 = details.get('pattern', {})
    print(f"Regime: {p4.get('regime', 'N/A')}")
    print(f"Action: {p4.get('regime_action', 'N/A')}")


def main():
    print("\n" + "=" * 60)
    print("TRADING SYSTEM - REAL DATA TEST")
    print("Using vnstock for Vietnam Stock Market")
    print("=" * 60)
    
    test_single_stock()
    test_market_scan()
    test_detailed_analysis()
    
    print("\n" + "=" * 60)
    print("TEST COMPLETED!")
    print("=" * 60)


if __name__ == '__main__':
    main()
