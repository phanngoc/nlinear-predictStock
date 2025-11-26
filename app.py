import streamlit as st
import torch
import torch.nn as nn
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from torch.utils.data import Dataset, DataLoader
import plotly.graph_objects as go
from datetime import datetime, timedelta

# =============== Models ===============
class NLinear(nn.Module):
    def __init__(self, seq_len, pred_len):
        super().__init__()
        self.seq_len = seq_len
        self.pred_len = pred_len
        self.linear = nn.Linear(seq_len, pred_len)
    
    def forward(self, x):
        seq_last = x[:, -1:, :].detach()
        x = x - seq_last
        x = self.linear(x.permute(0, 2, 1)).permute(0, 2, 1)
        return x + seq_last

class MovingAvg(nn.Module):
    def __init__(self, kernel_size):
        super().__init__()
        self.kernel_size = kernel_size
        self.avg = nn.AvgPool1d(kernel_size=kernel_size, stride=1, padding=0)
    
    def forward(self, x):
        front = x[:, 0:1, :].repeat(1, (self.kernel_size - 1) // 2, 1)
        end = x[:, -1:, :].repeat(1, (self.kernel_size - 1) // 2, 1)
        x = torch.cat([front, x, end], dim=1)
        return self.avg(x.permute(0, 2, 1)).permute(0, 2, 1)

class DLinear(nn.Module):
    def __init__(self, seq_len, pred_len, kernel_size=25):
        super().__init__()
        self.moving_avg = MovingAvg(kernel_size)
        self.linear_seasonal = nn.Linear(seq_len, pred_len)
        self.linear_trend = nn.Linear(seq_len, pred_len)
    
    def forward(self, x):
        trend = self.moving_avg(x)
        seasonal = x - trend
        trend_out = self.linear_trend(trend.permute(0, 2, 1)).permute(0, 2, 1)
        seasonal_out = self.linear_seasonal(seasonal.permute(0, 2, 1)).permute(0, 2, 1)
        return trend_out + seasonal_out

class LSTMModel(nn.Module):
    def __init__(self, seq_len, pred_len, hidden_size=64, num_layers=2):
        super().__init__()
        self.pred_len = pred_len
        self.lstm = nn.LSTM(1, hidden_size, num_layers, batch_first=True, dropout=0.2)
        self.fc = nn.Linear(hidden_size, pred_len)
    
    def forward(self, x):
        # x: (batch, seq_len, 1)
        out, _ = self.lstm(x)
        out = self.fc(out[:, -1, :])  # (batch, pred_len)
        return out.unsqueeze(-1)  # (batch, pred_len, 1)

# =============== Dataset ===============
class StockDataset(Dataset):
    def __init__(self, data, seq_len, pred_len):
        self.data = data
        self.seq_len = seq_len
        self.pred_len = pred_len
    
    def __len__(self):
        return len(self.data) - self.seq_len - self.pred_len + 1
    
    def __getitem__(self, idx):
        x = self.data[idx:idx + self.seq_len]
        y = self.data[idx + self.seq_len:idx + self.seq_len + self.pred_len]
        return torch.FloatTensor(x), torch.FloatTensor(y)

# =============== Training ===============
def train_model(model, train_loader, epochs, lr, progress_bar):
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    
    for epoch in range(epochs):
        model.train()
        total_loss = 0
        for batch_x, batch_y in train_loader:
            optimizer.zero_grad()
            output = model(batch_x)
            loss = criterion(output, batch_y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        progress_bar.progress((epoch + 1) / epochs, f"Epoch {epoch+1}/{epochs} - Loss: {total_loss/len(train_loader):.6f}")
    return model

@st.cache_data
def load_stock_data(symbol, start_date, end_date):
    from vnstock import Vnstock
    stock = Vnstock().stock(symbol=symbol, source='VCI')
    df = stock.quote.history(start=start_date, end=end_date, interval='1D')
    return df

# =============== Streamlit App ===============
st.set_page_config(page_title="Stock Price Prediction", layout="wide")
st.title("📈 Dự đoán giá cổ phiếu với NLinear/DLinear")

# Sidebar
st.sidebar.header("⚙️ Cấu hình")
symbol = st.sidebar.text_input("Mã cổ phiếu", value="VNM")
model_type = st.sidebar.selectbox("Mô hình", ["NLinear", "DLinear", "LSTM"])
seq_len = st.sidebar.slider("Số ngày lookback", 30, 120, 60)
pred_len = st.sidebar.slider("Số ngày dự đoán", 7, 60, 40)  # ~2 tháng
epochs = st.sidebar.slider("Epochs", 50, 300, 100)
lr = st.sidebar.select_slider("Learning rate", options=[0.0001, 0.0005, 0.001, 0.005], value=0.001)

if st.sidebar.button("🚀 Bắt đầu dự đoán", type="primary"):
    try:
        # Load data
        with st.spinner("Đang tải dữ liệu..."):
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=365*3)).strftime('%Y-%m-%d')
            df = load_stock_data(symbol, start_date, end_date)
        
        st.success(f"✅ Đã tải {len(df)} ngày dữ liệu của {symbol}")
        
        # Prepare data
        prices = df['close'].values.reshape(-1, 1)
        scaler = MinMaxScaler()
        prices_scaled = scaler.fit_transform(prices)
        
        # Split data
        train_size = int(len(prices_scaled) * 0.8)
        train_data = prices_scaled[:train_size]
        
        dataset = StockDataset(train_data, seq_len, pred_len)
        loader = DataLoader(dataset, batch_size=32, shuffle=True)
        
        # Train model
        st.subheader("🔄 Training Model")
        progress_bar = st.progress(0)
        
        if model_type == "NLinear":
            model = NLinear(seq_len, pred_len)
        elif model_type == "DLinear":
            model = DLinear(seq_len, pred_len)
        else:
            model = LSTMModel(seq_len, pred_len)
        
        model = train_model(model, loader, epochs, lr, progress_bar)
        st.success("✅ Training hoàn tất!")
        
        # Predict future
        st.subheader("📊 Kết quả dự đoán")
        model.eval()
        with torch.no_grad():
            last_seq = torch.FloatTensor(prices_scaled[-seq_len:]).unsqueeze(0)
            prediction = model(last_seq).squeeze().numpy()
        
        # Inverse transform
        prediction = scaler.inverse_transform(prediction.reshape(-1, 1)).flatten()
        
        # Create future dates
        last_date = pd.to_datetime(df['time'].iloc[-1])
        future_dates = pd.date_range(start=last_date + timedelta(days=1), periods=pred_len, freq='B')
        
        # Plot
        fig = go.Figure()
        
        # Historical data (last 90 days)
        hist_df = df.tail(90)
        fig.add_trace(go.Scatter(
            x=hist_df['time'], y=hist_df['close'],
            mode='lines', name='Giá thực tế',
            line=dict(color='blue', width=2)
        ))
        
        # Prediction
        fig.add_trace(go.Scatter(
            x=future_dates, y=prediction,
            mode='lines+markers', name='Dự đoán',
            line=dict(color='red', width=2, dash='dash')
        ))
        
        fig.update_layout(
            title=f"Dự đoán giá {symbol} - {pred_len} ngày tới",
            xaxis_title="Ngày", yaxis_title="Giá (VND)",
            hovermode='x unified', height=500
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Summary
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Giá hiện tại", f"{df['close'].iloc[-1]:,.0f} VND")
        with col2:
            st.metric("Giá dự đoán (cuối kỳ)", f"{prediction[-1]:,.0f} VND", 
                     f"{((prediction[-1]/df['close'].iloc[-1])-1)*100:.2f}%")
        with col3:
            st.metric("Giá dự đoán trung bình", f"{prediction.mean():,.0f} VND")
        
        # Prediction table
        st.subheader("📋 Chi tiết dự đoán")
        pred_df = pd.DataFrame({
            'Ngày': future_dates.strftime('%Y-%m-%d'),
            'Giá dự đoán (VND)': [f"{p:,.0f}" for p in prediction]
        })
        st.dataframe(pred_df, use_container_width=True)
        
    except Exception as e:
        st.error(f"❌ Lỗi: {str(e)}")

# Info section
with st.expander("ℹ️ Về NLinear, DLinear và LSTM"):
    st.markdown("""
    **NLinear**: Chuẩn hóa dữ liệu bằng cách trừ giá trị cuối, dùng linear layer dự đoán, rồi cộng lại.
    
    **DLinear**: Phân tách chuỗi thành trend và seasonal, dùng 2 linear layers riêng biệt.
    
    **LSTM**: Mạng Long Short-Term Memory, phù hợp cho dữ liệu chuỗi thời gian, có khả năng học các pattern dài hạn.
    
    ⚠️ **Lưu ý**: Đây chỉ là công cụ tham khảo, không phải khuyến nghị đầu tư.
    """)
