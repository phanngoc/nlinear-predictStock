"""Streamlit UI for Advanced Trading System"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings('ignore')

from data_loader import VNStockLoader, VN30_SYMBOLS, BLUECHIP_SYMBOLS
from trading_engine import TradingEngine

st.set_page_config(
    page_title="Trading System - 5 Modules",
    page_icon="📈",
    layout="wide"
)

# Cache data loading
@st.cache_data(ttl=3600)
def load_data(symbols, days):
    loader = VNStockLoader()
    return loader.load_multiple(symbols, days)

@st.cache_data(ttl=3600)
def load_single(symbol, days):
    loader = VNStockLoader()
    return loader.load_single(symbol, days)


def plot_price_chart(prices_df, target, signals=None):
    """Plot price chart with signals"""
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        row_heights=[0.7, 0.3],
                        vertical_spacing=0.05)
    
    # Price
    fig.add_trace(
        go.Candlestick(x=prices_df.index,
                       open=prices_df['open'],
                       high=prices_df['high'],
                       low=prices_df['low'],
                       close=prices_df['close'],
                       name=target),
        row=1, col=1
    )
    
    # Volume
    colors = ['red' if c < o else 'green' 
              for c, o in zip(prices_df['close'], prices_df['open'])]
    fig.add_trace(
        go.Bar(x=prices_df.index, y=prices_df['volume'], 
               marker_color=colors, name='Volume', opacity=0.5),
        row=2, col=1
    )
    
    fig.update_layout(
        height=500,
        xaxis_rangeslider_visible=False,
        showlegend=False
    )
    
    return fig


def plot_signal_gauge(signal, confidence):
    """Plot signal gauge"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=signal,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': f"Signal (Conf: {confidence:.0%})"},
        delta={'reference': 0},
        gauge={
            'axis': {'range': [-1, 1]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [-1, -0.3], 'color': "red"},
                {'range': [-0.3, 0.3], 'color': "gray"},
                {'range': [0.3, 1], 'color': "green"}
            ],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': signal
            }
        }
    ))
    fig.update_layout(height=250)
    return fig


def plot_phase_signals(phase_signals):
    """Plot phase signals as horizontal bar"""
    phases = list(phase_signals.keys())
    signals = [phase_signals[p]['signal'] for p in phases]
    
    colors = ['green' if s > 0 else 'red' if s < 0 else 'gray' for s in signals]
    
    fig = go.Figure(go.Bar(
        x=signals,
        y=phases,
        orientation='h',
        marker_color=colors,
        text=[f"{s:+.2f}" for s in signals],
        textposition='outside'
    ))
    
    fig.update_layout(
        height=200,
        xaxis=dict(range=[-1, 1], title='Signal'),
        yaxis=dict(title=''),
        showlegend=False
    )
    
    return fig


def show_signal_explanation():
    """Show signal calculation explanation"""
    with st.expander("📖 Cách tính Signal - Hướng dẫn đọc kết quả", expanded=False):
        st.markdown("""
        ### 🎯 Signal là gì?
        
        **Signal** là chỉ số tổng hợp từ -1 đến +1, cho biết xu hướng mua/bán:
        
        | Signal | Ý nghĩa | Hành động |
        |--------|---------|-----------|
        | **+0.6 → +1.0** | 🟢🟢 Rất tích cực | **STRONG BUY** - Mua mạnh |
        | **+0.3 → +0.6** | 🟢 Tích cực | **BUY** - Mua |
        | **-0.3 → +0.3** | ⚪ Trung lập | **HOLD** - Giữ nguyên |
        | **-0.6 → -0.3** | 🔴 Tiêu cực | **SELL** - Bán |
        | **-1.0 → -0.6** | 🔴🔴 Rất tiêu cực | **STRONG SELL** - Bán mạnh |
        
        ---
        
        ### 📊 Công thức tính Signal tổng hợp
        
        ```
        Final Signal = 0.25 × Foundation + 0.20 × Network + 0.20 × Multivariate + 0.35 × Pattern
        ```
        
        | Module | Trọng số | Phân tích |
        |-------|----------|-----------|
        | **Foundation** | 25% | ARIMA (dự báo), Kalman (lọc nhiễu), HMM (xu hướng) |
        | **Network** | 20% | Mối quan hệ giữa các cổ phiếu, cổ phiếu dẫn dắt |
        | **Multivariate** | 20% | VAR, Granger causality, rủi ro đuôi (tail risk) |
        | **Pattern** | 35% | Regime (Bull/Bear), Factor model, Anomaly |
        
        ---
        
        ### 🔍 Chi tiết từng Module
        
        **Foundation (Nền tảng):**
        - **ARIMA**: Dự báo giá ngắn hạn (1-5 ngày). Signal > 0 = giá sẽ tăng
        - **Kalman Filter**: So sánh giá thực vs giá "thật". Z-score > 2 = đang overvalued
        - **HMM Regime**: Xác định thị trường Bull/Bear/Sideways
        
        **Network (Mạng lưới):**
        - **Density Change**: Tăng = các CP tương quan cao hơn = Risk-off
        - **Lead-Lag**: Tìm CP dẫn dắt để dự đoán CP theo sau
        
        **Multivariate (Đa biến):**
        - **VAR**: Dự báo dựa trên nhiều CP cùng lúc
        - **Granger**: Tìm CP nào "gây ra" biến động CP khác
        - **Copula**: Đo rủi ro crash (tail dependency)
        
        **Pattern (Mẫu hình):**
        - **4-State Regime**: Bull/Bear × High/Low Volatility
        - **Factor Model**: Tìm alpha từ residual (CP undervalued/overvalued)
        - **Anomaly**: Phát hiện bất thường thống kê
        
        ---
        
        ### 📈 Confidence là gì?
        
        **Confidence** (0% - 100%) cho biết độ tin cậy của signal:
        - **> 70%**: Tin cậy cao, có thể hành động
        - **50-70%**: Trung bình, cần xem xét thêm
        - **< 50%**: Thấp, nên chờ đợi
        
        ---
        
        ### 🎭 Market Regime
        
        | Regime | Đặc điểm | Chiến lược |
        |--------|----------|------------|
        | 🟢 **BULL_LOW_VOL** | Tăng + ít biến động | Full Long |
        | 🟡 **BULL_HIGH_VOL** | Tăng + nhiều biến động | Giảm vị thế |
        | 🟠 **BEAR_LOW_VOL** | Giảm + ít biến động | Cash/Short |
        | 🔴 **BEAR_HIGH_VOL** | Giảm + nhiều biến động | Hedge |
        | ⚪ **SIDEWAYS** | Đi ngang | Mean reversion |
        """)


def main():
    st.title("📈 Advanced Trading System")
    st.markdown("*5-Module Analysis for Vietnam Stock Market*")
    
    # Show explanation at top
    show_signal_explanation()
    
    # Sidebar
    st.sidebar.header("⚙️ Settings")
    
    # Stock selection
    stock_option = st.sidebar.radio(
        "Stock Selection",
        ["Single Stock", "Market Scan"]
    )
    
    days = st.sidebar.slider("Data Period (days)", 180, 730, 365)
    
    if stock_option == "Single Stock":
        # Single stock analysis
        col1, col2 = st.sidebar.columns(2)
        with col1:
            target = st.text_input("Stock Symbol", "VNM").upper()
        with col2:
            preset = st.selectbox("Or Select", ["Custom"] + BLUECHIP_SYMBOLS)
            if preset != "Custom":
                target = preset
        
        peers = st.sidebar.multiselect(
            "Peer Stocks (for network analysis)",
            VN30_SYMBOLS,
            default=['FPT', 'VIC', 'VHM', 'HPG', 'MWG']
        )
        
        if target not in peers:
            peers = [target] + peers[:5]
        
        if st.sidebar.button("🔍 Analyze", type="primary"):
            with st.spinner(f"Loading data for {target}..."):
                # Load data
                prices_df = load_data(peers, days)
                single_df = load_single(target, days)
                
                if prices_df is None or len(prices_df) < 60:
                    st.error("Insufficient data. Try different stocks.")
                    return
                
                # Generate signal
                engine = TradingEngine()
                result = engine.generate_signal(prices_df, target)
                
                # Debug: check Multivariate
                p3_debug = result['details'].get('multivariate', {})
                if 'error' in p3_debug:
                    st.warning(f"Multivariate có lỗi: {p3_debug['error']}")
            
            # Display results
            st.header(f"📊 {target} Analysis")
            
            # Price info
            current_price = prices_df[target].iloc[-1]
            prev_price = prices_df[target].iloc[-2]
            daily_change = (current_price / prev_price - 1) * 100
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Current Price", f"{current_price:,.0f}", f"{daily_change:+.2f}%")
            col2.metric("Signal", f"{result['signal']:+.3f}")
            col3.metric("Confidence", f"{result['confidence']:.1%}")
            col4.metric("Action", result['action'])
            
            # Charts
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.subheader("Price Chart")
                if single_df is not None:
                    fig = plot_price_chart(single_df, target)
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.subheader("Signal Gauge")
                fig = plot_signal_gauge(result['signal'], result['confidence'])
                st.plotly_chart(fig, use_container_width=True)
            
            # Module signals with explanation
            st.subheader("📊 Module Signals")
            
            st.markdown("""
            <div style="background-color: #e8f4ea; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
            <b>📖 Cách đọc:</b> Mỗi module đóng góp vào signal cuối cùng với trọng số <b>thích ứng theo regime</b>.
            <span style="color:green">Xanh</span> = bullish, <span style="color:red">Đỏ</span> = bearish.
            <br><i>🇻🇳 Tối ưu cho thị trường Việt Nam: Lead-lag và Regime detection được ưu tiên.</i>
            </div>
            """, unsafe_allow_html=True)
            
            fig = plot_phase_signals(result['phase_signals'])
            st.plotly_chart(fig, use_container_width=True)
            
            # Module contribution breakdown with adaptive weights
            st.markdown("**Đóng góp của từng Module vào Signal cuối (Adaptive Weights):**")
            
            # Get actual weights used from result
            weights = result.get('weights_used', {'foundation': 0.25, 'network': 0.25, 'multivariate': 0.15, 'pattern': 0.35})
            
            contrib_data = []
            for phase in ['foundation', 'network', 'multivariate', 'pattern']:
                w = weights.get(phase, 0)
                sig = result['phase_signals'].get(phase, {}).get('signal', 0)
                contribution = sig * w
                contrib_data.append({
                    'Phase': phase.title(),
                    'Signal': f"{sig:+.3f}",
                    'Weight': f"{w:.0%}",
                    'Contribution': f"{contribution:+.3f}"
                })
            
            contrib_df = pd.DataFrame(contrib_data)
            st.dataframe(contrib_df, use_container_width=True, hide_index=True)
            
            # Details
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("💰 Position Sizing")
                pos = result['position']
                
                st.markdown("""
                <div style="background-color: #fff3cd; padding: 8px; border-radius: 5px; font-size: 12px; margin-bottom: 10px;">
                💡 <b>Kelly Criterion</b>: Tính toán % vốn tối ưu dựa trên xác suất thắng và tỷ lệ risk/reward.
                </div>
                """, unsafe_allow_html=True)
                
                st.write(f"**Direction:** {pos['direction']}")
                st.write(f"**Position Size:** {pos['position_pct']:.1%}")
                st.write(f"**Dollar Amount:** ${pos['dollar_amount']:,.0f}")
            
            with col2:
                st.subheader("⚠️ Risk Management")
                risk = result['risk']
                
                st.markdown("""
                <div style="background-color: #f8d7da; padding: 8px; border-radius: 5px; font-size: 12px; margin-bottom: 10px;">
                💡 <b>ATR-based</b>: Stop loss = 2× volatility, Take profit = 4× volatility (Risk/Reward 1:2)
                </div>
                """, unsafe_allow_html=True)
                
                st.write(f"**Stop Loss:** {risk['stop_loss']:,.0f} ({(risk['stop_loss']/current_price-1)*100:+.1f}%)")
                st.write(f"**Take Profit:** {risk['take_profit']:,.0f} ({(risk['take_profit']/current_price-1)*100:+.1f}%)")
                st.write(f"**Risk/Reward:** {risk['risk_reward']:.1f}")
            
            # Regime info with explanation
            st.subheader("🎯 Market Regime")
            regime = result['regime']
            
            regime_info = {
                'BULL_LOW_VOL': ('🟢', 'Thị trường tăng, biến động thấp', 'Tốt nhất để LONG'),
                'BULL_HIGH_VOL': ('🟡', 'Thị trường tăng, biến động cao', 'Cẩn thận, giảm vị thế'),
                'BEAR_LOW_VOL': ('🟠', 'Thị trường giảm, biến động thấp', 'Nên đứng ngoài hoặc SHORT'),
                'BEAR_HIGH_VOL': ('🔴', 'Thị trường giảm, biến động cao', 'Nguy hiểm, cần HEDGE'),
                'SIDEWAYS': ('⚪', 'Thị trường đi ngang', 'Mean reversion strategy'),
                'UNKNOWN': ('❓', 'Không xác định', 'Chờ tín hiệu rõ hơn')
            }
            
            emoji, desc, action = regime_info.get(regime, ('❓', 'N/A', 'N/A'))
            
            col1, col2, col3 = st.columns(3)
            col1.write(f"**Regime:** {emoji} {regime}")
            col2.write(f"**Mô tả:** {desc}")
            col3.write(f"**Khuyến nghị:** {action}")
            
            # Phase details expander
            with st.expander("📋 Chi tiết phân tích từng Phase"):
                details = result['details']
                
                st.markdown("### Foundation (Nền tảng)")
                st.markdown("*Phân tích chuỗi thời gian: dự báo xu hướng ngắn hạn*")
                p1 = details.get('foundation', {})
                if 'components' in p1:
                    comp = p1['components']
                    
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        arima_sig = comp.get('arima', {}).get('signal', 0)
                        st.metric("ARIMA", f"{arima_sig:+.3f}", 
                                 help="Dự báo giá ngắn hạn. >0 = giá sẽ tăng")
                    with c2:
                        kalman_sig = comp.get('kalman', {}).get('signal', 0)
                        st.metric("Kalman", f"{kalman_sig:+.3f}",
                                 help="So sánh giá thực vs giá lọc. <0 = đang overvalued")
                    with c3:
                        hmm_sig = comp.get('hmm', {}).get('signal', 0)
                        hmm_regime = comp.get('hmm', {}).get('regime', 'N/A')
                        st.metric("HMM", f"{hmm_sig:+.3f} ({hmm_regime})",
                                 help="Xác định xu hướng Bull/Bear/Sideways")
                
                st.markdown("### Network (Mạng lưới)")
                st.markdown("*Phân tích mối quan hệ giữa các cổ phiếu*")
                p2 = details.get('network', {})
                stats = p2.get('network_stats', {})
                leaders = p2.get('leaders', [])[:3]
                
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"**Network Density:** {stats.get('density', 0):.3f}")
                    st.caption("Density cao = các CP tương quan mạnh = rủi ro hệ thống")
                with c2:
                    st.write(f"**Market Leaders:** {[l[0] for l in leaders]}")
                    st.caption("CP có ảnh hưởng lớn nhất trong network")
                
                st.markdown("### Multivariate (Đa biến)")
                st.markdown("*Phân tích quan hệ nhân quả và rủi ro đuôi*")
                p3 = details.get('multivariate', {})
                
                # Check for error
                if 'error' in p3:
                    st.error(f"Multivariate Error: {p3['error']}")
                else:
                    c1, c2 = st.columns(2)
                    with c1:
                        risk = p3.get('risk_level', 'N/A')
                        risk_emoji = '🟢' if 'LOW' in str(risk) else '🔴' if 'HIGH' in str(risk) else '🟡'
                        st.write(f"**Tail Risk:** {risk_emoji} {risk}")
                        st.caption("Rủi ro crash dựa trên copula analysis")
                        
                        # Show copula details
                        copula = p3.get('components', {}).get('copula', {})
                        if copula:
                            lower = copula.get('avg_lower_tail', 0)
                            upper = copula.get('avg_upper_tail', 0)
                            st.caption(f"Lower tail: {lower:.2%}, Upper tail: {upper:.2%}")
                    
                    with c2:
                        indicators = p3.get('leading_indicators', [])
                        if indicators:
                            st.write(f"**Leading Indicators:** {[f'{l[0]} (p={l[1]:.3f})' for l in indicators[:3]]}")
                        else:
                            # Try getting from granger component
                            granger = p3.get('components', {}).get('granger', {})
                            leaders = granger.get('leaders', [])
                            if leaders:
                                st.write(f"**Leading Indicators:** {[f'{l[0]}' for l in leaders[:3]]}")
                            else:
                                st.write("**Leading Indicators:** Không tìm thấy")
                        st.caption("CP dự báo được biến động của CP này")
                
                st.markdown("### Pattern (Mẫu hình)")
                st.markdown("*Phát hiện regime và anomaly*")
                p4 = details.get('pattern', {})
                
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"**4-State Regime:** {p4.get('regime', 'N/A')}")
                    st.caption("Bull/Bear × High/Low Volatility")
                with c2:
                    st.write(f"**Recommended Action:** {p4.get('regime_action', 'N/A')}")
                    st.caption("Hành động phù hợp với regime hiện tại")
    
    else:
        # Market scan
        st.sidebar.subheader("Scan Settings")
        
        scan_preset = st.sidebar.selectbox(
            "Stock Universe",
            ["Bluechip (8)", "VN30 (20)", "Custom"]
        )
        
        if scan_preset == "Bluechip (8)":
            symbols = BLUECHIP_SYMBOLS
        elif scan_preset == "VN30 (20)":
            symbols = VN30_SYMBOLS
        else:
            symbols = st.sidebar.multiselect("Select Stocks", VN30_SYMBOLS, default=BLUECHIP_SYMBOLS)
        
        if st.sidebar.button("🔍 Scan Market", type="primary"):
            with st.spinner(f"Scanning {len(symbols)} stocks..."):
                prices_df = load_data(symbols, days)
                
                if prices_df is None or len(prices_df) < 60:
                    st.error("Insufficient data")
                    return
                
                engine = TradingEngine()
                scan = engine.scan_market(prices_df, top_n=10)
            
            st.header("📊 Market Scan Results")
            st.write(f"Scanned {len(prices_df.columns)} stocks, {len(prices_df)} days of data")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🟢 Buy Opportunities")
                if scan['buy_opportunities']:
                    for opp in scan['buy_opportunities']:
                        st.success(f"**{opp['asset']}** | Signal: {opp['signal']:+.2f} | {opp['regime']}")
                else:
                    st.info("No strong buy signals")
            
            with col2:
                st.subheader("🔴 Sell Opportunities")
                if scan['sell_opportunities']:
                    for opp in scan['sell_opportunities']:
                        st.error(f"**{opp['asset']}** | Signal: {opp['signal']:+.2f} | {opp['regime']}")
                else:
                    st.info("No strong sell signals")
            
            # Full rankings
            st.subheader("📋 Full Rankings")
            
            rankings_df = pd.DataFrame(scan['all_rankings'])
            rankings_df['signal'] = rankings_df['signal'].apply(lambda x: f"{x:+.3f}")
            rankings_df['score'] = rankings_df['score'].apply(lambda x: f"{x:.3f}")
            rankings_df.index = range(1, len(rankings_df) + 1)
            
            st.dataframe(rankings_df, use_container_width=True)
            
            # Heatmap with explanation
            st.subheader("📊 Signal Heatmap")
            
            st.markdown("""
            <div style="background-color: #f0f2f6; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
            <b>📖 Cách đọc:</b> Cột <span style="color:green">xanh</span> = tín hiệu mua (signal > 0), 
            cột <span style="color:red">đỏ</span> = tín hiệu bán (signal < 0). 
            Cột càng cao = tín hiệu càng mạnh.
            </div>
            """, unsafe_allow_html=True)
            
            signals = [opp['signal'] for opp in scan['all_rankings']]
            assets = [opp['asset'] for opp in scan['all_rankings']]
            regimes = [opp['regime'] for opp in scan['all_rankings']]
            
            # Color based on signal strength
            colors = []
            for s in signals:
                if s > 0.3:
                    colors.append('darkgreen')
                elif s > 0:
                    colors.append('lightgreen')
                elif s > -0.3:
                    colors.append('salmon')
                else:
                    colors.append('darkred')
            
            fig = go.Figure(go.Bar(
                x=assets,
                y=signals,
                marker_color=colors,
                text=[f"{s:+.2f}" for s in signals],
                textposition='outside',
                hovertemplate="<b>%{x}</b><br>Signal: %{y:.3f}<br><extra></extra>"
            ))
            
            # Add threshold lines
            fig.add_hline(y=0.3, line_dash="dash", line_color="green", 
                         annotation_text="Buy threshold", annotation_position="right")
            fig.add_hline(y=-0.3, line_dash="dash", line_color="red",
                         annotation_text="Sell threshold", annotation_position="right")
            fig.add_hline(y=0, line_color="gray", line_width=1)
            
            fig.update_layout(
                height=350,
                yaxis=dict(range=[-1, 1], title="Signal Strength"),
                xaxis=dict(title="Stock", tickangle=-45),
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Summary stats
            col1, col2, col3 = st.columns(3)
            buy_count = sum(1 for s in signals if s > 0.3)
            sell_count = sum(1 for s in signals if s < -0.3)
            hold_count = len(signals) - buy_count - sell_count
            
            col1.metric("🟢 Buy Signals", buy_count, help="Signal > 0.3")
            col2.metric("⚪ Hold", hold_count, help="-0.3 < Signal < 0.3")
            col3.metric("🔴 Sell Signals", sell_count, help="Signal < -0.3")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    ⚠️ **Disclaimer**: Đây chỉ là công cụ phân tích tham khảo. 
    Kết quả KHÔNG phải khuyến nghị đầu tư. Hãy tự nghiên cứu và tham khảo chuyên gia trước khi đầu tư.
    """)


if __name__ == "__main__":
    main()
