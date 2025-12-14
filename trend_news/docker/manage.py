#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Công cụ quản lý container crawler tin tức - supercronic
"""

import os
import sys
import subprocess
import time
from pathlib import Path


def run_command(cmd, shell=True, capture_output=True):
    """Thực thi lệnh hệ thống"""
    try:
        result = subprocess.run(
            cmd, shell=shell, capture_output=capture_output, text=True
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)


def manual_run():
    """Thực thi crawler thủ công một lần"""
    print("🔄 Thực thi crawler thủ công...")
    try:
        result = subprocess.run(
            ["python", "main.py"], cwd="/app", capture_output=False, text=True
        )
        if result.returncode == 0:
            print("✅ Thực thi hoàn thành")
        else:
            print(f"❌ 执行thất bại，退出码: {result.returncode}")
    except Exception as e:
        print(f"❌ 执行出错: {e}")


def parse_cron_schedule(cron_expr):
    """解析cron表达式并返回người类có thể读của描述"""
    if not cron_expr or cron_expr == "未设置":
        return "未设置"
    
    try:
        parts = cron_expr.strip().split()
        if len(parts) != 5:
            return f"原始表达式: {cron_expr}"
        
        minute, hour, day, month, weekday = parts
        
        # phân tíchphút钟
        if minute == "*":
            minute_desc = "每phút钟"
        elif minute.startswith("*/"):
            interval = minute[2:]
            minute_desc = f"每{interval}phút钟"
        elif "," in minute:
            minute_desc = f"ở第{minute}phút钟"
        else:
            minute_desc = f"ở第{minute}phút钟"
        
        # phân tích小giờ
        if hour == "*":
            hour_desc = "每小giờ"
        elif hour.startswith("*/"):
            interval = hour[2:]
            hour_desc = f"每{interval}小giờ"
        elif "," in hour:
            hour_desc = f"ở{hour}点"
        else:
            hour_desc = f"ở{hour}点"
        
        # phân tíchngày
        if day == "*":
            day_desc = "每天"
        elif day.startswith("*/"):
            interval = day[2:]
            day_desc = f"每{interval}天"
        else:
            day_desc = f"每tháng{day}号"
        
        # phân tíchtháng份
        if month == "*":
            month_desc = "每tháng"
        else:
            month_desc = f"ở{month}tháng"
        
        # phân tích星期
        weekday_names = {
            "0": "周ngày", "1": "周một", "2": "周hai", "3": "周ba", 
            "4": "周bốn", "5": "周năm", "6": "周sáu", "7": "周ngày"
        }
        if weekday == "*":
            weekday_desc = ""
        else:
            weekday_desc = f"ở{weekday_names.get(weekday, weekday)}"
        
        # 组合描述
        if minute.startswith("*/") and hour == "*" and day == "*" and month == "*" and weekday == "*":
            # 简单của间隔Chế độ，如 */30 * * * *
            return f"每{minute[2:]}phút钟执行mộtlần"
        elif hour != "*" and minute != "*" and day == "*" and month == "*" and weekday == "*":
            # 每天特定thời gian，如 0 9 * * *
            return f"每天{hour}:{minute.zfill(2)}执行"
        elif weekday != "*" and day == "*":
            # 每周特定thời gian
            return f"{weekday_desc}{hour}:{minute.zfill(2)}执行"
        else:
            # 复杂Chế độ，显示详细thông tin
            desc_parts = [part for part in [month_desc, day_desc, weekday_desc, hour_desc, minute_desc] if part and part != "每tháng" and part != "每天" and part != "每小giờ"]
            if desc_parts:
                return " ".join(desc_parts) + "执行"
            else:
                return f"复杂表达式: {cron_expr}"
    
    except Exception as e:
        return f"解析失败: {cron_expr}"


def show_status():
    """显示容器状态"""
    print("📊 容器状态:")

    # 检查 PID 1 状态
    supercronic_is_pid1 = False
    pid1_cmdline = ""
    try:
        with open('/proc/1/cmdline', 'r') as f:
            pid1_cmdline = f.read().replace('\x00', ' ').strip()
        print(f"  🔍 PID 1 进程: {pid1_cmdline}")
        
        if "supercronic" in pid1_cmdline.lower():
            print("  ✅ supercronic 正确运行vì PID 1")
            supercronic_is_pid1 = True
        else:
            print("  ❌ PID 1 khônglà supercronic")
            print(f"  📋 实际của PID 1: {pid1_cmdline}")
    except Exception as e:
        print(f"  ❌ 无法đọc PID 1 thông tin: {e}")

    # 检查môi trườngbiến
    cron_schedule = os.environ.get("CRON_SCHEDULE", "未设置")
    run_mode = os.environ.get("RUN_MODE", "未设置")
    immediate_run = os.environ.get("IMMEDIATE_RUN", "未设置")
    
    print(f"  ⚙️ 运行cấu hình:")
    print(f"    CRON_SCHEDULE: {cron_schedule}")
    
    # Phân tích并显示cron表达式của含义
    cron_description = parse_cron_schedule(cron_schedule)
    print(f"    ⏰ 执行频率: {cron_description}")
    
    print(f"    RUN_MODE: {run_mode}")
    print(f"    IMMEDIATE_RUN: {immediate_run}")

    # 检查File cấu hình
    config_files = ["/app/config/config.yaml", "/app/config/frequency_words.txt"]
    print("  📁 File cấu hình:")
    for file_path in config_files:
        if Path(file_path).exists():
            print(f"    ✅ {Path(file_path).name}")
        else:
            print(f"    ❌ {Path(file_path).name} 缺失")

    # 检查关键file
    key_files = [
        ("/usr/local/bin/supercronic-linux-amd64", "supercronichai进制file"),
        ("/usr/local/bin/supercronic", "supercronic软链接"),
        ("/tmp/crontab", "crontabfile"),
        ("/entrypoint.sh", "启动脚本")
    ]
    
    print("  📂 关键file检查:")
    for file_path, description in key_files:
        if Path(file_path).exists():
            print(f"    ✅ {description}: 存ở")
            # Đối vớicrontabfile，显示nội dung
            if file_path == "/tmp/crontab":
                try:
                    with open(file_path, 'r') as f:
                        crontab_content = f.read().strip()
                        print(f"         nội dung: {crontab_content}")
                except:
                    pass
        else:
            print(f"    ❌ {description}: không tồn tại")

    # 检查容器运行thời gian
    print("  ⏱️ 容器thời gianthông tin:")
    try:
        # 检查 PID 1 củakhởi độngthời gian
        with open('/proc/1/stat', 'r') as f:
            stat_content = f.read().strip().split()
            if len(stat_content) >= 22:
                # starttime là第22个字段（索引21）
                starttime_ticks = int(stat_content[21])
                
                # đọc系统khởi độngthời gian
                with open('/proc/stat', 'r') as stat_f:
                    for line in stat_f:
                        if line.startswith('btime'):
                            boot_time = int(line.split()[1])
                            break
                    else:
                        boot_time = 0
                
                # đọc系统giờ钟频率
                clock_ticks = os.sysconf(os.sysconf_names['SC_CLK_TCK'])
                
                if boot_time > 0:
                    pid1_start_time = boot_time + (starttime_ticks / clock_ticks)
                    current_time = time.time()
                    uptime_seconds = int(current_time - pid1_start_time)
                    uptime_minutes = uptime_seconds // 60
                    uptime_hours = uptime_minutes // 60
                    
                    if uptime_hours > 0:
                        print(f"    PID 1 运行thời gian: {uptime_hours} 小giờ {uptime_minutes % 60} phút钟")
                    else:
                        print(f"    PID 1 运行thời gian: {uptime_minutes} phút钟 ({uptime_seconds} 秒)")
                else:
                    print(f"    PID 1 运行thời gian: 无法精确tính toán")
            else:
                print("    ❌ 无法Phân tích PID 1 thống kêthông tin")
    except Exception as e:
        print(f"    ❌ thời gian检查thất bại: {e}")

    # 状态总结và建议
    print("  📊 状态总结:")
    if supercronic_is_pid1:
        print("    ✅ supercronic 正确运行vì PID 1")
        print("    ✅ 定giờ任务应该正常工作")
        
        # 显示hiện tạicủa调度thông tin
        if cron_schedule != "未设置":
            print(f"    ⏰ hiện tại调度: {cron_description}")
            
            # 提供một些常见của调度建议
            if "phút钟" in cron_description and "每30phút钟" not in cron_description and "每60phút钟" not in cron_description:
                print("    💡 频繁执行Chế độ，适合实giờ监控")
            elif "小giờ" in cron_description:
                print("    💡 theo小giờ执行Chế độ，适合定期tổng hợp")
            elif "天" in cron_description:
                print("    💡 每ngày执行Chế độ，适合ngày报tạo")
        
        print("    💡 nếu定giờ任务không执行，检查:")
        print("       • crontab định dạnglà否正确")
        print("       • giờ区thiết lậplà否正确")
        print("       • 应用程序là否cólỗi")
    else:
        print("    ❌ supercronic 状态ngoại lệ")
        if pid1_cmdline:
            print(f"    📋 hiện tại PID 1: {pid1_cmdline}")
        print("    💡 建议操作:")
        print("       • 重启容器: docker restart trend-radar")
        print("       • 检查容器nhật ký: docker logs trend-radar")

    # 显示nhật ký检查建议
    print("  📋 运行状态检查:")
    print("    • 查xem完整容器nhật ký: docker logs trend-radar")
    print("    • 查xem实giờnhật ký: docker logs -f trend-radar")
    print("    • 手动执行测试: python manage.py run")
    print("    • 重启容器服务: docker restart trend-radar")


def show_config():
    """显示当前配置"""
    print("⚙️ hiện tạicấu hình:")

    env_vars = [
        "CRON_SCHEDULE",
        "RUN_MODE",
        "IMMEDIATE_RUN",
        "FEISHU_WEBHOOK_URL",
        "DINGTALK_WEBHOOK_URL",
        "WEWORK_WEBHOOK_URL",
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
        "CONFIG_PATH",
        "FREQUENCY_WORDS_PATH",
    ]

    for var in env_vars:
        value = os.environ.get(var, "未设置")
        # ẩn敏感thông tin
        if any(sensitive in var for sensitive in ["WEBHOOK", "TOKEN", "KEY"]):
            if value and value != "未设置":
                masked_value = value[:10] + "***" if len(value) > 10 else "***"
                print(f"  {var}: {masked_value}")
            else:
                print(f"  {var}: {value}")
        else:
            print(f"  {var}: {value}")

    crontab_file = "/tmp/crontab"
    if Path(crontab_file).exists():
        print("  📅 Crontabnội dung:")
        try:
            with open(crontab_file, "r") as f:
                content = f.read().strip()
                print(f"    {content}")
        except Exception as e:
            print(f"    đọcthất bại: {e}")
    else:
        print("  📅 Crontabfilekhông tồn tại")


def show_files():
    """显示输出file"""
    print("📁 输出file:")

    output_dir = Path("/app/output")
    if not output_dir.exists():
        print("  📭 输出thư mụckhông tồn tại")
        return

    # 显示nhất近củafile
    date_dirs = sorted([d for d in output_dir.iterdir() if d.is_dir()], reverse=True)

    if not date_dirs:
        print("  📭 输出thư mụcvì空")
        return

    # 显示nhất近2天củafile
    for date_dir in date_dirs[:2]:
        print(f"  📅 {date_dir.name}:")
        for subdir in ["html", "txt"]:
            sub_path = date_dir / subdir
            if sub_path.exists():
                files = list(sub_path.glob("*"))
                if files:
                    recent_files = sorted(
                        files, key=lambda x: x.stat().st_mtime, reverse=True
                    )[:3]
                    print(f"    📂 {subdir}: {len(files)} 个file")
                    for file in recent_files:
                        mtime = time.ctime(file.stat().st_mtime)
                        size_kb = file.stat().st_size // 1024
                        print(
                            f"      📄 {file.name} ({size_kb}KB, {mtime.split()[3][:5]})"
                        )
                else:
                    print(f"    📂 {subdir}: 空")


def show_logs():
    """显示实giờngày志"""
    print("📋 实giờnhật ký (theo Ctrl+C 退出):")
    print("💡 提示: nàysẽ显示 PID 1 进程của输出")
    try:
        # 尝试多种phương thức查xemnhật ký
        log_files = [
            "/proc/1/fd/1",  # PID 1 của标准输出
            "/proc/1/fd/2",  # PID 1 của标准lỗi
        ]
        
        for log_file in log_files:
            if Path(log_file).exists():
                print(f"📄 尝试đọc: {log_file}")
                subprocess.run(["tail", "-f", log_file], check=True)
                break
        else:
            print("📋 无法找đến标准nhật kýfile，建议Sử dụng: docker logs trend-radar")
            
    except KeyboardInterrupt:
        print("\n👋 退出nhật ký查xem")
    except Exception as e:
        print(f"❌ 查xemnhật kýthất bại: {e}")
        print("💡 建议Sử dụng: docker logs trend-radar")


def restart_supercronic():
    """重启supercronic进程"""
    print("🔄 重启supercronic...")
    print("⚠️ 注意: supercronic là PID 1，无法直接重启")
    
    # 检查hiện tại PID 1
    try:
        with open('/proc/1/cmdline', 'r') as f:
            pid1_cmdline = f.read().replace('\x00', ' ').strip()
        print(f"  🔍 hiện tại PID 1: {pid1_cmdline}")
        
        if "supercronic" in pid1_cmdline.lower():
            print("  ✅ PID 1 là supercronic")
            print("  💡 muốn重启 supercronic，需muốn重启整个容器:")
            print("    docker restart trend-radar")
        else:
            print("  ❌ PID 1 khônglà supercronic，nàylàngoại lệ状态")
            print("  💡 建议重启容器để修复问题:")
            print("    docker restart trend-radar")
    except Exception as e:
        print(f"  ❌ 无法检查 PID 1: {e}")
        print("  💡 建议重启容器: docker restart trend-radar")


def show_help():
    """显示帮助信息"""
    help_text = """
🐳 TrendRadar 容器管理工具

📋 命令列表:
  run         - Thực thi crawler thủ công một lần
  status      - 显示容器运行状态
  config      - 显示当前配置
  files       - 显示输出file
  logs        - 实giờ查xemngày志
  restart     - 重启nói明
  help        - 显示此帮助

📖 Sử dụng示例:
  # ở容器trong执行
  python manage.py run
  python manage.py status
  python manage.py logs
  
  # ở宿主机执行
  docker exec -it trend-radar python manage.py run
  docker exec -it trend-radar python manage.py status
  docker logs trend-radar

💡 常用操作指南:
  1. 检查运行状态: status
     - 查xem supercronic là否vì PID 1
     - 检查File cấu hìnhvà关键file
     - 查xem cron 调度设置
  
  2. 手动执行测试: run  
     - 立即执行mộtlầntin tứcthu thập
     - 测试程序là否正常工作
  
  3. 查xemngày志: logs
     - 实giờ监控运行情况
     - cũngcó thểSử dụng: docker logs trend-radar
  
  4. 重启服务: restart
     - doở supercronic là PID 1，需muốn重启整个容器
     - Sử dụng: docker restart trend-radar
"""
    print(help_text)


def main():
    if len(sys.argv) < 2:
        show_help()
        return

    command = sys.argv[1]
    commands = {
        "run": manual_run,
        "status": show_status,
        "config": show_config,
        "files": show_files,
        "logs": show_logs,
        "restart": restart_supercronic,
        "help": show_help,
    }

    if command in commands:
        try:
            commands[command]()
        except KeyboardInterrupt:
            print("\n👋 操作đãhủy")
        except Exception as e:
            print(f"❌ 执行出错: {e}")
    else:
        print(f"❌ 未知命令: {command}")
        print("运行 'python manage.py help' 查xemcó thể用命令")


if __name__ == "__main__":
    main()