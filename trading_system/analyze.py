#!/usr/bin/env python
"""
Quick Analysis Script - Analyze any VN stock
Usage: python analyze.py VNM
       python analyze.py VNM FPT VIC
"""
import sys
import warnings
warnings.filterwarnings('ignore')

from data_loader import VNStockLoader
from trading_engine import TradingEngine


def analyze_stock(target: str, peers: list = None):
    """Analyze a single stock with context from peers"""
    
    loader = VNStockLoader()
    
    # Default peers if not provided
    if peers is None:
        peers = ['VNM', 'FPT', 'VIC', 'VHM', 'HPG', 'MWG']
    
    # Ensure target is in peers
    if target not in peers:
        peers = [target] + peers[:5]
    
    print(f"\n📊 Loading data for {target} and {len(peers)-1} peers...")
    prices_df = loader.load_multiple(peers, days=365)
    
    if len(prices_df) < 60:
        print("❌ Insufficient data")
        return None
    
    # Get current price info
    current_price = prices_df[target].iloc[-1]
    prev_price = prices_df[target].iloc[-2]
    daily_change = (current_price / prev_price - 1) * 100
    
    # 1-month and 3-month returns
    if len(prices_df) >= 22:
        month_return = (current_price / prices_df[target].iloc[-22] - 1) * 100
    else:
        month_return = 0
        
    if len(prices_df) >= 66:
        quarter_return = (current_price / prices_df[target].iloc[-66] - 1) * 100
    else:
        quarter_return = 0
    
    print(f"\n{'='*50}")
    print(f"📈 {target} - Current Analysis")
    print(f"{'='*50}")
    print(f"Price:    {current_price:,.0f} VND ({daily_change:+.2f}% today)")
    print(f"1-Month:  {month_return:+.1f}%")
    print(f"3-Month:  {quarter_return:+.1f}%")
    
    # Generate signal
    engine = TradingEngine()
    result = engine.generate_signal(prices_df, target)
    
    print(f"\n{'='*50}")
    print(f"🎯 TRADING SIGNAL")
    print(f"{'='*50}")
    
    signal = result['signal']
    confidence = result['confidence']
    action = result['action']
    
    # Signal interpretation
    if signal > 0.5:
        emoji = "🟢🟢"
        strength = "STRONG BUY"
    elif signal > 0.2:
        emoji = "🟢"
        strength = "BUY"
    elif signal > -0.2:
        emoji = "⚪"
        strength = "HOLD"
    elif signal > -0.5:
        emoji = "🔴"
        strength = "SELL"
    else:
        emoji = "🔴🔴"
        strength = "STRONG SELL"
    
    print(f"Signal:     {signal:+.3f} {emoji} {strength}")
    print(f"Confidence: {confidence:.1%}")
    print(f"Regime:     {result['regime']}")
    
    # Module breakdown
    print(f"\n📊 Module Signals:")
    for phase, sig in result['phase_signals'].items():
        s = sig['signal']
        c = sig['confidence']
        bar = "█" * int(abs(s) * 10) if s != 0 else "░"
        direction = "+" if s > 0 else "-" if s < 0 else " "
        print(f"  {phase:12}: {direction}{bar:10} ({s:+.2f})")
    
    # Position sizing
    pos = result['position']
    risk = result['risk']
    
    print(f"\n💰 Position Recommendation:")
    print(f"  Direction:  {pos['direction']}")
    print(f"  Size:       {pos['position_pct']:.1%} of portfolio")
    
    print(f"\n⚠️  Risk Management:")
    print(f"  Stop Loss:   {risk['stop_loss']:,.0f} ({(risk['stop_loss']/current_price-1)*100:+.1f}%)")
    print(f"  Take Profit: {risk['take_profit']:,.0f} ({(risk['take_profit']/current_price-1)*100:+.1f}%)")
    
    return result


def scan_market(symbols: list = None):
    """Scan multiple stocks"""
    
    if symbols is None:
        symbols = ['VNM', 'FPT', 'VIC', 'VHM', 'HPG', 'MWG', 'PNJ', 'REE', 'TCB', 'VCB']
    
    loader = VNStockLoader()
    
    print(f"\n🔍 Scanning {len(symbols)} stocks...")
    prices_df = loader.load_multiple(symbols, days=365)
    
    if len(prices_df) < 60:
        print("❌ Insufficient data")
        return
    
    engine = TradingEngine()
    scan = engine.scan_market(prices_df, top_n=10)
    
    print(f"\n{'='*60}")
    print(f"📊 MARKET SCAN RESULTS")
    print(f"{'='*60}")
    
    print(f"\n🟢 BUY Candidates:")
    if scan['buy_opportunities']:
        for opp in scan['buy_opportunities']:
            print(f"  {opp['asset']:5} | Signal: {opp['signal']:+.2f} | {opp['regime']}")
    else:
        print("  None")
    
    print(f"\n🔴 SELL Candidates:")
    if scan['sell_opportunities']:
        for opp in scan['sell_opportunities']:
            print(f"  {opp['asset']:5} | Signal: {opp['signal']:+.2f} | {opp['regime']}")
    else:
        print("  None")
    
    print(f"\n📋 Full Rankings:")
    print(f"  {'Rank':<5} {'Stock':<6} {'Action':<6} {'Signal':>8} {'Regime':<15}")
    print(f"  {'-'*45}")
    for i, opp in enumerate(scan['all_rankings'], 1):
        print(f"  {i:<5} {opp['asset']:<6} {opp['action']:<6} {opp['signal']:>+8.3f} {opp['regime']:<15}")


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python analyze.py VNM          # Analyze single stock")
        print("  python analyze.py VNM FPT VIC  # Analyze with specific peers")
        print("  python analyze.py --scan       # Scan market")
        return
    
    if sys.argv[1] == '--scan':
        symbols = sys.argv[2:] if len(sys.argv) > 2 else None
        scan_market(symbols)
    else:
        target = sys.argv[1].upper()
        peers = [s.upper() for s in sys.argv[2:]] if len(sys.argv) > 2 else None
        analyze_stock(target, peers)


if __name__ == '__main__':
    main()
