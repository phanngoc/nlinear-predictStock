# CLAUDE.md - Best Practices for TrendRadar Development

## 📋 Tổng Quan

File này chứa best practices và guidelines khi phát triển TrendRadar với Claude AI.

## 🏗️ Kiến Trúc Project

### Cấu Trúc Modular

Project sử dụng **modular architecture** với các packages riêng biệt:

```
src/
├── config/         # Quản lý cấu hình
├── core/           # Core business logic
├── processors/     # Data processing
├── renderers/      # Report generation
├── notifiers/      # Notification sending
└── utils/          # Shared utilities
```

### Nguyên Tắc Thiết Kế

1. **Single Responsibility**: Mỗi module chỉ làm một việc
2. **Dependency Injection**: Inject dependencies qua constructor
3. **Configuration Over Code**: Ưu tiên config file hơn hardcode
4. **Fail Fast**: Validate inputs sớm, throw errors rõ ràng

## 🔧 Development Guidelines

### 1. Khi Thêm Feature Mới

```python
# ✅ ĐÚNG: Tạo module mới trong package phù hợp
# src/processors/new_processor.py

from typing import Dict, List
from src.config import CONFIG

def process_new_data(data: Dict) -> List:
    """
    Process new data type.
    
    Args:
        data: Input data dictionary
        
    Returns:
        List: Processed results
    """
    # Implementation
    pass
```

```python
# ❌ SAI: Thêm code vào main.py
def process_new_data(data):
    # Không nên thêm vào main.py
    pass
```

### 2. Import Guidelines

```python
# ✅ ĐÚNG: Import từ modules
from src.config import CONFIG, VERSION
from src.core import DataFetcher
from src.utils import get_beijing_time

# ❌ SAI: Import từ main.py
from main import some_function  # Tránh điều này
```

### 3. Configuration Management

```python
# ✅ ĐÚNG: Sử dụng CONFIG
from src.config import CONFIG

def my_function():
    interval = CONFIG["REQUEST_INTERVAL"]
    platforms = CONFIG["PLATFORMS"]

# ❌ SAI: Hardcode values
def my_function():
    interval = 1000  # Không nên hardcode
```

### 4. Error Handling

```python
# ✅ ĐÚNG: Specific exceptions với messages rõ ràng
try:
    data = fetch_data()
except requests.RequestException as e:
    print(f"Lỗi khi fetch data: {e}")
    raise
except json.JSONDecodeError as e:
    print(f"Lỗi parse JSON: {e}")
    return None

# ❌ SAI: Catch all exceptions
try:
    data = fetch_data()
except Exception:
    pass  # Silent fail - rất nguy hiểm
```

### 5. Type Hints

```python
# ✅ ĐÚNG: Sử dụng type hints
from typing import Dict, List, Optional

def process_titles(
    titles: Dict[str, List[str]], 
    threshold: int = 5
) -> Optional[Dict]:
    """Process titles with type safety."""
    pass

# ❌ SAI: Không có type hints
def process_titles(titles, threshold=5):
    pass
```

### 6. Docstrings

```python
# ✅ ĐÚNG: Docstring đầy đủ
def calculate_weight(data: Dict, threshold: int) -> float:
    """
    Calculate news weight for ranking.
    
    Args:
        data: Title data with ranks and count
        threshold: Rank threshold for highlighting
        
    Returns:
        float: Calculated weight score
        
    Example:
        >>> data = {"ranks": [1, 2], "count": 3}
        >>> calculate_weight(data, 5)
        24.5
    """
    pass

# ❌ SAI: Không có docstring
def calculate_weight(data, threshold):
    pass
```

## 🧪 Testing

### Unit Tests

```python
# tests/test_processors.py
import pytest
from src.processors import calculate_news_weight

def test_calculate_weight():
    data = {"ranks": [1, 2, 3], "count": 3}
    weight = calculate_news_weight(data, rank_threshold=5)
    assert weight > 0
    assert isinstance(weight, float)
```

### Integration Tests

```python
# tests/test_integration.py
from src.core import DataFetcher
from src.config import CONFIG

def test_full_pipeline():
    fetcher = DataFetcher()
    results, _, _ = fetcher.crawl_websites([("test_id", "Test")])
    assert isinstance(results, dict)
```

## 📝 Code Style

### Naming Conventions

```python
# Classes: PascalCase
class DataFetcher:
    pass

# Functions/Variables: snake_case
def fetch_data():
    pass

user_name = "test"

# Constants: UPPER_SNAKE_CASE
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 10
```

### File Organization

```python
# ✅ ĐÚNG: Organize imports
# Standard library
import os
import json
from pathlib import Path

# Third-party
import requests
from typing import Dict, List

# Local
from src.config import CONFIG
from src.utils import get_beijing_time

# ❌ SAI: Mixed imports
from src.config import CONFIG
import os
import requests
from src.utils import get_beijing_time
```

## 🔄 Refactoring Guidelines

### Legacy Functions (`src/legacy_functions.py`)

The file `src/legacy_functions.py` contains ~3200 lines of complex functions that haven't been fully refactored yet. This is intentional - it serves as a compatibility layer while we progressively refactor.

**What's in there:**
- Statistics & frequency counting
- HTML report generation (1000+ lines of HTML/CSS/JS)
- Content rendering for 6 platforms (Feishu, DingTalk, WeWork, Telegram, Email, ntfy)
- Notification sending logic
- Content batching algorithms

**How to refactor progressively:**

1. **Pick one function** to refactor (start with smallest)
2. **Create proper module** in appropriate package:
   ```
   src/renderers/html_renderer.py
   src/notifiers/feishu.py
   src/processors/statistics.py
   ```
3. **Move function** with all dependencies
4. **Update imports** in `main.py`
5. **Test thoroughly**
6. **Remove from legacy_functions.py**

**Example refactoring:**
```python
# Before: in src/legacy_functions.py
def check_version_update(...):
    # 40 lines of code

# After: in src/utils/version_check.py
def check_version_update(...):
    # Same 40 lines

# Update main.py:
from src.utils.version_check import check_version_update
```

### Khi Refactor Code

1. **Backup trước**: Luôn tạo backup trước khi refactor lớn
2. **Refactor từng bước**: Không refactor quá nhiều cùng lúc
3. **Test sau mỗi bước**: Chạy tests sau mỗi thay đổi
4. **Commit thường xuyên**: Commit sau mỗi refactor nhỏ

### Legacy Code

```python
# Khi cần sử dụng legacy functions tạm thời
from main import legacy_function  # TODO: Refactor this

# Thêm comment giải thích
def new_function():
    # Using legacy function temporarily
    # Will be refactored in Phase X
    result = legacy_function()
    return result
```

## 🚀 Performance

### Optimization Tips

```python
# ✅ ĐÚNG: Cache kết quả nếu có thể
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_calculation(n: int) -> int:
    # Expensive operation
    return result

# ✅ ĐÚNG: Sử dụng generators cho large datasets
def process_large_data(items):
    for item in items:
        yield process_item(item)

# ❌ SAI: Load all vào memory
def process_large_data(items):
    return [process_item(item) for item in items]
```

## 🔐 Security

### Sensitive Data

```python
# ✅ ĐÚNG: Sử dụng environment variables
import os

webhook_url = os.environ.get("FEISHU_WEBHOOK_URL")
api_key = os.environ.get("API_KEY")

# ❌ SAI: Hardcode credentials
webhook_url = "https://open.feishu.cn/..."  # Nguy hiểm!
```

### Input Validation

```python
# ✅ ĐÚNG: Validate inputs
def process_title(title: str) -> str:
    if not isinstance(title, str):
        raise TypeError("Title must be string")
    if not title.strip():
        raise ValueError("Title cannot be empty")
    return title.strip()
```

## 📊 Logging

```python
# ✅ ĐÚNG: Informative logging
print(f"Fetching data from {platform_id}...")
print(f"✓ Successfully fetched {len(results)} items")
print(f"✗ Failed to fetch from {platform_id}: {error}")

# ❌ SAI: Vague logging
print("Fetching...")
print("Done")
print("Error")
```

## 🎯 Version Control

### Commit Messages

```bash
# ✅ ĐÚNG: Descriptive commits
git commit -m "feat: Add Telegram notifier support"
git commit -m "fix: Handle empty title in data processor"
git commit -m "refactor: Extract config loading to separate module"

# ❌ SAI: Vague commits
git commit -m "update"
git commit -m "fix bug"
git commit -m "changes"
```

### Branch Strategy

```bash
# Feature development
git checkout -b feature/telegram-support

# Bug fixes
git checkout -b fix/empty-title-handling

# Refactoring
git checkout -b refactor/config-module
```

## 🤖 Working with Claude

### Effective Prompts

```
✅ ĐÚNG: Specific và có context
"Tôi cần refactor hàm count_word_frequency trong main.py. 
Hàm này có 300 dòng và xử lý word matching. 
Hãy tách thành các functions nhỏ hơn trong src/processors/statistics.py"

❌ SAI: Vague
"Refactor code"
```

### Iterative Development

1. **Chia nhỏ tasks**: Refactor từng module một
2. **Test từng bước**: Verify sau mỗi thay đổi
3. **Ask for clarification**: Hỏi khi không chắc chắn
4. **Review suggestions**: Không accept blindly

## 📚 Resources

### Documentation

- `README.md` - Project overview
- `src/README.md` - Module documentation
- Inline docstrings - Function documentation

### Code Examples

Xem các modules trong `src/` để tham khảo:
- `src/config/settings.py` - Configuration pattern
- `src/core/data_fetcher.py` - Class design pattern
- `src/utils/time_utils.py` - Utility functions pattern

## ✅ Checklist Trước Khi Commit

- [ ] Code chạy không lỗi
- [ ] Đã thêm docstrings
- [ ] Đã thêm type hints
- [ ] Đã test manually
- [ ] Đã remove debug prints
- [ ] Đã update README nếu cần
- [ ] Commit message rõ ràng

## 🎓 Learning Path

### Cho Người Mới

1. Đọc `README.md`
2. Xem cấu trúc `src/`
3. Chạy `main_refactored.py` để hiểu flow
4. Đọc code trong `src/config/` và `src/utils/`
5. Thử thêm feature nhỏ

### Cho Contributors

1. Review CLAUDE.md này
2. Hiểu modular architecture
3. Follow coding standards
4. Write tests
5. Submit clean PRs

---

**Happy Coding! 🚀**

*Last updated: 2025-11-23*
