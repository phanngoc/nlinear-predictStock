from typing import Dict, List, Optional
from pathlib import Path
from src.utils import (
    get_beijing_time,
    format_time_filename,
    html_escape,
    get_output_path,
)
from src.utils.format_utils import format_rank_display
from src.utils.text_utils import clean_title
from src.processors.report_processor import prepare_report_data

class HTMLRenderer:
    @staticmethod
    def format_title(title_data: Dict, show_source: bool = True) -> str:
        """
        Format title for HTML platform.
        """
        rank_display = format_rank_display(
            title_data["ranks"], title_data["rank_threshold"], "html"
        )

        link_url = title_data["mobile_url"] or title_data["url"]
        cleaned_title = clean_title(title_data["title"])

        escaped_title = html_escape(cleaned_title)
        escaped_source_name = html_escape(title_data["source_name"])

        if link_url:
            escaped_url = html_escape(link_url)
            formatted_title = f'[{escaped_source_name}] <a href="{escaped_url}" target="_blank" class="news-link">{escaped_title}</a>'
        else:
            formatted_title = (
                f'[{escaped_source_name}] <span class="no-link">{escaped_title}</span>'
            )

        if rank_display:
            formatted_title += f" {rank_display}"
        if title_data["time_display"]:
            escaped_time = html_escape(title_data["time_display"])
            formatted_title += f" <font color='grey'>- {escaped_time}</font>"
        if title_data["count"] > 1:
            formatted_title += f" <font color='green'>({title_data['count']}lần)</font>"

        if title_data.get("is_new"):
            formatted_title = f"<div class='new-title'>🆕 {formatted_title}</div>"

        return formatted_title

    @staticmethod
    def generate_report(
        stats: List[Dict],
        total_titles: int,
        failed_ids: Optional[List] = None,
        new_titles: Optional[Dict] = None,
        id_to_name: Optional[Dict] = None,
        mode: str = "daily",
        is_daily_summary: bool = False,
        update_info: Optional[Dict] = None,
    ) -> str:
        """tạoHTMLbáo cáo"""
        if is_daily_summary:
            if mode == "current":
                filename = "bảng xếp hạng hiện tạitổng hợp.html"
            elif mode == "incremental":
                filename = "当ngàytăng dần.html"
            else:
                filename = "当ngàytổng hợp.html"
        else:
            filename = f"{format_time_filename()}.html"

        file_path = get_output_path("html", filename)

        report_data = prepare_report_data(stats, failed_ids, new_titles, id_to_name, mode)

        html_content = HTMLRenderer.render_content(
            report_data, total_titles, is_daily_summary, mode, update_info
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        if is_daily_summary:
            root_file_path = Path("index.html")
            with open(root_file_path, "w", encoding="utf-8") as f:
                f.write(html_content)

        return file_path

    @staticmethod
    def render_content(
        report_data: Dict,
        total_titles: int,
        is_daily_summary: bool = False,
        mode: str = "daily",
        update_info: Optional[Dict] = None,
    ) -> str:
        """renderHTMLnội dung"""
        html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Tin tức nóngphút析</title>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js" integrity="sha512-BNaRQnYJYiPSqHHDb58B0yaPfCu+Wgds8Gp/gU33kqBtgNS4tSPHuGibyoeqMV/TJlSKda6FXzoEyYGjTe+vXA==" crossorigin="anonymous" referrerpolicy="no-referrer"></script>
        <style>
            * { box-sizing: border-box; }
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
                margin: 0; 
                padding: 16px; 
                background: #fafafa;
                color: #333;
                line-height: 1.5;
            }
            
            .container {
                max-width: 600px;
                margin: 0 auto;
                background: white;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 2px 16px rgba(0,0,0,0.06);
            }
            
            .header {
                background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
                color: white;
                padding: 32px 24px;
                text-align: center;
                position: relative;
            }
            
            .save-buttons {
                position: absolute;
                top: 16px;
                right: 16px;
                display: flex;
                gap: 8px;
            }
            
            .save-btn {
                background: rgba(255, 255, 255, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.3);
                color: white;
                padding: 8px 16px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 13px;
                font-weight: 500;
                transition: all 0.2s ease;
                backdrop-filter: blur(10px);
                white-space: nowrap;
            }
            
            .save-btn:hover {
                background: rgba(255, 255, 255, 0.3);
                border-color: rgba(255, 255, 255, 0.5);
                transform: translateY(-1px);
            }
            
            .save-btn:active {
                transform: translateY(0);
            }
            
            .save-btn:disabled {
                opacity: 0.6;
                cursor: not-allowed;
            }
            
            .header-title {
                font-size: 22px;
                font-weight: 700;
                margin: 0 0 20px 0;
            }
            
            .header-info {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 16px;
                font-size: 14px;
                opacity: 0.95;
            }
            
            .info-item {
                text-align: center;
            }
            
            .info-label {
                display: block;
                font-size: 12px;
                opacity: 0.8;
                margin-bottom: 4px;
            }
            
            .info-value {
                font-weight: 600;
                font-size: 16px;
            }
            
            .content {
                padding: 24px;
            }
            
            .word-group {
                margin-bottom: 40px;
            }
            
            .word-group:first-child {
                margin-top: 0;
            }
            
            .word-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 20px;
                padding-bottom: 8px;
                border-bottom: 1px solid #f0f0f0;
            }
            
            .word-info {
                display: flex;
                align-items: center;
                gap: 12px;
            }
            
            .word-name {
                font-size: 17px;
                font-weight: 600;
                color: #1a1a1a;
            }
            
            .word-count {
                color: #666;
                font-size: 13px;
                font-weight: 500;
            }
            
            .word-count.hot { color: #dc2626; font-weight: 600; }
            .word-count.warm { color: #ea580c; font-weight: 600; }
            
            .word-index {
                color: #999;
                font-size: 12px;
            }
            
            .news-item {
                margin-bottom: 20px;
                padding: 16px 0;
                border-bottom: 1px solid #f5f5f5;
                position: relative;
                display: flex;
                gap: 12px;
                align-items: center;
            }
            
            .news-item:last-child {
                border-bottom: none;
            }
            
            .news-item.new::after {
                content: "NEW";
                position: absolute;
                top: 12px;
                right: 0;
                background: #fbbf24;
                color: #92400e;
                font-size: 9px;
                font-weight: 700;
                padding: 3px 6px;
                border-radius: 4px;
                letter-spacing: 0.5px;
            }
            
            .news-number {
                color: #999;
                font-size: 13px;
                font-weight: 600;
                min-width: 20px;
                text-align: center;
                flex-shrink: 0;
                background: #f8f9fa;
                border-radius: 50%;
                width: 24px;
                height: 24px;
                display: flex;
                align-items: center;
                justify-content: center;
                align-self: flex-start;
                margin-top: 8px;
            }
            
            .news-content {
                flex: 1;
                min-width: 0;
                padding-right: 40px;
            }
            
            .news-item.new .news-content {
                padding-right: 50px;
            }
            
            .news-header {
                display: flex;
                align-items: center;
                gap: 8px;
                margin-bottom: 8px;
                flex-wrap: wrap;
            }
            
            .source-name {
                color: #666;
                font-size: 12px;
                font-weight: 500;
            }
            
            .rank-num {
                color: #fff;
                background: #6b7280;
                font-size: 10px;
                font-weight: 700;
                padding: 2px 6px;
                border-radius: 10px;
                min-width: 18px;
                text-align: center;
            }
            
            .rank-num.top { background: #dc2626; }
            .rank-num.high { background: #ea580c; }
            
            .time-info {
                color: #999;
                font-size: 11px;
            }
            
            .count-info {
                color: #059669;
                font-size: 11px;
                font-weight: 500;
            }
            
            .news-title {
                font-size: 15px;
                line-height: 1.4;
                color: #1a1a1a;
                margin: 0;
            }
            
            .news-link {
                color: #2563eb;
                text-decoration: none;
            }
            
            .news-link:hover {
                text-decoration: underline;
            }
            
            .news-link:visited {
                color: #7c3aed;
            }
            
            .new-section {
                margin-top: 40px;
                padding-top: 24px;
                border-top: 2px solid #f0f0f0;
            }
            
            .new-section-title {
                color: #1a1a1a;
                font-size: 16px;
                font-weight: 600;
                margin: 0 0 20px 0;
            }
            
            .new-source-group {
                margin-bottom: 24px;
            }
            
            .new-source-title {
                color: #666;
                font-size: 13px;
                font-weight: 500;
                margin: 0 0 12px 0;
                padding-bottom: 6px;
                border-bottom: 1px solid #f5f5f5;
            }
            
            .new-item {
                display: flex;
                align-items: center;
                gap: 12px;
                padding: 8px 0;
                border-bottom: 1px solid #f9f9f9;
            }
            
            .new-item:last-child {
                border-bottom: none;
            }
            
            .new-item-number {
                color: #999;
                font-size: 12px;
                font-weight: 600;
                min-width: 18px;
                text-align: center;
                flex-shrink: 0;
                background: #f8f9fa;
                border-radius: 50%;
                width: 20px;
                height: 20px;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .new-item-rank {
                color: #fff;
                background: #6b7280;
                font-size: 10px;
                font-weight: 700;
                padding: 3px 6px;
                border-radius: 8px;
                min-width: 20px;
                text-align: center;
                flex-shrink: 0;
            }
            
            .new-item-rank.top { background: #dc2626; }
            .new-item-rank.high { background: #ea580c; }
            
            .new-item-content {
                flex: 1;
                min-width: 0;
            }
            
            .new-item-title {
                font-size: 14px;
                line-height: 1.4;
                color: #1a1a1a;
                margin: 0;
            }
            
            .error-section {
                background: #fef2f2;
                border: 1px solid #fecaca;
                border-radius: 8px;
                padding: 16px;
                margin-bottom: 24px;
            }
            
            .error-title {
                color: #dc2626;
                font-size: 14px;
                font-weight: 600;
                margin: 0 0 8px 0;
            }
            
            .error-list {
                list-style: none;
                padding: 0;
                margin: 0;
            }
            
            .error-item {
                color: #991b1b;
                font-size: 13px;
                padding: 2px 0;
                font-family: 'SF Mono', Consolas, monospace;
            }
            
            .footer {
                margin-top: 32px;
                padding: 20px 24px;
                background: #f8f9fa;
                border-top: 1px solid #e5e7eb;
                text-align: center;
            }
            
            .footer-content {
                font-size: 13px;
                color: #6b7280;
                line-height: 1.6;
            }
            
            .footer-link {
                color: #4f46e5;
                text-decoration: none;
                font-weight: 500;
                transition: color 0.2s ease;
            }
            
            .footer-link:hover {
                color: #7c3aed;
                text-decoration: underline;
            }
            
            .project-name {
                font-weight: 600;
                color: #374151;
            }
            
            @media (max-width: 480px) {
                body { padding: 12px; }
                .header { padding: 24px 20px; }
                .content { padding: 20px; }
                .footer { padding: 16px 20px; }
                .header-info { grid-template-columns: 1fr; gap: 12px; }
                .news-header { gap: 6px; }
                .news-content { padding-right: 45px; }
                .news-item { gap: 8px; }
                .new-item { gap: 8px; }
                .news-number { width: 20px; height: 20px; font-size: 12px; }
                .save-buttons {
                    position: static;
                    margin-bottom: 16px;
                    display: flex;
                    gap: 8px;
                    justify-content: center;
                    flex-direction: column;
                    width: 100%;
                }
                .save-btn {
                    width: 100%;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="save-buttons">
                    <button class="save-btn" onclick="saveAsImage()">保存vìhình ảnh</button>
                    <button class="save-btn" onclick="saveAsMultipleImages()">phút段保存</button>
                </div>
                <div class="header-title">Tin tức nóngphút析</div>
                <div class="header-info">
                    <div class="info-item">
                        <span class="info-label">Loại báo cáo</span>
                        <span class="info-value">"""

        # Xử lý hiển thị loại báo cáo
        if is_daily_summary:
            if mode == "current":
                html += "bảng xếp hạng hiện tại"
            elif mode == "incremental":
                html += "Chế độ tăng dần"
            else:
                html += "当ngàytổng hợp"
        else:
            html += "实giờphút析"

        html += """</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Tổng số tin tức</span>
                        <span class="info-value">"""

        html += f"{total_titles} tin"

        # Tính số lượng tin tức nóng sau khi lọc
        hot_news_count = sum(len(stat["titles"]) for stat in report_data["stats"])

        html += """</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Tin tức nóng</span>
                        <span class="info-value">"""

        html += f"{hot_news_count} tin"

        html += """</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">tạogiờ间</span>
                        <span class="info-value">"""

        now = get_beijing_time()
        html += now.strftime("%m-%d %H:%M")

        html += """</span>
                    </div>
                </div>
            </div>
            
            <div class="content">"""

        # Xử lý thông tin lỗi ID thất bại
        if report_data["failed_ids"]:
            html += """
                <div class="error-section">
                    <div class="error-title">⚠️ 请求失败của平台</div>
                    <ul class="error-list">"""
            for id_value in report_data["failed_ids"]:
                html += f'<li class="error-item">{html_escape(id_value)}</li>'
            html += """
                    </ul>
                </div>"""

        # Xử lý dữ liệu thống kê chính
        if report_data["stats"]:
            total_count = len(report_data["stats"])

            for i, stat in enumerate(report_data["stats"], 1):
                count = stat["count"]

                # Xác định cấp độ nóng
                if count >= 10:
                    count_class = "hot"
                elif count >= 5:
                    count_class = "warm"
                else:
                    count_class = ""

                escaped_word = html_escape(stat["word"])

                html += f"""
                <div class="word-group">
                    <div class="word-header">
                        <div class="word-info">
                            <div class="word-name">{escaped_word}</div>
                            <div class="word-count {count_class}">{count} tin</div>
                        </div>
                        <div class="word-index">{i}/{total_count}</div>
                    </div>"""

                # Xử lý tiêu đề tin tức dưới mỗi nhóm từ，đánh số thứ tự cho mỗi tin tức
                for j, title_data in enumerate(stat["titles"], 1):
                    is_new = title_data.get("is_new", False)
                    new_class = "new" if is_new else ""

                    html += f"""
                    <div class="news-item {new_class}">
                        <div class="news-number">{j}</div>
                        <div class="news-content">
                            <div class="news-header">
                                <span class="source-name">{html_escape(title_data["source_name"])}</span>"""

                    # Xử lý hiển thị thứ hạng
                    ranks = title_data.get("ranks", [])
                    if ranks:
                        min_rank = min(ranks)
                        max_rank = max(ranks)
                        rank_threshold = title_data.get("rank_threshold", 10)

                        # Xác định cấp độ thứ hạng
                        if min_rank <= 3:
                            rank_class = "top"
                        elif min_rank <= rank_threshold:
                            rank_class = "high"
                        else:
                            rank_class = ""

                        if min_rank == max_rank:
                            rank_text = str(min_rank)
                        else:
                            rank_text = f"{min_rank}-{max_rank}"

                        html += f'<span class="rank-num {rank_class}">{rank_text}</span>'

                    # Xử lý hiển thị thời gian
                    time_display = title_data.get("time_display", "")
                    if time_display:
                        # Đơn giản hóa định dạng hiển thị thời gian，thay thế dấu sóng bằng~
                        simplified_time = (
                            time_display.replace(" ~ ", "~")
                            .replace("[", "")
                            .replace("]", "")
                        )
                        html += (
                            f'<span class="time-info">{html_escape(simplified_time)}</span>'
                        )

                    # Xử lýSố lần xuất hiện
                    count_info = title_data.get("count", 1)
                    if count_info > 1:
                        html += f'<span class="count-info">{count_info}lần</span>'

                    html += """
                            </div>
                            <div class="news-title">"""

                    # Xử lý tiêu đề và liên kết
                    escaped_title = html_escape(title_data["title"])
                    link_url = title_data.get("mobile_url") or title_data.get("url", "")

                    if link_url:
                        escaped_url = html_escape(link_url)
                        html += f'<a href="{escaped_url}" target="_blank" class="news-link">{escaped_title}</a>'
                    else:
                        html += escaped_title

                    html += """
                            </div>
                        </div>
                    </div>"""

                html += """
                </div>"""

        # Xử lý khu vực tin tức mới
        if report_data["new_titles"]:
            html += f"""
                <div class="new-section">
                    <div class="new-section-title">Xu hướng nóng mới lần này (tổng {report_data['total_new_count']} tin)</div>"""

            for source_data in report_data["new_titles"]:
                escaped_source = html_escape(source_data["source_name"])
                titles_count = len(source_data["titles"])

                html += f"""
                    <div class="new-source-group">
                        <div class="new-source-title">{escaped_source} · {titles_count}tin</div>"""

                # Cũng thêm số thứ tự cho tin tức mới
                for idx, title_data in enumerate(source_data["titles"], 1):
                    ranks = title_data.get("ranks", [])

                    # Xử lý hiển thị thứ hạng tin tức mới
                    rank_class = ""
                    if ranks:
                        min_rank = min(ranks)
                        if min_rank <= 3:
                            rank_class = "top"
                        elif min_rank <= title_data.get("rank_threshold", 10):
                            rank_class = "high"

                        if len(ranks) == 1:
                            rank_text = str(ranks[0])
                        else:
                            rank_text = f"{min(ranks)}-{max(ranks)}"
                    else:
                        rank_text = "?"

                    html += f"""
                        <div class="new-item">
                            <div class="new-item-number">{idx}</div>
                            <div class="new-item-rank {rank_class}">{rank_text}</div>
                            <div class="new-item-content">
                                <div class="new-item-title">"""

                    # Xử lý liên kết tin tức mới
                    escaped_title = html_escape(title_data["title"])
                    link_url = title_data.get("mobile_url") or title_data.get("url", "")

                    if link_url:
                        escaped_url = html_escape(link_url)
                        html += f'<a href="{escaped_url}" target="_blank" class="news-link">{escaped_title}</a>'
                    else:
                        html += escaped_title

                    html += """
                                </div>
                            </div>
                        </div>"""

                html += """
                    </div>"""

            html += """
                </div>"""

        html += """
            </div>
            
            <div class="footer">
                <div class="footer-content">
                    do <span class="project-name">TrendRadar</span> tạo · 
                    <a href="https://github.com/sansan0/TrendRadar" target="_blank" class="footer-link">
                        GitHub dự án mã nguồn mở
                    </a>"""

        if update_info:
            html += f"""
                    <br>
                    <span style="color: #ea580c; font-weight: 500;">
                        Phát hiện phiên bản mới {update_info['remote_version']}，phiên bản hiện tại {update_info['current_version']}
                    </span>"""

        html += """
                </div>
            </div>
        </div>
        
        <script>
            async function saveAsImage() {
                const button = event.target;
                const originalText = button.textContent;
                
                try {
                    button.textContent = 'tạotrong...';
                    button.disabled = true;
                    window.scrollTo(0, 0);
                    
                    // v.v.待trang ổn định
                    await new Promise(resolve => setTimeout(resolve, 200));
                    
                    // trước khi chụp màn hìnhẩnnút
                    const buttons = document.querySelector('.save-buttons');
                    buttons.style.visibility = 'hidden';
                    
                    // lạilầnv.v.待đảm bảonúthoàn toànẩn
                    await new Promise(resolve => setTimeout(resolve, 100));
                    
                    const container = document.querySelector('.container');
                    
                    const canvas = await html2canvas(container, {
                        backgroundColor: '#ffffff',
                        scale: 1.5,
                        useCORS: true,
                        allowTaint: false,
                        imageTimeout: 10000,
                        removeContainer: false,
                        foreignObjectRendering: false,
                        logging: false,
                        width: container.offsetWidth,
                        height: container.offsetHeight,
                        x: 0,
                        y: 0,
                        scrollX: 0,
                        scrollY: 0,
                        windowWidth: window.innerWidth,
                        windowHeight: window.innerHeight
                    });
                    
                    buttons.style.visibility = 'visible';
                    
                    const link = document.createElement('a');
                    const now = new Date();
                    const filename = `TrendRadar_Tin tức nóngphút析_${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}_${String(now.getHours()).padStart(2, '0')}${String(now.getMinutes()).padStart(2, '0')}.png`;
                    
                    link.download = filename;
                    link.href = canvas.toDataURL('image/png', 1.0);
                    
                    // Kích hoạt tải xuống
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                    
                    button.textContent = 'Lưu thành công!';
                    setTimeout(() => {
                        button.textContent = originalText;
                        button.disabled = false;
                    }, 2000);
                    
                } catch (error) {
                    const buttons = document.querySelector('.save-buttons');
                    buttons.style.visibility = 'visible';
                    button.textContent = 'Lưu thất bại';
                    setTimeout(() => {
                        button.textContent = originalText;
                        button.disabled = false;
                    }, 2000);
                }
            }
            
            async function saveAsMultipleImages() {
                const button = event.target;
                const originalText = button.textContent;
                const container = document.querySelector('.container');
                const scale = 1.5; 
                const maxHeight = 5000 / scale;
                
                try {
                    button.textContent = 'phút析trong...';
                    button.disabled = true;
                    
                    // 获取所cócó thể能củaphút割元素
                    const newsItems = Array.from(container.querySelectorAll('.news-item'));
                    const wordGroups = Array.from(container.querySelectorAll('.word-group'));
                    const newSection = container.querySelector('.new-section');
                    const errorSection = container.querySelector('.error-section');
                    const header = container.querySelector('.header');
                    const footer = container.querySelector('.footer');
                    
                    // 计算元素位置và高度
                    const containerRect = container.getBoundingClientRect();
                    const elements = [];
                    
                    // thêmheader作vì必须包含của元素
                    elements.push({
                        type: 'header',
                        element: header,
                        top: 0,
                        bottom: header.offsetHeight,
                        height: header.offsetHeight
                    });
                    
                    // thêmthông tin lỗi（nếu存ở）
                    if (errorSection) {
                        const rect = errorSection.getBoundingClientRect();
                        elements.push({
                            type: 'error',
                            element: errorSection,
                            top: rect.top - containerRect.top,
                            bottom: rect.bottom - containerRect.top,
                            height: rect.height
                        });
                    }
                    
                    // theoword-groupphút组处理news-item
                    wordGroups.forEach(group => {
                        const groupRect = group.getBoundingClientRect();
                        const groupNewsItems = group.querySelectorAll('.news-item');
                        
                        // thêmword-groupcủaheader部phút
                        const wordHeader = group.querySelector('.word-header');
                        if (wordHeader) {
                            const headerRect = wordHeader.getBoundingClientRect();
                            elements.push({
                                type: 'word-header',
                                element: wordHeader,
                                parent: group,
                                top: groupRect.top - containerRect.top,
                                bottom: headerRect.bottom - containerRect.top,
                                height: headerRect.height
                            });
                        }
                        
                        // thêmmỗinews-item
                        groupNewsItems.forEach(item => {
                            const rect = item.getBoundingClientRect();
                            elements.push({
                                type: 'news-item',
                                element: item,
                                parent: group,
                                top: rect.top - containerRect.top,
                                bottom: rect.bottom - containerRect.top,
                                height: rect.height
                            });
                        });
                    });
                    
                    // thêmmớitin tức部phút
                    if (newSection) {
                        const rect = newSection.getBoundingClientRect();
                        elements.push({
                            type: 'new-section',
                            element: newSection,
                            top: rect.top - containerRect.top,
                            bottom: rect.bottom - containerRect.top,
                            height: rect.height
                        });
                    }
                    
                    // thêmfooter
                    const footerRect = footer.getBoundingClientRect();
                    elements.push({
                        type: 'footer',
                        element: footer,
                        top: footerRect.top - containerRect.top,
                        bottom: footerRect.bottom - containerRect.top,
                        height: footer.offsetHeight
                    });
                    
                    // 计算phút割点
                    const segments = [];
                    let currentSegment = { start: 0, end: 0, height: 0, includeHeader: true };
                    let headerHeight = header.offsetHeight;
                    currentSegment.height = headerHeight;
                    
                    for (let i = 1; i < elements.length; i++) {
                        const element = elements[i];
                        const potentialHeight = element.bottom - currentSegment.start;
                        
                        // 检查là否需muốntạo新phút段
                        if (potentialHeight > maxHeight && currentSegment.height > headerHeight) {
                            // ở前một元素结束处phút割
                            currentSegment.end = elements[i - 1].bottom;
                            segments.push(currentSegment);
                            
                            // 开始新phút段
                            currentSegment = {
                                start: currentSegment.end,
                                end: 0,
                                height: element.bottom - currentSegment.end,
                                includeHeader: false
                            };
                        } else {
                            currentSegment.height = potentialHeight;
                            currentSegment.end = element.bottom;
                        }
                    }
                    
                    // thêmnhất后mộtphút段
                    if (currentSegment.height > 0) {
                        currentSegment.end = container.offsetHeight;
                        segments.push(currentSegment);
                    }


                    
                    button.textContent = `tạotrong (0/${segments.length})...`;
                    
                    // Ẩn nút lưu
                    const buttons = document.querySelector('.save-buttons');
                    buttons.style.visibility = 'hidden';
                    
                    // vìmỗiphút段tạohình ảnh
                    const images = [];
                    for (let i = 0; i < segments.length; i++) {
                        const segment = segments[i];
                        button.textContent = `tạotrong (${i + 1}/${segments.length})...`;
                        
                        // tạo临giờ容器用ở截图
                        const tempContainer = document.createElement('div');
                        tempContainer.style.cssText = `
                            position: absolute;
                            left: -9999px;
                            top: 0;
                            width: ${container.offsetWidth}px;
                            background: white;
                        `;
                        tempContainer.className = 'container';
                        
                        // Sao chép nội dung container
                        const clonedContainer = container.cloneNode(true);
                        
                        // 移除克隆nội dungtrongcủa保存nút
                        const clonedButtons = clonedContainer.querySelector('.save-buttons');
                        if (clonedButtons) {
                            clonedButtons.style.display = 'none';
                        }
                        
                        tempContainer.appendChild(clonedContainer);
                        document.body.appendChild(tempContainer);
                        
                        // v.v.待DOMhơn新
                        await new Promise(resolve => setTimeout(resolve, 100));
                        
                        // Sử dụnghtml2canvaschụp khu vực cụ thể
                        const canvas = await html2canvas(clonedContainer, {
                            backgroundColor: '#ffffff',
                            scale: scale,
                            useCORS: true,
                            allowTaint: false,
                            imageTimeout: 10000,
                            logging: false,
                            width: container.offsetWidth,
                            height: segment.end - segment.start,
                            x: 0,
                            y: segment.start,
                            windowWidth: window.innerWidth,
                            windowHeight: window.innerHeight
                        });
                        
                        images.push(canvas.toDataURL('image/png', 1.0));
                        
                        // 清理临giờ容器
                        document.body.removeChild(tempContainer);
                    }
                    
                    // Khôi phục hiển thị nút
                    buttons.style.visibility = 'visible';
                    
                    // dưới载所cóhình ảnh
                    const now = new Date();
                    const baseFilename = `TrendRadar_Tin tức nóngphút析_${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}_${String(now.getHours()).padStart(2, '0')}${String(now.getMinutes()).padStart(2, '0')}`;
                    
                    for (let i = 0; i < images.length; i++) {
                        const link = document.createElement('a');
                        link.download = `${baseFilename}_part${i + 1}.png`;
                        link.href = images[i];
                        document.body.appendChild(link);
                        link.click();
                        document.body.removeChild(link);
                        
                        // 延迟mộtdướitránh浏览器阻止多个dưới载
                        await new Promise(resolve => setTimeout(resolve, 100));
                    }
                    
                    button.textContent = `đã保存 ${segments.length} hình ảnh!`;
                    setTimeout(() => {
                        button.textContent = originalText;
                        button.disabled = false;
                    }, 2000);
                    
                } catch (error) {
                    console.error('phút段Lưu thất bại:', error);
                    const buttons = document.querySelector('.save-buttons');
                    buttons.style.visibility = 'visible';
                    button.textContent = 'Lưu thất bại';
                    setTimeout(() => {
                        button.textContent = originalText;
                        button.disabled = false;
                    }, 2000);
                }
            }
            
            document.addEventListener('DOMContentLoaded', function() {
                window.scrollTo(0, 0);
            });
        </script>
    </body>
    </html>
    """

        return html
