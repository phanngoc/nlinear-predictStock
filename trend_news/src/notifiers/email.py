import smtplib
from typing import Optional
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr, formatdate, make_msgid
from email.header import Header
from src.config import SMTP_CONFIGS
from src.utils import get_beijing_time


def send_to_email(
    from_email: str,
    password: str,
    to_email: str,
    report_type: str,
    html_file_path: str,
    custom_smtp_server: Optional[str] = None,
    custom_smtp_port: Optional[int] = None,
) -> bool:
    """Gửi thông báo email"""
    try:
        if not html_file_path or not Path(html_file_path).exists():
            print(f"lỗi：HTMLfilekhông tồn tạihoặc未提供: {html_file_path}")
            return False

        print(f"Sử dụngHTMLfile: {html_file_path}")
        with open(html_file_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        domain = from_email.split("@")[-1].lower()

        if custom_smtp_server and custom_smtp_port:
            # Sử dụngtùy chỉnh SMTP cấu hình
            smtp_server = custom_smtp_server
            smtp_port = int(custom_smtp_port)
            # Xác định phương thức mã hóa theo cổng：465=SSL, 587=TLS
            if smtp_port == 465:
                use_tls = False  # SSL chế độ（SMTP_SSL）
            elif smtp_port == 587:
                use_tls = True   # TLS chế độ（STARTTLS）
            else:
                # Cổng khác ưu tiên thử TLS（hơn安全，hơn广泛支持）
                use_tls = True
        elif domain in SMTP_CONFIGS:
            # Sử dụng预设cấu hình
            config = SMTP_CONFIGS[domain]
            smtp_server = config["server"]
            smtp_port = config["port"]
            use_tls = config["encryption"] == "TLS"
        else:
            print(f"未识别của邮箱服务商: {domain}，Sử dụng chung SMTP cấu hình")
            smtp_server = f"smtp.{domain}"
            smtp_port = 587
            use_tls = True

        msg = MIMEMultipart("alternative")

        # Tuân thủ nghiêm ngặt RFC 标准thiết lập From header
        sender_name = "TrendRadar"
        msg["From"] = formataddr((sender_name, from_email))

        # thiết lập收件người
        recipients = [addr.strip() for addr in to_email.split(",")]
        if len(recipients) == 1:
            msg["To"] = recipients[0]
        else:
            msg["To"] = ", ".join(recipients)

        # thiết lập邮件主题
        now = get_beijing_time()
        subject = f"TrendRadar xu hướng nóngphút析báo cáo - {report_type} - {now.strftime('%mtháng%dngày %H:%M')}"
        msg["Subject"] = Header(subject, "utf-8")

        # thiết lập其他标准 header
        msg["MIME-Version"] = "1.0"
        msg["Date"] = formatdate(localtime=True)
        msg["Message-ID"] = make_msgid()

        # thêm纯文本một phần（作vì备选）
        text_content = f"""
TrendRadar xu hướng nóngphút析báo cáo
========================
Loại báo cáo：{report_type}
tạogiờ间：{now.strftime('%Y-%m-%d %H:%M:%S')}

Vui lòng sử dụng hỗ trợHTMLcủa邮件客户端查xem完整báo cáonội dung。
        """
        text_part = MIMEText(text_content, "plain", "utf-8")
        msg.attach(text_part)

        html_part = MIMEText(html_content, "html", "utf-8")
        msg.attach(html_part)

        print(f"正ởGửi emailđến {to_email}...")
        print(f"SMTP máy chủ: {smtp_server}:{smtp_port}")
        print(f"发件người: {from_email}")

        try:
            if use_tls:
                # TLS Chế độ
                server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
                server.set_debuglevel(0)  # 设vì1có thể查xem详细调试信息
                server.ehlo()
                server.starttls()
                server.ehlo()
            else:
                # SSL Chế độ
                server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=30)
                server.set_debuglevel(0)
                server.ehlo()

            # đăng nhập
            server.login(from_email, password)

            # Gửi email
            server.send_message(msg)
            server.quit()

            print(f"邮件gửithành công [{report_type}] -> {to_email}")
            return True

        except smtplib.SMTPServerDisconnected:
            print(f"邮件gửithất bại：máy chủ意外ngắt kết nốikết nối，请检查网络hoặc稍后thử lại")
            return False

    except smtplib.SMTPAuthenticationError as e:
        print(f"邮件gửithất bại：认证lỗi，请检查邮箱và密码/mã ủy quyền")
        print(f"详细lỗi: {str(e)}")
        return False
    except smtplib.SMTPRecipientsRefused as e:
        print(f"邮件gửithất bại：收件người地址bị拒绝 {e}")
        return False
    except smtplib.SMTPSenderRefused as e:
        print(f"邮件gửithất bại：发件người地址bị拒绝 {e}")
        return False
    except smtplib.SMTPDataError as e:
        print(f"邮件gửithất bại：邮件dữ liệulỗi {e}")
        return False
    except smtplib.SMTPConnectError as e:
        print(f"邮件gửithất bại：无法kết nốiđến SMTP máy chủ {smtp_server}:{smtp_port}")
        print(f"详细lỗi: {str(e)}")
        return False
    except Exception as e:
        print(f"邮件gửithất bại [{report_type}]：{e}")
        import traceback

        traceback.print_exc()
        return False
