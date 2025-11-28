"""
Script để kiểm tra và crawl dữ liệu tin tức nếu chưa có folder hôm nay.

Script này sẽ:
1. Kiểm tra xem folder hôm nay có tồn tại trong TrendNews/output/ không
2. Nếu chưa có hoặc folder rỗng, chạy python TrendNews/main.py để crawl
3. Trả về status (crawled/not_needed)
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime
import pytz


def get_beijing_time() -> datetime:
    """Get current Beijing time."""
    return datetime.now(pytz.timezone("Asia/Shanghai"))


def format_date_folder() -> str:
    """
    Format date for folder names.
    
    Returns:
        str: Formatted date string (e.g., "2025năm11tháng27ngày")
    """
    return get_beijing_time().strftime("%Ynăm%mtháng%dngày")


def check_today_folder_exists(output_base_path: Path) -> bool:
    """
    Kiểm tra xem folder hôm nay có tồn tại và có file txt không.
    
    Args:
        output_base_path: Đường dẫn đến thư mục TrendNews/output
        
    Returns:
        bool: True nếu folder tồn tại và có ít nhất 1 file txt
    """
    date_folder = format_date_folder()
    txt_dir = output_base_path / date_folder / "txt"
    
    if not txt_dir.exists():
        return False
    
    # Kiểm tra xem có file txt nào không
    txt_files = list(txt_dir.glob("*.txt"))
    return len(txt_files) > 0


def run_crawl_script(trendnews_main_path: Path) -> bool:
    """
    Chạy script crawl TrendNews/main.py.
    
    Args:
        trendnews_main_path: Đường dẫn đến TrendNews/main.py
        
    Returns:
        bool: True nếu crawl thành công, False nếu có lỗi
    """
    try:
        print(f"🔄 Bắt đầu crawl dữ liệu từ {trendnews_main_path}...")
        
        # Chạy script trong thư mục TrendNews để đảm bảo import paths đúng
        script_dir = trendnews_main_path.parent
        result = subprocess.run(
            [sys.executable, str(trendnews_main_path)],
            cwd=str(script_dir),
            capture_output=True,
            text=True,
            timeout=600  # Timeout 10 phút
        )
        
        if result.returncode == 0:
            print("✅ Crawl dữ liệu thành công!")
            return True
        else:
            print(f"❌ Lỗi khi crawl: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Crawl timeout sau 10 phút")
        return False
    except Exception as e:
        print(f"❌ Lỗi khi chạy crawl script: {e}")
        return False


def check_and_crawl(
    output_base_path: str = None,
    trendnews_main_path: str = None
) -> dict:
    """
    Kiểm tra và crawl dữ liệu nếu cần.
    
    Args:
        output_base_path: Đường dẫn đến TrendNews/output (mặc định: ../../TrendNews/output)
        trendnews_main_path: Đường dẫn đến TrendNews/main.py (mặc định: ../../TrendNews/main.py)
        
    Returns:
        dict: {
            "status": "crawled" | "not_needed",
            "date_folder": str,
            "message": str
        }
    """
    # Xác định đường dẫn mặc định
    script_dir = Path(__file__).parent.parent  # AnswerMe/backend
    project_root = script_dir.parent.parent  # nlinear-predictStock
    
    if output_base_path is None:
        output_base_path = project_root / "TrendNews" / "output"
    else:
        output_base_path = Path(output_base_path)
    
    if trendnews_main_path is None:
        trendnews_main_path = project_root / "TrendNews" / "main.py"
    else:
        trendnews_main_path = Path(trendnews_main_path)
    
    date_folder = format_date_folder()
    
    # Kiểm tra xem folder hôm nay đã tồn tại chưa
    if check_today_folder_exists(output_base_path):
        return {
            "status": "not_needed",
            "date_folder": date_folder,
            "message": f"Folder {date_folder} đã tồn tại và có dữ liệu"
        }
    
    # Chạy crawl nếu chưa có
    print(f"📂 Folder {date_folder} chưa tồn tại hoặc rỗng, bắt đầu crawl...")
    
    if not trendnews_main_path.exists():
        return {
            "status": "error",
            "date_folder": date_folder,
            "message": f"Không tìm thấy file {trendnews_main_path}"
        }
    
    success = run_crawl_script(trendnews_main_path)
    
    if success:
        # Kiểm tra lại sau khi crawl
        if check_today_folder_exists(output_base_path):
            return {
                "status": "crawled",
                "date_folder": date_folder,
                "message": f"Đã crawl thành công dữ liệu cho {date_folder}"
            }
        else:
            return {
                "status": "error",
                "date_folder": date_folder,
                "message": "Crawl hoàn thành nhưng không tìm thấy dữ liệu"
            }
    else:
        return {
            "status": "error",
            "date_folder": date_folder,
            "message": "Crawl thất bại"
        }


if __name__ == "__main__":
    result = check_and_crawl()
    print(f"\n📊 Kết quả: {result['status']}")
    print(f"📁 Folder: {result['date_folder']}")
    print(f"💬 {result['message']}")
    sys.exit(0 if result['status'] != 'error' else 1)

