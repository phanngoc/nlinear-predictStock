"""Test Foundation Signals"""
import numpy as np
import sys
sys.path.insert(0, '..')

from foundation import (
    ARIMAModel, KalmanFilter, HMMRegimeDetector,
    StationarityTest, PCAAnalyzer, FoundationSignals
)


def generate_sample_data(n=500, trend='bull'):
    """Generate sample price data"""
    np.random.seed(42)
    
    if trend == 'bull':
        drift = 0.001
    elif trend == 'bear':
        drift = -0.001
    else:
        drift = 0
        
    returns = np.random.normal(drift, 0.02, n)
    prices = 100 * np.exp(np.cumsum(returns))
    return prices


def test_arima():
    print("=" * 50)
    print("Testing ARIMA Model")
    print("=" * 50)
    
    prices = generate_sample_data(200, 'bull')
    
    model = ARIMAModel()
    result = model.get_signal(prices, pred_days=5)
    
    print(f"Signal: {result['signal']:.3f}")
    print(f"Direction: {result['direction']}")
    print(f"Confidence: {result['confidence']:.3f}")
    print(f"Forecast: {result['forecast'][:3]}...")
    print()


def test_kalman():
    print("=" * 50)
    print("Testing Kalman Filter")
    print("=" * 50)
    
    prices = generate_sample_data(200, 'sideways')
    
    kf = KalmanFilter()
    result = kf.get_signal(prices)
    
    print(f"Signal: {result['signal']:.3f}")
    print(f"Z-score: {result['z_score']:.3f}")
    print(f"Filtered Price: {result['filtered_price']:.2f}")
    print(f"Actual Price: {result['actual_price']:.2f}")
    print(f"Deviation: {result['deviation']:.2f}")
    print()


def test_hmm():
    print("=" * 50)
    print("Testing HMM Regime Detector")
    print("=" * 50)
    
    prices = generate_sample_data(300, 'bull')
    
    hmm = HMMRegimeDetector()
    result = hmm.get_signal(prices)
    
    print(f"Signal: {result['signal']:.3f}")
    print(f"Regime: {result['regime_name']}")
    print(f"Confidence: {result['confidence']:.3f}")
    print(f"Transition: {result['transition']}")
    print(f"Probabilities: {result['probabilities']}")
    print()


def test_stationarity():
    print("=" * 50)
    print("Testing Stationarity")
    print("=" * 50)
    
    prices = generate_sample_data(200, 'bull')
    
    result = StationarityTest.full_test(prices)
    
    print(f"ADF p-value: {result['adf']['p_value']:.4f}")
    print(f"KPSS p-value: {result['kpss']['p_value']:.4f}")
    print(f"Conclusion: {result['conclusion']}")
    print(f"Recommended Strategy: {result['recommended_strategy']}")
    print()


def test_foundation_signals():
    print("=" * 50)
    print("Testing Foundation Signals (Composite)")
    print("=" * 50)
    
    prices = generate_sample_data(300, 'bull')
    
    fs = FoundationSignals()
    result = fs.generate(prices, pred_days=5)
    
    print(f"Composite Signal: {result['signal']:.3f}")
    print(f"Confidence: {result['confidence']:.3f}")
    print(f"Action: {result['action']}")
    print(f"Signal Quality: {result['signal_quality']}")
    print(f"Regime: {result['regime']}")
    print(f"Recommended Strategy: {result['recommended_strategy']}")
    print()
    print("Component Signals:")
    for name, comp in result['components'].items():
        print(f"  {name}: {comp['signal']:.3f}")


if __name__ == '__main__':
    test_arima()
    test_kalman()
    test_hmm()
    test_stationarity()
    test_foundation_signals()
    
    print("\n" + "=" * 50)
    print("Foundation Tests Completed!")
    print("=" * 50)
