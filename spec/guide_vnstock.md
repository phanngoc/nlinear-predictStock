
https://github.com/thinh-vu/vnstock
8.1. Cài đặt
Bạn có thể cài đặt thư viện bản phát hành ổn định qua PyPI với câu lệnh sau:

pip install -U vnstock
Bạn cũng có thể cài đặt bản phát hành thử nghiệm trên Github với câu lệnh:

pip install git+https://github.com/thinh-vu/vnstock
8.2. Nạp thư viện
Bạn cần nạp thư viện vào môi trường Python thông qua giao diện Jupyter Notebook hoặc Terminal để có thể gọi và sử dụng các hàm được cung cấp.

Có 4 cách nạp thư viện vào môi trường làm việc như sau:

8.2.1. Nạp thông qua giao diện làm việc chính
Giao diện làm việc chính cho phép chuyển đổi nguồn và chỉ cần khai báo tên mã khi khởi động. Cấu trúc này phù hợp khi phân tích xuyên suốt 1 mã chứng khoán và nguồn dữ liệu đồng thời giúp tăng độ ổn định của mã nguồn trong tương lai khi các nguồn dữ mới được bổ sung hoặc nguồn cũ hết hiệu lực, bạn chỉ cần đổi tên nguồn để tiếp tục sử dụng.

from vnstock import Vnstock
stock = Vnstock().stock(symbol='VCI', source='VCI')
stock.quote.history(start='2020-01-01', end='2024-05-25')
8.2.2. Nạp thông qua các class tổng hợp
Bạn chọn nạp một trong các lớp chức năng chính. Các lớp chức năng này cho phép chuyển đổi dễ dàng nguồn dữ liệu được hỗ trợ trong khi giữ nguyên cấu trúc hàm. Cấu trúc này giúp tăng độ ổn định của mã nguồn trong tương lai khi các nguồn dữ mới được bổ sung hoặc nguồn cũ hết hiệu lực, bạn chỉ cần đổi tên nguồn để tiếp tục sử dụng.

from vnstock import Listing, Quote, Company, Finance, Trading, Screener 
8.2.3. Nạp các lớp tính năng riêng lẻ theo nguồn dữ liệu cố định
Bạn cần tham khảo mã nguồn để sử dụng đúng các chức năng có sẵn trong thư viện.

from vnstock.explorer.vci import Listing, Quote, Company, Finance, Trading
hoặc

from vnstock.explorer.tcbs import Quote, Company, Finance, Trading, Screener
8.3. Danh sách niêm yết
Danh sách các mã chứng khoán sử dụng trong việc thiết lập vòng lặp truy xuất dữ liệu từ các chức năng khác như Giá lịch sử, Thông tin công ty, Báo cáo tài chính, vv

from vnstock import Listing
listing = Listing()
listing.all_symbols()
8.7. Giá lịch sử & thống kê giao dịch
Giá lịch sử
from vnstock import Vnstock
stock = Vnstock().stock(symbol='ACB', source='VCI')
stock.quote.history(start='2024-01-01', end='2025-03-19', interval='1D')
hoặc

from vnstock import Quote
quote = Quote(symbol='ACB', source='VCI')
quote.history(start='2024-01-01', end='2025-03-19', interval='1D')
8.5. Intraday
Dữ liệu giao dịch khớp lệnh theo từng tick

stock.quote.intraday(symbol='ACB', page_size=10_000, show_log=False)
Chi tiết vui lòng tham khảo tài liệu và Demo Notebook.

5.6. Bảng giá giao dịch
from vnstock import Trading
Trading(source='VCI').price_board(['VCB','ACB','TCB','BID'])
8.7. Truy xuất thông tin công ty
from vnstock import Vnstock
company = Vnstock().stock(symbol='ACB', source='VCI').company
company.overview()
hoặc

from vnstock import Company
company = Company(symbol='ACB', source='VCI')
company.overview()
8.8. Truy xuất báo cáo tài chính
from vnstock import Vnstock
stock = Vnstock().stock(symbol='VCI', source='VCI')
# Bảng cân đối kế toán - năm
stock.finance.balance_sheet(period='year', lang='vi', dropna=True)
# Bảng cân đối kế toán - quý
stock.finance.balance_sheet(period='quarter', lang='en', dropna=True)
# Kết quả hoạt động kinh doanh
stock.finance.income_statement(period='year', lang='vi', dropna=True)
# Lưu chuyển tiền tệ
stock.finance.cash_flow(period='year', dropna=True)
# Chỉ số tài chính
stock.finance.ratio(period='year', lang='vi', dropna=True)
8.9. Bộ lọc cổ phiếu
from vnstock import Screener
stock.screener.stock(params={"exchangeName": "HOSE,HNX,UPCOM"}, limit=1700)
8.10. Dữ liệu quỹ mở
from vnstock.explorer.fmarket.fund import Fund
fund = Fund()
fund.listing()
8.11. Dữ liệu thị trường quốc tế: Cổ phiếu, FX, Index
from vnstock import Vnstock
fx = Vnstock().fx(symbol='JPYVND', source='MSN')
df = fx.quote.history(start='2025-01-02', end='2025-03-20', interval='1D')
df
8.12. Tỷ giá & giá vàng
from vnstock.explorer.misc import *

# Tỷ giá ngoại tệ VCB
vcb_exchange_rate(date='2024-03-21')

# Giá vàng SJC
sjc_gold_price()
8.13. Xuất dữ liệu
Tất cả dữ liệu trả về từ Vnstock đều là Pandas DataFrame hoặc Series, do đó, bạn có thể mô hình hoá các thao tác phân tích của mình với lệnh Python dễ dàng nhờ hỗ trợ của AI. Nếu cần xuất dữ liệu sang các định dạng truyền thống, bạn chỉ cần gán các hàm mô tả ở trên với 1 tên biến và thực hiện xuất dữ liệu như dưới đây:

# Biến ratio_df lưu giá trị của phép tính vào bộ nhớ
ratio_df = stock.finance.ratio(period='year', lang='vi', dropna=True)

# Xuất dữ liệu ra Excel
ratio_df.to_excel('/nơi_lưu_file_của_bạn/tên_file-ratio_df.xlsx`, index=False')
# Xuất dữ liệu ra CSV
ratio_df.to_csv('/nơi_lưu_file_của_bạn/tên_file-ratio_df.csv`, index=False') 
