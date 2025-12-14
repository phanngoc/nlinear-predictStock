# TrendRadar - Modular Source Code

Đây là cấu trúc module hóa của TrendRadar, được refactor từ file `main.py` gốc.

## Cấu Trúc

### 📦 config/
Quản lý cấu hình ứng dụng
- `constants.py`: VERSION, SMTP_CONFIGS
- `settings.py`: load_config(), CONFIG

### 🔧 core/
Core components chính
- `data_fetcher.py`: Lấy dữ liệu từ API
- `push_manager.py`: Quản lý push notifications
- `analyzer.py`: Main analyzer (simplified)

### ⚙️ processors/
Xử lý dữ liệu
- `data_processor.py`: Parse và save titles
- `statistics.py`: Tính toán thống kê
- `frequency_words.py`: Xử lý từ khóa

### 🎨 renderers/
Render nội dung cho các platforms
- `base.py`: Base renderer class
- `html_renderer.py`: HTML reports
- `feishu_renderer.py`: Feishu messages
- `dingtalk_renderer.py`: DingTalk messages
- `wework_renderer.py`: WeWork messages
- `telegram_renderer.py`: Telegram messages
- `ntfy_renderer.py`: ntfy messages

### 📤 notifiers/
Gửi thông báo
- `base.py`: Base notifier class
- `feishu.py`: Feishu notifications
- `dingtalk.py`: DingTalk notifications
- `wework.py`: WeWork notifications
- `telegram.py`: Telegram notifications
- `email.py`: Email notifications
- `ntfy.py`: ntfy notifications
- `manager.py`: Notification orchestration

### 🛠️ utils/
Utility functions
- `time_utils.py`: Time formatting
- `file_utils.py`: File operations
- `text_utils.py`: Text processing
- `format_utils.py`: Content formatting

## Import Examples

```python
# Config
from src.config import VERSION, CONFIG

# Core
from src.core import DataFetcher, PushRecordManager, NewsAnalyzer

# Processors
from src.processors import (
    load_frequency_words,
    calculate_news_weight,
    save_titles_to_file,
)

# Utils
from src.utils import (
    get_beijing_time,
    clean_title,
    format_rank_display,
)

# Renderers
from src.renderers import HTMLRenderer, FeishuRenderer

# Notifiers
from src.notifiers import FeishuNotifier, EmailNotifier
```

## Usage

```python
from src.main import main

if __name__ == "__main__":
    main()
```

## Testing

Mỗi module có thể được test độc lập:

```python
# Test config
from src.config import CONFIG
assert CONFIG is not None

# Test utils
from src.utils import clean_title
assert clean_title("  Test  ") == "Test"

# Test processors
from src.processors import load_frequency_words
word_groups, filters = load_frequency_words()
assert len(word_groups) > 0
```

## Status

- ✅ Config: Fully implemented
- ✅ Utils: Fully implemented  
- ✅ Core: Fully implemented (simplified analyzer)
- ✅ Processors: Partially implemented
- 🔄 Renderers: Structure only
- 🔄 Notifiers: Structure only

## Notes

- Modular structure hoàn chỉnh
- Backward compatible với main.py gốc
- Sẵn sàng cho full implementation
- Tuân thủ SOLID principles
