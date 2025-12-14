# 🎯 Advanced Trading System - 5 Phase Integration

> Hệ thống giao dịch tích hợp 5 phases phân tích để đạt mục tiêu >30% annual return

## 🚀 Quick Start

### Run Streamlit UI
```bash
cd trading_system
./run_app.sh
# Or: streamlit run app_trading.py
```
Open http://localhost:8502

### Command Line Analysis
```bash
# Quick analysis
python analyze.py VNM

# Market scan
python analyze.py --scan

# Deep analysis
python deep_analyze.py FPT
```

## 📊 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        TRADING ENGINE                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Module 1         Module 2         Module 3         Module 4         Module 5│
│  Foundation       Network          Multivariate     Pattern          Crypto │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌────────┐│
│  │ ARIMA    │    │ Corr Net │    │ VAR/VECM │    │ Regime   │    │On-chain││
│  │ Kalman   │    │ Centrality│   │ Granger  │    │ Factors  │    │DEX Flow││
│  │ HMM      │    │ Lead-Lag │    │ Copula   │    │ Anomaly  │    │Social  ││
│  │ PCA      │    │ Clusters │    │ G-Lasso  │    │ Detection│    │Whale   ││
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘    └────────┘│
│       │               │               │               │               │     │
│       └───────────────┴───────────────┴───────────────┴───────────────┘     │
│                                   │                                          │
│                    ┌──────────────▼──────────────┐                          │
│                    │     SIGNAL AGGREGATOR       │                          │
│                    │  (Weighted + Confirmation)  │                          │
│                    └──────────────┬──────────────┘                          │
│                                   │                                          │
│                    ┌──────────────▼──────────────┐                          │
│                    │      RISK MANAGER           │                          │
│                    │  (Kelly + Stop Loss)        │                          │
│                    └──────────────┬──────────────┘                          │
│                                   │                                          │
│                    ┌──────────────▼──────────────┐                          │
│                    │    TRADING DECISION         │                          │
│                    │  BUY / SELL / HOLD          │                          │
│                    └─────────────────────────────┘                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
trading_system/
├── __init__.py
├── trading_engine.py          # Main engine integrating all phases
├── demo.py                    # Demo script
├── README.md
│
├── foundation/                # Time Series & Statistics
│   ├── arima_model.py        # ARIMA forecasting
│   ├── kalman_filter.py      # Noise filtering
│   ├── hmm_regime.py         # Regime detection
│   ├── statistics.py         # Stationarity, PCA
│   └── foundation_signals.py # Aggregate Foundation
│
├── network/                   # Network Analysis
│   ├── correlation_network.py # Build correlation graphs
│   ├── network_metrics.py    # Centrality, clustering
│   ├── lead_lag_detector.py  # Lead-lag relationships
│   └── network_signals.py    # Aggregate Network
│
├── multivariate/              # Multivariate Modeling
│   ├── var_model.py          # VAR/VECM
│   ├── granger_causality.py  # Causality analysis
│   ├── copula_model.py       # Tail dependencies
│   └── multivariate_signals.py
│
├── pattern/                   # Pattern Hunting
│   ├── regime_detector.py    # 4-state regime
│   ├── factor_model.py       # Hidden factors
│   ├── anomaly_detector.py   # Statistical anomalies
│   └── pattern_signals.py
│
├── crypto/                    # Crypto-specific
│   └── crypto_signals.py     # On-chain, DEX, social
│
└── core/                      # Core modules
    ├── signal_aggregator.py  # Combine all signals
    └── risk_manager.py       # Position sizing, stops
```

## 🚀 Quick Start

```python
from trading_system.trading_engine import TradingEngine
import pandas as pd

# Load price data
prices_df = pd.read_csv('prices.csv', index_col=0, parse_dates=True)

# Create engine
engine = TradingEngine()

# Generate signal for single asset
result = engine.generate_signal(prices_df, 'VNM')
print(f"Signal: {result['signal']:.3f}")
print(f"Action: {result['action']}")
print(f"Regime: {result['regime']}")

# Scan entire market
scan = engine.scan_market(prices_df, top_n=5)
print("Buy opportunities:", scan['buy_opportunities'])
```

## 📈 Module Details

### Foundation (25% weight)
| Component | Purpose | Signal |
|-----------|---------|--------|
| ARIMA | Short-term forecast | Direction |
| Kalman | Noise filtering | Deviation |
| HMM | Regime detection | Bull/Bear/Sideways |
| PCA | Factor extraction | Hidden drivers |

### Network (20% weight)
| Component | Purpose | Signal |
|-----------|---------|--------|
| Correlation Network | Market structure | Density change |
| Centrality | Find leaders | Leader stocks |
| Lead-Lag | Predictive pairs | Trade laggers |
| Clustering | Sector groups | Diversification |

### Multivariate (20% weight)
| Component | Purpose | Signal |
|-----------|---------|--------|
| VAR | Cross-asset forecast | Multi-asset prediction |
| Granger | Causality | Leading indicators |
| Copula | Tail dependency | Crash risk |
| G-Lasso | Sparse correlation | True relationships |

### Pattern (25% weight)
| Component | Purpose | Signal |
|-----------|---------|--------|
| 4-State Regime | Bull/Bear × High/Low Vol | Position sizing |
| Factor Model | Hidden factors | Alpha from residuals |
| Anomaly | Statistical arbitrage | Mean reversion |

### Crypto (10% weight)
| Component | Purpose | Signal |
|-----------|---------|--------|
| Exchange Flow | Inflow/Outflow | Accumulation/Distribution |
| Whale Activity | Large transactions | Smart money |
| Social Sentiment | Twitter/Telegram | Contrarian |

## 🎯 Target: >30% Annual Return

### Mathematical Framework
```
Expected Return = Win_Rate × Avg_Win - Loss_Rate × Avg_Loss

Target parameters:
- Win Rate: 55-60% (multi-signal confirmation)
- Risk/Reward: 1:2 minimum
- Trade Frequency: 2-4 trades/week
- Position Size: Kelly-optimized (10-25%)

Conservative estimate:
Monthly = 0.57 × 4% - 0.43 × 2% = 1.42%
Annual = (1.0142)^12 - 1 ≈ 18%

With regime optimization: 25-35%
```

### Risk Controls
| Control | Value |
|---------|-------|
| Max Position | 25% |
| Max Drawdown | 15% |
| Stop Loss | 2× ATR |
| Take Profit | 4× ATR |

## 📊 Signal Interpretation

| Signal Range | Action | Position |
|--------------|--------|----------|
| > 0.6 | Strong BUY | Full position |
| 0.3 - 0.6 | BUY | Half position |
| -0.3 - 0.3 | HOLD | No change |
| -0.6 - -0.3 | SELL | Reduce |
| < -0.6 | Strong SELL | Exit/Short |

## ⚠️ Disclaimer

> Đây là công cụ nghiên cứu và học tập. Kết quả dự đoán KHÔNG phải khuyến nghị đầu tư. Luôn tham khảo chuyên gia tài chính trước khi đầu tư.

## 📦 Dependencies

```
numpy
pandas
scipy
statsmodels
hmmlearn
networkx
scikit-learn
```

## 🔧 Installation

```bash
pip install -r requirements.txt
cd trading_system
python demo.py
```
