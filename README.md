# 📈 Stock Price Prediction with NLinear/DLinear

> Ứng dụng dự đoán giá cổ phiếu Việt Nam sử dụng các mô hình Deep Learning hiện đại (NLinear, DLinear, LSTM) kết hợp với công cụ phân tích xu hướng tin tức TrendNews.

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.0+-red.svg)](https://streamlit.io/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-orange.svg)](https://pytorch.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

![Stock Prediction Demo](image.png)

## ✨ Tính Năng Chính

### 🎯 Dự Đoán Giá Cổ Phiếu
- **3 Mô hình AI**: NLinear, DLinear, LSTM
- **Dữ liệu thực**: Tích hợp vnstock để lấy dữ liệu cổ phiếu Việt Nam
- **Dự đoán linh hoạt**: Tùy chỉnh số ngày lookback (30-120 ngày) và số ngày dự đoán (7-60 ngày)
- **Trực quan hóa**: Biểu đồ tương tác với Plotly

### 📰 Phân Tích Xu Hướng Tin Tức (TrendNews)
- Thu thập tin tức từ 11+ nền tảng (Weibo, Douyin, Baidu, Zhihu...)
- Phân tích từ khóa và xu hướng
- Thông báo qua Telegram/Email

![News Trend Demo](image1.png)
![Chatbot Demo](image2.png)


## 🚀 Cài Đặt

### Yêu Cầu
- Python 3.8+
- pip

### Bước 1: Clone Repository
```bash
git clone https://github.com/phanngoc/nlinear-predictStock.git
cd nlinear-predictStock
```

### Bước 2: Cài Đặt Dependencies
```bash
pip install -r requirements.txt
```

### Bước 3: Chạy Ứng Dụng
```bash
streamlit run app.py
```

Ứng dụng sẽ mở tại `http://localhost:8501`

## 📊 Mô Hình AI

### NLinear (Normalization-Linear)
- Chuẩn hóa dữ liệu bằng cách trừ giá trị cuối cùng
- Sử dụng linear layer đơn giản để dự đoán
- Hiệu quả với time-series có trend rõ ràng

### DLinear (Decomposition-Linear)
- Phân tách chuỗi thành **Trend** và **Seasonal** components
- Sử dụng 2 linear layers riêng biệt cho từng thành phần
- Phù hợp với dữ liệu có tính mùa vụ

### LSTM (Long Short-Term Memory)
- Mạng neural hồi quy với khả năng nhớ dài hạn
- Học các pattern phức tạp trong dữ liệu
- Hiệu quả với chuỗi thời gian phi tuyến

## 🎮 Hướng Dẫn Sử Dụng

1. **Nhập mã cổ phiếu**: Ví dụ `VNM`, `FPT`, `VIC`
2. **Chọn mô hình**: NLinear, DLinear hoặc LSTM
3. **Cấu hình tham số**:
   - Số ngày lookback: 30-120 ngày
   - Số ngày dự đoán: 7-60 ngày
   - Epochs: 50-300
   - Learning rate: 0.0001 - 0.005
4. **Bấm "Bắt đầu dự đoán"** và xem kết quả!

## 📁 Cấu Trúc Project

```
nlinear-predictStock/
├── app.py                  # 🚀 Ứng dụng Streamlit chính
├── requirements.txt        # 📦 Dependencies
├── guide_nlinear.md       # 📖 Hướng dẫn NLinear/DLinear
├── guide_vnstock.md       # 📖 Hướng dẫn vnstock API
├── README.md              # 📄 Documentation
│
└── TrendNews/             # 📰 Module phân tích tin tức
    ├── main.py            # Entry point
    ├── config/            # Cấu hình
    ├── src/               # Source code
    │   ├── core/          # Thu thập dữ liệu
    │   ├── processors/    # Xử lý dữ liệu
    │   ├── renderers/     # Render báo cáo
    │   └── notifiers/     # Gửi thông báo
    └── output/            # Kết quả phân tích
```

## 🔧 Công Nghệ Sử Dụng

| Công nghệ | Mục đích |
|-----------|----------|
| **Streamlit** | Web UI framework |
| **PyTorch** | Deep Learning framework |
| **vnstock** | API lấy dữ liệu cổ phiếu VN |
| **Plotly** | Biểu đồ tương tác |
| **Pandas** | Xử lý dữ liệu |
| **scikit-learn** | Tiền xử lý dữ liệu |

## 📈 Ví Dụ Kết Quả

```
📊 Dự đoán giá VNM - 40 ngày tới

┌─────────────────┬────────────────┬─────────────┐
│ Giá hiện tại    │ Giá dự đoán    │ Thay đổi    │
├─────────────────┼────────────────┼─────────────┤
│ 75,000 VND      │ 78,500 VND     │ +4.67%      │
└─────────────────┴────────────────┴─────────────┘
```

## ⚠️ Lưu Ý Quan Trọng

> **Disclaimer**: Đây chỉ là công cụ tham khảo và học tập. Kết quả dự đoán **không phải** là khuyến nghị đầu tư. Hãy luôn tham khảo ý kiến chuyên gia tài chính trước khi đưa ra quyết định đầu tư.

## 🔗 Tài Liệu Tham Khảo

- [vnstock Documentation](https://github.com/thinh-vu/vnstock)
- [NLinear/DLinear Paper](https://arxiv.org/abs/2205.13504)
- [Streamlit Documentation](https://docs.streamlit.io/)

## 🤝 Đóng Góp

Contributions are welcome! 

1. Fork repo
2. Tạo feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Mở Pull Request

## 📧 Liên Hệ

- GitHub: [@phanngoc](https://github.com/phanngoc)
- Issues: [GitHub Issues](https://github.com/phanngoc/nlinear-predictStock/issues)

## 📝 License

MIT License - xem [LICENSE](LICENSE) để biết thêm chi tiết.

---

Made with ❤️ by Phan Ngoc