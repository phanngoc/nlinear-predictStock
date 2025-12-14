
Tôi sẽ giúp bạn hiểu và áp dụng NLinear và DLinear cho dự đoán giá cổ phiếu. Đây là hai mô hình linear đơn giản nhưng rất hiệu quả cho time-series forecasting.

## Tổng quan về NLinear và DLinear

**NLinear (Normalization-Linear)**: Chuẩn hóa dữ liệu bằng cách trừ đi giá trị cuối cùng của chuỗi input, sau đó dùng một lớp linear để dự đoán, cuối cùng cộng lại giá trị đã trừ.

**DLinear (Decomposition-Linear)**: Phân tách chuỗi thành trend và seasonal components, sau đó dùng hai lớp linear riêng biệt để dự đoán từng thành phần.

## Code Implementation

Tôi sẽ tạo một ví dụ hoàn chỉnh cho bạn:

```python
import torch
import torch.nn as nn
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from torch.utils.data import Dataset, DataLoader
import matplotlib.pyplot as plt

# =============== Mô hình NLinear ===============
class NLinear(nn.Module):
    """
    Normalization-Linear
    """
    def __init__(self, seq_len, pred_len, individual=False, channels=1):
        super(NLinear, self).__init__()
        self.seq_len = seq_len
        self.pred_len = pred_len
        self.individual = individual
        self.channels = channels
        
        if self.individual:
            self.Linear = nn.ModuleList()
            for i in range(self.channels):
                self.Linear.append(nn.Linear(self.seq_len, self.pred_len))
        else:
            self.Linear = nn.Linear(self.seq_len, self.pred_len)
    
    def forward(self, x):
        # x: [Batch, Input length, Channel]
        seq_last = x[:, -1:, :].detach()
        x = x - seq_last  # Normalization
        
        if self.individual:
            output = torch.zeros([x.size(0), self.pred_len, x.size(2)], 
                                dtype=x.dtype).to(x.device)
            for i in range(self.channels):
                output[:, :, i] = self.Linear[i](x[:, :, i])
        else:
            x = x.permute(0, 2, 1)  # [Batch, Channel, Input length]
            output = self.Linear(x)
            output = output.permute(0, 2, 1)  # [Batch, Output length, Channel]
        
        output = output + seq_last  # De-normalization
        return output


# =============== Mô hình DLinear ===============
class MovingAvg(nn.Module):
    """
    Moving average block để trích xuất trend
    """
    def __init__(self, kernel_size, stride=1):
        super(MovingAvg, self).__init__()
        self.kernel_size = kernel_size
        self.avg = nn.AvgPool1d(kernel_size=kernel_size, stride=stride, padding=0)
    
    def forward(self, x):
        # x: [Batch, Length, Channel]
        front = x[:, 0:1, :].repeat(1, (self.kernel_size - 1) // 2, 1)
        end = x[:, -1:, :].repeat(1, (self.kernel_size - 1) // 2, 1)
        x = torch.cat([front, x, end], dim=1)
        x = self.avg(x.permute(0, 2, 1))
        x = x.permute(0, 2, 1)
        return x


class SeriesDecomp(nn.Module):
    """
    Series decomposition block
    """
    def __init__(self, kernel_size):
        super(SeriesDecomp, self).__init__()
        self.moving_avg = MovingAvg(kernel_size, stride=1)
    
    def forward(self, x):
        moving_mean = self.moving_avg(x)
        res = x - moving_mean
        return res, moving_mean


class DLinear(nn.Module):
    """
    Decomposition-Linear
    """
    def __init__(self, seq_len, pred_len, individual=False, channels=1, kernel_size=25):
        super(DLinear, self).__init__()
        self.seq_len = seq_len
        self.pred_len = pred_len
        self.individual = individual
        self.channels = channels
        
        # Decomposition
        self.decompsition = SeriesDecomp(kernel_size)
        
        if self.individual:
            self.Linear_Seasonal = nn.ModuleList()
            self.Linear_Trend = nn.ModuleList()
            
            for i in range(self.channels):
                self.Linear_Seasonal.append(nn.Linear(self.seq_len, self.pred_len))
                self.Linear_Trend.append(nn.Linear(self.seq_len, self.pred_len))
        else:
            self.Linear_Seasonal = nn.Linear(self.seq_len, self.pred_len)
            self.Linear_Trend = nn.Linear(self.seq_len, self.pred_len)
    
    def forward(self, x):
        # x: [Batch, Input length, Channel]
        seasonal_init, trend_init = self.decompsition(x)
        
        if self.individual:
            seasonal_output = torch.zeros([seasonal_init.size(0), self.pred_len, 
                                          seasonal_init.size(2)], 
                                         dtype=seasonal_init.dtype).to(seasonal_init.device)
            trend_output = torch.zeros([trend_init.size(0), self.pred_len, 
                                       trend_init.size(2)], 
                                      dtype=trend_init.dtype).to(trend_init.device)
            
            for i in range(self.channels):
                seasonal_output[:, :, i] = self.Linear_Seasonal[i](seasonal_init[:, :, i])
                trend_output[:, :, i] = self.Linear_Trend[i](trend_init[:, :, i])
        else:
            seasonal_init = seasonal_init.permute(0, 2, 1)
            trend_init = trend_init.permute(0, 2, 1)
            
            seasonal_output = self.Linear_Seasonal(seasonal_init)
            trend_output = self.Linear_Trend(trend_init)
            
            seasonal_output = seasonal_output.permute(0, 2, 1)
            trend_output = trend_output.permute(0, 2, 1)
        
        x = seasonal_output + trend_output
        return x


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


# =============== Hàm training ===============
def train_model(model, train_loader, val_loader, epochs, lr, device):
    model = model.to(device)
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    
    train_losses = []
    val_losses = []
    
    for epoch in range(epochs):
        # Training
        model.train()
        train_loss = 0
        for batch_x, batch_y in train_loader:
            batch_x = batch_x.to(device)
            batch_y = batch_y.to(device)
            
            optimizer.zero_grad()
            output = model(batch_x)
            loss = criterion(output, batch_y)
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item()
        
        train_loss /= len(train_loader)
        train_losses.append(train_loss)
        
        # Validation
        model.eval()
        val_loss = 0
        with torch.no_grad():
            for batch_x, batch_y in val_loader:
                batch_x = batch_x.to(device)
                batch_y = batch_y.to(device)
                
                output = model(batch_x)
                loss = criterion(output, batch_y)
                val_loss += loss.item()
        
        val_loss /= len(val_loader)
        val_losses.append(val_loss)
        
        if (epoch + 1) % 10 == 0:
            print(f'Epoch [{epoch+1}/{epochs}], Train Loss: {train_loss:.6f}, Val Loss: {val_loss:.6f}')
    
    return train_losses, val_losses


# =============== Ví dụ sử dụng ===============
if __name__ == "__main__":
    # Tạo dữ liệu giả lập (trong thực tế bạn sẽ load dữ liệu stock thật)
    np.random.seed(42)
    dates = pd.date_range('2020-01-01', periods=1000, freq='D')
    
    # Tạo dữ liệu giá cổ phiếu giả lập với trend và seasonality
    trend = np.linspace(100, 150, 1000)
    seasonal = 10 * np.sin(np.linspace(0, 8*np.pi, 1000))
    noise = np.random.randn(1000) * 2
    stock_prices = trend + seasonal + noise
    
    # Chuẩn hóa dữ liệu
    scaler = StandardScaler()
    stock_prices_scaled = scaler.fit_transform(stock_prices.reshape(-1, 1))
    
    # Chia dữ liệu
    train_size = int(len(stock_prices_scaled) * 0.7)
    val_size = int(len(stock_prices_scaled) * 0.15)
    
    train_data = stock_prices_scaled[:train_size]
    val_data = stock_prices_scaled[train_size:train_size + val_size]
    test_data = stock_prices_scaled[train_size + val_size:]
    
    # Hyperparameters
    seq_len = 60  # 60 ngày để dự đoán
    pred_len = 7  # Dự đoán 7 ngày tiếp theo
    batch_size = 32
    epochs = 50
    lr = 0.001
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    # Tạo datasets và dataloaders
    train_dataset = StockDataset(train_data, seq_len, pred_len)
    val_dataset = StockDataset(val_data, seq_len, pred_len)
    test_dataset = StockDataset(test_data, seq_len, pred_len)
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
    
    # Train NLinear
    print("=" * 50)
    print("Training NLinear Model")
    print("=" * 50)
    nlinear_model = NLinear(seq_len=seq_len, pred_len=pred_len, individual=False, channels=1)
    nlinear_train_losses, nlinear_val_losses = train_model(
        nlinear_model, train_loader, val_loader, epochs, lr, device
    )
    
    # Train DLinear
    print("\n" + "=" * 50)
    print("Training DLinear Model")
    print("=" * 50)
    dlinear_model = DLinear(seq_len=seq_len, pred_len=pred_len, individual=False, 
                            channels=1, kernel_size=25)
    dlinear_train_losses, dlinear_val_losses = train_model(
        dlinear_model, train_loader, val_loader, epochs, lr, device
    )
    
    # Đánh giá trên test set
    print("\n" + "=" * 50)
    print("Evaluation on Test Set")
    print("=" * 50)
    
    def evaluate(model, test_loader, device):
        model.eval()
        predictions = []
        actuals = []
        
        with torch.no_grad():
            for batch_x, batch_y in test_loader:
                batch_x = batch_x.to(device)
                output = model(batch_x)
                predictions.append(output.cpu().numpy())
                actuals.append(batch_y.numpy())
        
        predictions = np.concatenate(predictions, axis=0)
        actuals = np.concatenate(actuals, axis=0)
        
        mse = np.mean((predictions - actuals) ** 2)
        mae = np.mean(np.abs(predictions - actuals))
        
        return mse, mae, predictions, actuals
    
    nlinear_mse, nlinear_mae, nlinear_preds, nlinear_actuals = evaluate(
        nlinear_model, test_loader, device
    )
    dlinear_mse, dlinear_mae, dlinear_preds, dlinear_actuals = evaluate(
        dlinear_model, test_loader, device
    )
    
    print(f"NLinear - MSE: {nlinear_mse:.6f}, MAE: {nlinear_mae:.6f}")
    print(f"DLinear - MSE: {dlinear_mse:.6f}, MAE: {dlinear_mae:.6f}")
    
    print("\nTraining completed! Models saved.")
```

## Giải thích các thành phần chính:

1. **NLinear**: Đơn giản hơn, chỉ chuẩn hóa và dùng linear layer
2. **DLinear**: Phức tạp hơn, tách trend và seasonal components
3. **Moving Average**: Dùng để extract trend component
4. **Series Decomposition**: Tách signal thành trend và residual

## Ưu điểm:
- Đơn giản, dễ train
- Hiệu quả với long-term forecasting
- Ít tham số hơn so với Transformer
- Thường work tốt cho stock prediction

## Tips khi áp dụng thực tế:

1. **Feature engineering**: Thêm các features như volume, technical indicators (RSI, MACD)
2. **Multi-variate**: Set `channels > 1` để dự đoán nhiều features cùng lúc
3. **Individual mode**: Set `individual=True` nếu muốn mỗi feature có linear layer riêng
4. **Kernel size**: Điều chỉnh kernel_size trong DLinear phù hợp với chu kỳ dữ liệu


