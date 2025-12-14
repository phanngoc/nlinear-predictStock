<img width="621" height="888" alt="Screenshot from 2025-11-25 08-29-27" src="https://github.com/user-attachments/assets/43bb2f53-8e60-4112-bc5f-61c9bb62e909" />


# Phiên bản refactor của TrendRadar 📡

> Công cụ phân tích xu hướng tin tức từ nhiều nền tảng truyền thông Trung Quốc với kiến trúc modular.

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## ✨ Tính Năng

- 🌐 **Thu thập từ 11+ nền tảng**: Weibo, Douyin, Baidu, Zhihu, Bilibili, v.v.
- 🔍 **Phân tích từ khóa thông minh**: Theo dõi xu hướng theo từ khóa tùy chỉnh
- 📊 **Báo cáo HTML đẹp mắt**: Giao diện hiện đại, responsive
- 📨 **Đa kênh thông báo**: Telegram, Email và nhiều hơn nữa
- 🔄 **3 chế độ hoạt động**: Daily, Incremental, Current
- 🏗️ **Kiến trúc modular**: Code sạch, dễ bảo trì và mở rộng
- 🐳 **Docker support**: Triển khai dễ dàng
- 🔒 **Proxy support**: Bảo mật và ổn định

## 🚀 Cài Đặt Nhanh

### Yêu Cầu

- Python 3.8+
- pip

### Cài Đặt Dependencies

```bash
pip install -r requirements.txt
```

## ⚙️ Cấu Hình

### 1. Tạo File Cấu Hình

```bash
cp config/config.yaml.example config/config.yaml
```

### 2. Chỉnh Sửa Cấu Hình

Mở `config/config.yaml` và điều chỉnh:

```yaml
# Chế độ báo cáo
report_mode: daily  # daily | incremental | current

# Cấu hình Telegram (tùy chọn)
telegram_bot_token: "YOUR_BOT_TOKEN"
telegram_chat_id: "YOUR_CHAT_ID"

# Cấu hình Email (tùy chọn)
email_from: "your-email@gmail.com"
email_password: "your-app-password"
email_to: "recipient@example.com"

# Platforms cần theo dõi
platforms:
  - id: weibo
    name: 微博
  - id: douyin
    name: 抖音
  # ... thêm platforms khác
```

### 3. Cấu Hình Từ Khóa

Chỉnh sửa `config/frequency_words.txt` để thêm từ khóa bạn muốn theo dõi:

```
AI
ChatGPT
Machine Learning
# Mỗi từ khóa một dòng
```

## 🎯 Sử Dụng

### Chạy Chương Trình

```bash
python3 main.py
```

### Các Chế Độ Hoạt Động

| Chế độ | Mô tả | Sử dụng khi |
|--------|-------|-------------|
| **daily** | Tổng hợp tất cả tin tức trong ngày | Muốn xem toàn bộ xu hướng |
| **incremental** | Chỉ tin tức mới xuất hiện | Theo dõi real-time |
| **current** | Bảng xếp hạng hiện tại | Xem trending hiện tại |

Cấu hình trong `config/config.yaml`:
```yaml
report_mode: daily  # hoặc incremental, current
```

## 📁 Cấu Trúc Project

```
TrendRadar/
├── config/                      # 📝 Cấu hình
│   ├── config.yaml             # Cấu hình chính
│   └── frequency_words.txt     # Từ khóa theo dõi
│
├── src/                        # 💻 Source Code (Modular Architecture)
│   ├── config/                 # Quản lý cấu hình
│   │   ├── __init__.py
│   │   ├── config_loader.py    # Load YAML config
│   │   └── smtp_config.py      # SMTP settings
│   │
│   ├── core/                   # Thành phần cốt lõi
│   │   ├── __init__.py
│   │   ├── data_fetcher.py     # Thu thập dữ liệu
│   │   └── push_manager.py     # Quản lý push notification
│   │
│   ├── processors/             # Xử lý dữ liệu
│   │   ├── __init__.py
│   │   ├── data_processor.py   # Xử lý dữ liệu thô
│   │   ├── statistics.py       # Thống kê và phân tích
│   │   ├── frequency_words.py  # Xử lý từ khóa
│   │   └── report_processor.py # Chuẩn bị dữ liệu báo cáo
│   │
│   ├── renderers/              # Render báo cáo
│   │   ├── __init__.py
│   │   ├── html_renderer.py    # Render HTML reports
│   │   └── telegram_renderer.py # Format cho Telegram
│   │
│   ├── notifiers/              # Gửi thông báo
│   │   ├── __init__.py
│   │   ├── manager.py          # Quản lý notifications
│   │   ├── telegram.py         # Telegram notifier
│   │   └── email.py            # Email notifier
│   │
│   └── utils/                  # Tiện ích
│       ├── __init__.py
│       ├── time_utils.py       # Xử lý thời gian
│       ├── text_utils.py       # Xử lý text
│       ├── file_utils.py       # Xử lý file
│       ├── format_utils.py     # Format dữ liệu
│       ├── message_utils.py    # Xử lý message
│       └── version_check.py    # Kiểm tra version
│
├── output/                     # 📊 Kết quả
│   └── YYYY年MM月DD日/
│       ├── html/               # Báo cáo HTML
│       └── txt/                # Dữ liệu thô
│
├── main.py                     # 🚀 Entry point
├── requirements.txt            # 📦 Dependencies
├── README.md                   # 📖 Documentation
└── REFACTOR_PLAN.md           # 🗺️ Refactoring plan
```

## 🏗️ Kiến Trúc Modular

### Nguyên Tắc Thiết Kế

1. **Separation of Concerns**: Mỗi module có trách nhiệm rõ ràng
2. **Single Responsibility**: Mỗi class/function làm một việc duy nhất
3. **Dependency Injection**: Dễ dàng test và mở rộng
4. **Clean Code**: Code dễ đọc, dễ bảo trì

### Luồng Hoạt Động

```
┌─────────────┐
│   main.py   │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│      NewsAnalyzer (main.py)         │
│  - Điều phối toàn bộ workflow       │
└──────┬──────────────────────────────┘
       │
       ├──► DataFetcher (core/)
       │    └─ Thu thập dữ liệu từ platforms
       │
       ├──► Processors (processors/)
       │    ├─ Xử lý dữ liệu thô
       │    ├─ Phân tích thống kê
       │    └─ Chuẩn bị báo cáo
       │
       ├──► Renderers (renderers/)
       │    ├─ HTMLRenderer: Tạo báo cáo HTML
       │    └─ TelegramRenderer: Format cho Telegram
       │
       └──► Notifiers (notifiers/)
            ├─ TelegramNotifier: Gửi Telegram
            └─ EmailNotifier: Gửi Email
```

## 📊 Platforms Hỗ Trợ

| Platform | ID | Mô tả |
|----------|-------|-------|
| 今日头条 | `toutiao` | Toutiao News |
| 百度热搜 | `baidu` | Baidu Hot Search |
| 华尔街见闻 | `wallstreetcn-hot` | Wallstreetcn |
| 澎湃新闻 | `thepaper` | The Paper |
| bilibili | `bilibili-hot-search` | Bilibili Hot |
| 财联社 | `cls-hot` | CLS Hot |
| 凤凰网 | `ifeng` | Ifeng News |
| 贴吧 | `tieba` | Tieba |
| 微博 | `weibo` | Weibo |
| 抖音 | `douyin` | Douyin |
| 知乎 | `zhihu` | Zhihu |

## 🔔 Kênh Thông Báo

### Telegram

```yaml
telegram_bot_token: "YOUR_BOT_TOKEN"
telegram_chat_id: "YOUR_CHAT_ID"
```

### Email

```yaml
email_from: "your-email@gmail.com"
email_password: "your-app-password"
email_to: "recipient@example.com"
```

Hỗ trợ các SMTP providers:
- Gmail
- Outlook
- QQ Mail
- 163 Mail
- Custom SMTP

## 🐳 Docker

```bash
# Build image
docker build -t trendradar .

# Run container
docker run -d \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/output:/app/output \
  trendradar
```

## 🛠️ Development

### Cấu Trúc Code

- **config/**: Quản lý cấu hình YAML và SMTP
- **core/**: Components cốt lõi (DataFetcher, PushManager)
- **processors/**: Xử lý và phân tích dữ liệu
- **renderers/**: Render báo cáo (HTML, Telegram)
- **notifiers/**: Gửi thông báo đa kênh
- **utils/**: Các hàm tiện ích

### Best Practices

1. Tuân thủ PEP 8
2. Viết docstrings cho functions/classes
3. Sử dụng type hints
4. Tách biệt concerns
5. Viết code dễ test

Xem thêm trong `CLAUDE.md` và `src/README.md`

## 📈 Ví Dụ Output

### Báo cáo HTML

![HTML Report Example](_image/html-report.png)

### Telegram Notification

```
📊 Thống kê từ khóa nóng

🔥 [1/5] AI : 15 tin

  1. [微博] ChatGPT phát hành tính năng mới [3] - 10:30
  2. [知乎] AI sẽ thay thế lập trình viên? [5-8] - 11:20
  ...
```

## 🔧 Troubleshooting

### Lỗi kết nối

```bash
# Kiểm tra proxy
USE_PROXY: true
DEFAULT_PROXY: "http://127.0.0.1:7890"
```

### Lỗi SMTP

```bash
# Sử dụng App Password cho Gmail
# Không dùng mật khẩu thường
```

## 📝 License

MIT License - xem [LICENSE](LICENSE) để biết thêm chi tiết.

## 🤝 Contributing

Contributions are welcome! 

1. Fork repo
2. Tạo feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Mở Pull Request

## 📧 Contact

- Issues: [GitHub Issues](https://github.com/sansan0/TrendRadar/issues)
- Discussions: [GitHub Discussions](https://github.com/sansan0/TrendRadar/discussions)

## 🙏 Acknowledgments

- Cảm ơn tất cả contributors
- Inspired by các công cụ phân tích xu hướng

---

Made with ❤️ by TrendRadar Team
