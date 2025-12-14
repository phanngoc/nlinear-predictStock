import streamlit as st
import torch
import torch.nn as nn
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from torch.utils.data import Dataset, DataLoader
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sqlite3
import json

DB_PATH = "predictions.db"

# =============== Database ===============
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''CREATE TABLE IF NOT EXISTS predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT, model_type TEXT, run_date TEXT,
        pred_start_date TEXT, pred_end_date TEXT,
        predictions TEXT, seq_len INTEGER, pred_len INTEGER, epochs INTEGER
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS actual_prices (
        symbol TEXT, date TEXT, close_price REAL,
        PRIMARY KEY (symbol, date)
    )''')
    conn.commit()
    conn.close()

def save_prediction(symbol, model_type, run_date, pred_start, pred_end, predictions, seq_len, pred_len, epochs):
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''INSERT INTO predictions (symbol, model_type, run_date, pred_start_date, pred_end_date, predictions, seq_len, pred_len, epochs)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (symbol, model_type, run_date, pred_start, pred_end, json.dumps(predictions), seq_len, pred_len, epochs))
    conn.commit()
    conn.close()

def save_actual_prices(symbol, df):
    conn = sqlite3.connect(DB_PATH)
    for _, row in df.iterrows():
        conn.execute('INSERT OR REPLACE INTO actual_prices (symbol, date, close_price) VALUES (?, ?, ?)',
            (symbol, str(row['time'])[:10], float(row['close'])))
    conn.commit()
    conn.close()

def get_predictions(symbol=None):
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT * FROM predictions"
    if symbol:
        query += f" WHERE symbol = '{symbol}'"
    query += " ORDER BY run_date DESC"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_actual_prices(symbol, start_date, end_date):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(f"SELECT * FROM actual_prices WHERE symbol = ? AND date BETWEEN ? AND ?",
        conn, params=(symbol, start_date, end_date))
    conn.close()
    return df

# =============== Models ===============
class NLinear(nn.Module):
    def __init__(self, seq_len, pred_len):
        super().__init__()
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
        self.lstm = nn.LSTM(1, hidden_size, num_layers, batch_first=True, dropout=0.2)
        self.fc = nn.Linear(hidden_size, pred_len)
    
    def forward(self, x):
        out, _ = self.lstm(x)
        out = self.fc(out[:, -1, :])
        return out.unsqueeze(-1)

# =============== Dataset & Training ===============
class StockDataset(Dataset):
    def __init__(self, data, seq_len, pred_len):
        self.data, self.seq_len, self.pred_len = data, seq_len, pred_len
    
    def __len__(self):
        return len(self.data) - self.seq_len - self.pred_len + 1
    
    def __getitem__(self, idx):
        x = self.data[idx:idx + self.seq_len]
        y = self.data[idx + self.seq_len:idx + self.seq_len + self.pred_len]
        return torch.FloatTensor(x), torch.FloatTensor(y)

def train_model(model, train_loader, epochs, lr, progress_callback=None):
    criterion, optimizer = nn.MSELoss(), torch.optim.Adam(model.parameters(), lr=lr)
    for epoch in range(epochs):
        model.train()
        total_loss = sum(
            (optimizer.zero_grad(), loss := criterion(model(bx), by), loss.backward(), optimizer.step(), loss.item())[-1]
            for bx, by in train_loader
        )
        if progress_callback:
            progress_callback(epoch + 1, epochs, total_loss / len(train_loader))
    return model

@st.cache_data
def load_stock_data(symbol, start_date, end_date):
    from vnstock import Vnstock
    stock = Vnstock().stock(symbol=symbol, source='VCI')
    return stock.quote.history(start=start_date, end=end_date, interval='1D')

def create_model(model_type, seq_len, pred_len):
    models = {"NLinear": NLinear, "DLinear": DLinear, "LSTM": LSTMModel}
    return models[model_type](seq_len, pred_len)

# =============== Accuracy Calculation ===============
def calculate_accuracy(predictions, actuals):
    """Calculate MAPE and direction accuracy"""
    if len(actuals) == 0:
        return None, None
    pred_arr = np.array(predictions[:len(actuals)])
    actual_arr = np.array(actuals)
    mape = np.mean(np.abs((actual_arr - pred_arr) / actual_arr)) * 100
    direction_acc = np.mean((np.diff(pred_arr) > 0) == (np.diff(actual_arr) > 0)) * 100 if len(actual_arr) > 1 else None
    return mape, direction_acc

# =============== Streamlit App ===============
st.set_page_config(page_title="Stock Price Prediction", layout="wide")
init_db()

page = st.sidebar.radio("📌 Trang", ["Dự đoán", "So sánh kết quả"])

if page == "Dự đoán":
    st.title("📈 Dự đoán giá cổ phiếu")
    
    st.sidebar.header("⚙️ Cấu hình")
    symbol = st.sidebar.text_input("Mã cổ phiếu", value="VNM")
    run_all = st.sidebar.checkbox("🔄 Chạy cả 3 mô hình", value=True)
    if not run_all:
        model_type = st.sidebar.selectbox("Mô hình", ["NLinear", "DLinear", "LSTM"])
    seq_len = st.sidebar.slider("Số ngày lookback", 30, 120, 60)
    pred_len = st.sidebar.slider("Số ngày dự đoán", 7, 60, 30)
    epochs = st.sidebar.slider("Epochs", 50, 300, 100)
    lr = st.sidebar.select_slider("Learning rate", options=[0.0001, 0.0005, 0.001, 0.005], value=0.001)

    if st.sidebar.button("🚀 Bắt đầu dự đoán", type="primary"):
        try:
            with st.spinner("Đang tải dữ liệu..."):
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=365*3)).strftime('%Y-%m-%d')
                df = load_stock_data(symbol, start_date, end_date)
                save_actual_prices(symbol, df)
            
            st.success(f"✅ Đã tải {len(df)} ngày dữ liệu của {symbol}")
            
            prices = df['close'].values.reshape(-1, 1)
            scaler = MinMaxScaler()
            prices_scaled = scaler.fit_transform(prices)
            train_data = prices_scaled[:int(len(prices_scaled) * 0.8)]
            dataset = StockDataset(train_data, seq_len, pred_len)
            loader = DataLoader(dataset, batch_size=32, shuffle=True)
            
            models_to_run = ["NLinear", "DLinear", "LSTM"] if run_all else [model_type]
            results = {}
            
            last_date = pd.to_datetime(df['time'].iloc[-1])
            future_dates = pd.date_range(start=last_date + timedelta(days=1), periods=pred_len, freq='B')
            run_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            for mt in models_to_run:
                st.subheader(f"🔄 Training {mt}")
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                def update_progress(epoch, total, loss):
                    progress_bar.progress(epoch / total)
                    status_text.text(f"Epoch {epoch}/{total} - Loss: {loss:.6f}")
                
                model = create_model(mt, seq_len, pred_len)
                model = train_model(model, loader, epochs, lr, update_progress)
                
                model.eval()
                with torch.no_grad():
                    last_seq = torch.FloatTensor(prices_scaled[-seq_len:]).unsqueeze(0)
                    prediction = model(last_seq).squeeze().numpy()
                prediction = scaler.inverse_transform(prediction.reshape(-1, 1)).flatten()
                results[mt] = prediction.tolist()
                
                save_prediction(symbol, mt, run_date, str(future_dates[0].date()), 
                    str(future_dates[-1].date()), prediction.tolist(), seq_len, pred_len, epochs)
                st.success(f"✅ {mt} hoàn tất!")
            
            # Plot all results
            st.subheader("📊 Kết quả dự đoán")
            fig = go.Figure()
            
            hist_df = df.tail(60)
            fig.add_trace(go.Scatter(x=hist_df['time'], y=hist_df['close'],
                mode='lines', name='Giá thực tế', line=dict(color='blue', width=2)))
            
            colors = {'NLinear': 'red', 'DLinear': 'green', 'LSTM': 'orange'}
            for mt, pred in results.items():
                fig.add_trace(go.Scatter(x=future_dates, y=pred,
                    mode='lines+markers', name=f'{mt}', line=dict(color=colors[mt], width=2, dash='dash')))
            
            fig.update_layout(title=f"Dự đoán giá {symbol}", xaxis_title="Ngày", 
                yaxis_title="Giá (VND)", hovermode='x unified', height=500)
            st.plotly_chart(fig, use_container_width=True)
            
            # Summary table
            st.subheader("📋 So sánh dự đoán")
            summary_data = {'Ngày': future_dates.strftime('%Y-%m-%d')}
            for mt, pred in results.items():
                summary_data[mt] = [f"{p:,.0f}" for p in pred]
            st.dataframe(pd.DataFrame(summary_data), use_container_width=True)
            
        except Exception as e:
            st.error(f"❌ Lỗi: {str(e)}")

else:  # So sánh kết quả
    st.title("📊 So sánh kết quả dự đoán với thực tế")
    
    predictions_df = get_predictions()
    if predictions_df.empty:
        st.warning("Chưa có dữ liệu dự đoán. Hãy chạy dự đoán trước!")
    else:
        symbols = predictions_df['symbol'].unique().tolist()
        selected_symbol = st.selectbox("Chọn mã cổ phiếu", symbols)
        
        # Update actual prices
        if st.button("🔄 Cập nhật giá thực tế"):
            with st.spinner("Đang cập nhật..."):
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
                df = load_stock_data(selected_symbol, start_date, end_date)
                save_actual_prices(selected_symbol, df)
                st.success("✅ Đã cập nhật giá thực tế!")
                st.rerun()
        
        symbol_preds = predictions_df[predictions_df['symbol'] == selected_symbol]
        run_dates = symbol_preds['run_date'].unique().tolist()
        selected_run = st.selectbox("Chọn lần chạy", run_dates)
        
        run_preds = symbol_preds[symbol_preds['run_date'] == selected_run]
        
        # Get actual prices for comparison
        pred_start = run_preds['pred_start_date'].iloc[0]
        pred_end = run_preds['pred_end_date'].iloc[0]
        actual_df = get_actual_prices(selected_symbol, pred_start, pred_end)
        
        st.subheader("📈 Biểu đồ so sánh")
        fig = go.Figure()
        
        # Plot actual prices if available
        if not actual_df.empty:
            fig.add_trace(go.Scatter(x=actual_df['date'], y=actual_df['close_price'],
                mode='lines+markers', name='Giá thực tế', line=dict(color='blue', width=3)))
        
        # Plot predictions
        colors = {'NLinear': 'red', 'DLinear': 'green', 'LSTM': 'orange'}
        accuracy_results = []
        
        for _, row in run_preds.iterrows():
            mt = row['model_type']
            preds = json.loads(row['predictions'])
            dates = pd.date_range(start=row['pred_start_date'], periods=len(preds), freq='B')
            
            fig.add_trace(go.Scatter(x=dates, y=preds,
                mode='lines+markers', name=f'{mt} (dự đoán)', 
                line=dict(color=colors.get(mt, 'gray'), width=2, dash='dash')))
            
            # Calculate accuracy
            if not actual_df.empty:
                actual_prices = []
                for d in dates:
                    match = actual_df[actual_df['date'] == str(d.date())]
                    if not match.empty:
                        actual_prices.append(match['close_price'].iloc[0])
                
                if actual_prices:
                    mape, dir_acc = calculate_accuracy(preds, actual_prices)
                    accuracy_results.append({
                        'Mô hình': mt,
                        'MAPE (%)': f"{mape:.2f}" if mape else "N/A",
                        'Direction Accuracy (%)': f"{dir_acc:.2f}" if dir_acc else "N/A",
                        'Số ngày so sánh': len(actual_prices)
                    })
        
        fig.update_layout(title=f"So sánh dự đoán vs thực tế - {selected_symbol}",
            xaxis_title="Ngày", yaxis_title="Giá (VND)", hovermode='x unified', height=500)
        st.plotly_chart(fig, use_container_width=True)
        
        # Accuracy table
        if accuracy_results:
            st.subheader("📊 Độ chính xác các mô hình")
            st.info("MAPE: Mean Absolute Percentage Error (càng thấp càng tốt)\nDirection Accuracy: Tỷ lệ dự đoán đúng xu hướng tăng/giảm")
            acc_df = pd.DataFrame(accuracy_results)
            st.dataframe(acc_df, use_container_width=True)
            
            # Best model
            if len(accuracy_results) > 1:
                best = min(accuracy_results, key=lambda x: float(x['MAPE (%)']) if x['MAPE (%)'] != 'N/A' else float('inf'))
                st.success(f"🏆 Mô hình tốt nhất (MAPE thấp nhất): **{best['Mô hình']}** với MAPE = {best['MAPE (%)']}%")
        else:
            st.warning("⏳ Chưa có dữ liệu giá thực tế để so sánh. Hãy đợi đến ngày dự đoán và cập nhật giá!")
        
        # Historical accuracy summary
        st.subheader("📈 Tổng hợp độ chính xác theo thời gian")
        all_accuracy = []
        for _, row in predictions_df[predictions_df['symbol'] == selected_symbol].iterrows():
            actual_df_hist = get_actual_prices(selected_symbol, row['pred_start_date'], row['pred_end_date'])
            if not actual_df_hist.empty:
                preds = json.loads(row['predictions'])
                dates = pd.date_range(start=row['pred_start_date'], periods=len(preds), freq='B')
                actual_prices = [actual_df_hist[actual_df_hist['date'] == str(d.date())]['close_price'].iloc[0] 
                    for d in dates if not actual_df_hist[actual_df_hist['date'] == str(d.date())].empty]
                if actual_prices:
                    mape, _ = calculate_accuracy(preds, actual_prices)
                    if mape:
                        all_accuracy.append({'Ngày chạy': row['run_date'], 'Mô hình': row['model_type'], 'MAPE (%)': mape})
        
        if all_accuracy:
            hist_df = pd.DataFrame(all_accuracy)
            fig2 = go.Figure()
            for mt in hist_df['Mô hình'].unique():
                mt_data = hist_df[hist_df['Mô hình'] == mt]
                fig2.add_trace(go.Scatter(x=mt_data['Ngày chạy'], y=mt_data['MAPE (%)'],
                    mode='lines+markers', name=mt))
            fig2.update_layout(title="MAPE theo thời gian", xaxis_title="Ngày chạy", yaxis_title="MAPE (%)", height=400)
            st.plotly_chart(fig2, use_container_width=True)
            
            # Average accuracy
            avg_acc = hist_df.groupby('Mô hình')['MAPE (%)'].mean().reset_index()
            avg_acc.columns = ['Mô hình', 'MAPE trung bình (%)']
            avg_acc = avg_acc.sort_values('MAPE trung bình (%)')
            st.dataframe(avg_acc, use_container_width=True)
            st.success(f"🏆 Mô hình hiệu quả nhất tổng thể: **{avg_acc.iloc[0]['Mô hình']}**")

# Info section
with st.expander("ℹ️ Hướng dẫn"):
    st.markdown("""
    **Trang Dự đoán**: Chạy dự đoán với 1 hoặc cả 3 mô hình, kết quả được lưu vào database.
    
    **Trang So sánh**: So sánh kết quả dự đoán với giá thực tế, tính độ chính xác.
    
    **Các chỉ số**:
    - MAPE: Sai số phần trăm tuyệt đối trung bình (càng thấp càng tốt)
    - Direction Accuracy: Tỷ lệ dự đoán đúng xu hướng tăng/giảm
    
    ⚠️ **Lưu ý**: Đây chỉ là công cụ tham khảo, không phải khuyến nghị đầu tư.
    """)
