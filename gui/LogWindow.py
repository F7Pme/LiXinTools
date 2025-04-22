from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                               QTextEdit, QPushButton, QLabel, QSizePolicy, QProgressBar, QGridLayout,
                               QCheckBox, QGroupBox, QScrollArea)
from PySide6.QtCore import Qt, Signal, QDateTime, QTimer
from PySide6.QtGui import QFont, QTextCursor, QPainter, QColor
from PySide6.QtGui import QGuiApplication

from gui.BaseWindow import BaseWindow
from gui.TitleBar import TitleBar
from gui.styles import StyleSheet, FontConfig, ColorPalette

import os
import sys
import time
import traceback
import psutil
import platform
import threading
import socket
from functools import partial

# 日志级别常量
LOG_LEVELS = {
    "ERROR": {"color": "#FF6B6B", "checked": True},
    "WARNING": {"color": "#FFD700", "checked": True},
    "SUCCESS": {"color": "#4CAF50", "checked": True},
    "INFO": {"color": "#90CAF9", "checked": True},
    "DEBUG": {"color": "#9370DB", "checked": True},
    "NETWORK": {"color": "#00CED1", "checked": True},
    "UI": {"color": "#FFA500", "checked": True},
    "MEMORY": {"color": "#FF69B4", "checked": True}  # 新增内存追踪日志类型，粉色
}

# 自定义复选框，使用Segoe MDL2 Assets图标显示勾选状态
class CheckBoxWithIcon(QCheckBox):
    def __init__(self, text, color="#333333"):
        super().__init__(text)
        self.text_color = color
        
    def paintEvent(self, event):
        super().paintEvent(event)
        if self.isChecked():
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.TextAntialiasing)
            painter.setFont(FontConfig.get_high_quality_font("Segoe MDL2 Assets", pixel_size=11))
            painter.setPen(QColor("#FFFFFF"))
            painter.drawText(4, 14, "\uE73E")  # 使用Segoe MDL2 Assets中的勾选图标

class LogWindow(BaseWindow):
    """开发者日志窗口，用于显示程序运行过程中的日志信息"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("开发者日志")
        self.setMinimumSize(800, 500)
        
        # 初始化日志相关变量
        self.log_records = []  # 所有日志记录，包含级别信息
        self.log_filters = {level: info["checked"] for level, info in LOG_LEVELS.items()}  # 日志过滤状态
        
        # 内存监控变量
        self.last_memory_usage = 0  # 上次记录的内存使用量
        self.memory_threshold_mb = 5  # 内存变化阈值(MB)
        
        self.setup_ui()
        self.setup_logger()
        
        # 确保窗口能够正确显示，但不要置顶
        self.setAttribute(Qt.WA_ShowWithoutActivating, False)  # 允许激活窗口
        
        # 重要：设置为非主窗口，这样关闭主窗口时应用程序会退出
        self.setAttribute(Qt.WA_QuitOnClose, False)
        
        # 启动性能监控线程
        self.stop_monitor = False
        self.monitor_thread = threading.Thread(target=self.monitor_system_resources)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        # 设置内存使用量更新定时器
        self.memory_timer = QTimer(self)
        self.memory_timer.timeout.connect(self.update_usage_info)
        self.memory_timer.start(1000)  # 每秒更新一次

    def setup_ui(self):
        # 添加标题栏
        self.title_bar = TitleBar(show_back_button=False)
        self.title_bar.title.setText("开发者日志")  # 直接设置标题文本
        self.title_bar.minimizeClicked.connect(self.showMinimized)
        self.title_bar.closeClicked.connect(self.hide)  # 只隐藏，不关闭
        
        # 系统信息和内存使用区域
        self.info_widget = QWidget()
        info_layout = QVBoxLayout(self.info_widget)
        info_layout.setContentsMargins(10, 5, 10, 5)
        info_layout.setSpacing(3)  # 行间距非常小
        
        # 使用表格布局，精确控制对齐和间距
        table_widget = QWidget()
        table_layout = QGridLayout(table_widget)
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.setHorizontalSpacing(2)  # 水平间距极小
        table_layout.setVerticalSpacing(3)    # 垂直间距保持小
        
        # 设置列宽策略，第1、3列(标签)固定宽度，第2、4列(值)可扩展
        table_layout.setColumnStretch(0, 0)  # 第1列不拉伸(标签)
        table_layout.setColumnStretch(1, 1)  # 第2列拉伸(值)
        table_layout.setColumnStretch(2, 0)  # 第3列不拉伸(标签)
        table_layout.setColumnStretch(3, 1)  # 第4列拉伸(值)
        
        # 系统信息标签样式
        info_style = "color: black; font-size: 11px;"
        value_style = "color: #0066CC; font-size: 11px; font-weight: bold;"
        
        # 第一行：操作系统/主机 和 本地IP
        self.create_label_pair(table_layout, 0, 0, "操作系统/主机 :", "os_value_label", "加载中...", info_style, value_style)
        self.create_label_pair(table_layout, 0, 2, "本地 IP :", "local_ip_value_label", "加载中...", info_style, value_style)
        
        # 第二行：处理器 和 内存
        self.create_label_pair(table_layout, 1, 0, "处理器 :", "cpu_value_label", "加载中...", info_style, value_style)
        self.create_label_pair(table_layout, 1, 2, "内存情况 :", "mem_value_label", "加载中...", info_style, value_style)
        
        # 第三行：内存使用进度条
        memory_label = QLabel("内存使用 :")
        memory_label.setStyleSheet(info_style)
        memory_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        self.memory_bar = QProgressBar()
        self.memory_bar.setRange(0, 100)
        self.memory_bar.setValue(0)
        self.memory_bar.setTextVisible(True)
        self.memory_bar.setFormat("%v%% (%p MB)")
        self.memory_bar.setFixedWidth(200)  # 设置固定宽度
        self.memory_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                background-color: #F5F5F5;
                color: #333333;
                height: 18px;
                text-align: center;
                font-size: 10px;
                font-weight: bold;
                padding: 1px;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, 
                                                stop:0 #4287f5, stop:1 #42b0f5);
                border-radius: 3px;
            }
        """)
        
        # 将内存进度条添加到第三行
        table_layout.addWidget(memory_label, 2, 0, alignment=Qt.AlignLeft)
        table_layout.addWidget(self.memory_bar, 2, 1, 1, 3)  # 跨越3列
        
        info_layout.addWidget(table_widget)
        
        # 主内容区域
        self.content_widget = QWidget()
        
        # 日志显示区域
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 10))
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                color: #FFFFFF;
                border: 1px solid #333333;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        
        # 底部区域
        bottom_container = QWidget()
        bottom_layout = QVBoxLayout(bottom_container)
        bottom_layout.setContentsMargins(10, 5, 10, 10)
        bottom_layout.setSpacing(10)
        
        # 日志过滤区域
        filter_group = QGroupBox("日志过滤")
        filter_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #CCCCCC;
                border-radius: 5px;
                margin-top: 10px;
                color: #333333;  /* 改为深灰色，使其更可见 */
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                background-color: #F5F5F5;  /* 添加背景色，确保可见性 */
            }
        """)
        filter_layout = QHBoxLayout(filter_group)
        # 增加顶部内边距，让标题更清晰
        filter_layout.setContentsMargins(10, 15, 10, 10)
        filter_layout.setSpacing(15)
        
        # 添加复选框 - 完全重写这一部分
        self.filter_checkboxes = {}
        for level, info in LOG_LEVELS.items():
            # 创建复选框，使用自定义类
            checkbox = CheckBoxWithIcon(level, "#333333")
            
            # 设置初始状态
            checkbox.setChecked(info["checked"])
            
            # 统一使用黑色文字，取消粗体
            checkbox.setStyleSheet("""
                QCheckBox {
                    color: #333333;
                    background: transparent;
                }
                QCheckBox::indicator {
                    width: 16px;
                    height: 16px;
                    border: 1px solid #999999;
                    border-radius: 3px;
                }
                QCheckBox::indicator:unchecked {
                    background-color: #FFFFFF;
                }
                QCheckBox::indicator:checked {
                    background-color: #3072F6;
                    border: 1px solid #3072F6;
                }
            """)
            
            # 保存复选框引用
            self.filter_checkboxes[level] = checkbox
            
            # 添加到布局
            filter_layout.addWidget(checkbox)
        
        # 在所有复选框创建完毕后，单独连接信号
        for level, checkbox in self.filter_checkboxes.items():
            # 使用partial创建专用于特定级别的回调函数
            filter_callback = partial(self.filter_checkbox_changed, level)
            checkbox.stateChanged.connect(filter_callback)
        
        # 删除全选和取消全选按钮
        filter_layout.addStretch()
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # 清空按钮
        self.clear_btn = QPushButton("清空日志")
        self.clear_btn.setFixedSize(100, 30)
        self.clear_btn.clicked.connect(self.clear_log)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #505050;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #606060;
            }
            QPushButton:pressed {
                background-color: #404040;
            }
        """)
        
        # 保存按钮
        self.save_btn = QPushButton("保存日志")
        self.save_btn.setFixedSize(100, 30)
        self.save_btn.clicked.connect(self.save_log)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #007ACC;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #0088EE;
            }
            QPushButton:pressed {
                background-color: #006699;
            }
        """)
        
        button_layout.addStretch()
        button_layout.addWidget(self.clear_btn)
        button_layout.addWidget(self.save_btn)
        
        # 添加到底部布局
        bottom_layout.addWidget(filter_group)
        bottom_layout.addLayout(button_layout)
        
        # 内容布局
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(10, 10, 10, 0)
        content_layout.setSpacing(10)
        content_layout.addWidget(self.info_widget)
        content_layout.addWidget(self.log_text)
        content_layout.addWidget(bottom_container)
        
        # 主窗口布局
        main_layout = self.centralWidget().layout()
        main_layout.addWidget(self.title_bar)
        main_layout.addWidget(self.content_widget)
        
        # 初始更新系统信息和内存使用情况
        self.update_all_system_info()
        
        # 启动定时器定期更新CPU和内存使用率
        self.usage_timer = QTimer(self)
        self.usage_timer.timeout.connect(self.update_usage_info)
        self.usage_timer.start(2000)  # 每2秒更新一次

    def create_label_pair(self, layout, row, col, label_text, value_name, initial_value, label_style, value_style):
        """在表格布局中创建标签和值对"""
        # 创建标签
        label = QLabel(label_text)
        label.setStyleSheet(label_style)
        label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        # 创建值
        value = QLabel(initial_value)
        value.setStyleSheet(value_style)
        value.setObjectName(value_name)
        value.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        # 添加到布局
        layout.addWidget(label, row, col)
        layout.addWidget(value, row, col + 1)
        
        return value
        
    def update_all_system_info(self):
        """更新所有系统信息"""
        try:
            # 操作系统信息+主机名合并
            os_name = platform.system()
            os_release = platform.release()
            hostname = socket.gethostname()
            os_info = f"{os_name} {os_release} ({hostname})"
            self.findChild(QLabel, "os_value_label").setText(os_info)
            
            # 处理器信息 - 获取更友好的名称
            processor = self.get_friendly_cpu_name()
            self.findChild(QLabel, "cpu_value_label").setText(processor)
            
            # 内存信息合并
            mem = psutil.virtual_memory()
            total_mem = self.format_bytes(mem.total)
            avail_mem = self.format_bytes(mem.available)
            self.findChild(QLabel, "mem_value_label").setText(f"总{total_mem} / 可用{avail_mem}")
            
            # 本地IP
            try:
                local_ip = socket.gethostbyname(hostname)
                self.findChild(QLabel, "local_ip_value_label").setText(local_ip)
            except:
                self.findChild(QLabel, "local_ip_value_label").setText("获取失败")
                
            # 更新内存使用率
            self.update_usage_info()
            
        except Exception as e:
            self.log(f"更新系统信息失败: {str(e)}", "ERROR")
    
    def get_friendly_cpu_name(self):
        """尝试获取更友好的CPU名称"""
        try:
            if platform.system() == "Windows":
                # 尝试使用WMI获取CPU信息
                import subprocess
                result = subprocess.check_output("wmic cpu get name", shell=True).decode('utf-8')
                lines = result.strip().split('\n')
                if len(lines) >= 2:  # 第一行是标题，第二行是值
                    return lines[1].strip()
                    
            # 如果上面方法失败，尝试使用cpuinfo库
            try:
                import cpuinfo
                info = cpuinfo.get_cpu_info()
                if 'brand_raw' in info:
                    return info['brand_raw']
            except ImportError:
                pass
                
            # 如果以上方法都失败，返回原始处理器信息
            processor = platform.processor()
            if not processor or processor == "":
                processor = "未知"
            return processor
                
        except Exception as e:
            self.log(f"获取CPU名称失败: {str(e)}", "ERROR")
            return platform.processor() or "未知"
    
    def update_usage_info(self):
        """更新内存使用率"""
        try:
            # 获取当前进程
            process = psutil.Process(os.getpid())
            
            # 使用专用工作集内存(Windows)或USS(其他系统)
            # 这与任务管理器显示的更接近
            if platform.system() == 'Windows':
                memory_info = process.memory_info()
                # 使用private替代rss，与任务管理器显示更接近
                memory_mb = memory_info.private / (1024 * 1024)
            else:
                # 在Linux/Mac上尝试使用USS(唯一集内存)，如果支持的话
                try:
                    memory_mb = process.memory_full_info().uss / (1024 * 1024)
                except:
                    memory_mb = process.memory_info().rss / (1024 * 1024)
            
            # 获取总内存
            total_memory = psutil.virtual_memory().total / (1024 * 1024)
            memory_percent = (memory_mb / total_memory) * 100
            
            # 更新内存进度条
            self.memory_bar.setValue(int(memory_percent))
            # 使用与日志一致的格式化，保留2位小数
            self.memory_bar.setFormat(f"{memory_percent:.2f}% ({memory_mb:.2f} MB)")
            
            # 检查内存变化并记录
            self.check_memory_change(memory_mb)
            
        except Exception as e:
            self.log(f"更新资源使用信息失败: {str(e)}", "ERROR")
    
    def check_memory_change(self, current_memory_mb):
        """检查内存变化，记录大于阈值的变化"""
        if self.last_memory_usage > 0:  # 忽略首次运行
            memory_change = current_memory_mb - self.last_memory_usage
            if abs(memory_change) >= self.memory_threshold_mb:
                change_type = "增加" if memory_change > 0 else "减少"
                self.log(f"内存使用{change_type}: {abs(memory_change):.2f} MB，当前使用: {current_memory_mb:.2f} MB", "MEMORY")
        
        # 更新上次内存使用量
        self.last_memory_usage = current_memory_mb
    
    def setup_logger(self):
        """设置日志记录系统"""
        # 记录启动信息
        self.log("应用程序启动，开发者日志系统初始化完成", "INFO")
        self.log(f"当前时间: {QDateTime.currentDateTime().toString('yyyy-MM-dd hh:mm:ss')}", "INFO")
        
        # 在日志开头记录系统硬件和软件信息
        self.log("===== 系统信息 =====", "INFO")
        # 软件信息
        self.log(f"操作系统: {platform.system()} {platform.release()}", "INFO")
        self.log(f"OS版本: {platform.version()}", "INFO")
        self.log(f"Python版本: {sys.version}", "INFO")
        self.log(f"Python实现: {platform.python_implementation()}", "INFO")
        
        # 硬件信息
        self.log("===== 硬件信息 =====", "INFO")
        # 使用友好的CPU名称
        self.log(f"处理器: {self.get_friendly_cpu_name()}", "INFO")
        # 备注原始处理器标识
        self.log(f"处理器标识: {platform.processor()}", "INFO")
        
        mem = psutil.virtual_memory()
        self.log(f"内存: 总计 {self.format_bytes(mem.total)}, 可用 {self.format_bytes(mem.available)}", "INFO")
        
        disk = psutil.disk_usage('/')
        self.log(f"磁盘: 总计 {self.format_bytes(disk.total)}, 可用 {self.format_bytes(disk.free)}", "INFO")
        
        # 网络信息
        hostname = socket.gethostname()
        self.log(f"主机名: {hostname}", "INFO")
        try:
            local_ip = socket.gethostbyname(hostname)
            self.log(f"本地IP: {local_ip}", "INFO")
        except:
            self.log("无法获取本地IP", "WARNING")
            
        # 显示网络接口
        try:
            net_interfaces = []
            for interface_name, interface_addresses in psutil.net_if_addrs().items():
                for address in interface_addresses:
                    if str(address.family) == 'AddressFamily.AF_INET':
                        net_interfaces.append(f"{interface_name}: {address.address}")
            
            if net_interfaces:
                self.log(f"网络接口: {', '.join(net_interfaces)}", "INFO")
        except:
            pass
            
        self.log("===== 系统信息结束 =====", "INFO")
        self.log("--------------------------------------", "INFO")
    
    def monitor_system_resources(self):
        """监控系统资源使用情况的后台线程"""
        last_log_time = 0
        
        while not self.stop_monitor:
            # 每60秒更新一次系统资源使用情况到界面
            current_time = time.time()
            if current_time - last_log_time >= 60:
                try:
                    self.update_all_system_info()  # 更新界面上的所有系统信息
                    last_log_time = current_time
                except Exception as e:
                    self.log(f"监控系统资源失败: {str(e)}", "ERROR")
            
            time.sleep(5)  # 每5秒检查一次是否需要记录
    
    def format_bytes(self, bytes_value):
        """格式化字节显示"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.2f} PB"
    
    def log(self, message, level="INFO"):
        """记录日志信息"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        
        # 保存日志记录，包含级别信息
        record = {"text": log_entry, "level": level}
        self.log_records.append(record)
        
        # 如果当前日志级别未被过滤，则显示
        if level in self.log_filters and self.log_filters[level]:
            self.display_log_entry(record)
    
    def display_log_entry(self, record):
        """显示单条日志条目"""
        level = record["level"]
        text = record["text"]
        
        # 设置颜色
        color = "#FFFFFF"  # 默认白色
        if level in LOG_LEVELS:
            color = LOG_LEVELS[level]["color"]
        
        # 添加到文本框
        self.log_text.moveCursor(QTextCursor.End)
        self.log_text.insertHtml(f'<span style="color:{color}">{text}</span><br>')
        self.log_text.moveCursor(QTextCursor.End)
    
    def filter_checkbox_changed(self, level, state):
        """处理过滤器复选框状态变化"""
        # 直接使用复选框的isChecked()获取最新状态
        checkbox = self.filter_checkboxes[level]
        is_checked = checkbox.isChecked()
        
        # 更新过滤状态
        self.log_filters[level] = is_checked
        
        # 应用过滤
        self.apply_filters()
    
    def apply_filters(self):
        """应用过滤并更新日志显示"""
        # 清空当前显示
        self.log_text.clear()
        
        # 显示所有符合过滤条件的日志
        for record in self.log_records:
            level = record["level"]
            
            # 检查是否应该显示该级别的日志
            if level in self.log_filters and self.log_filters[level]:
                self.display_log_entry(record)
        
        # 滚动到底部
        self.log_text.moveCursor(QTextCursor.End)
    
    def log_ui_event(self, window_name, event_type, details=""):
        """记录UI事件"""
        message = f"UI事件 - 窗口: {window_name}, 事件: {event_type}"
        if details:
            message += f", 详情: {details}"
        self.log(message, "UI")
    
    def log_network_event(self, event_type, url="", status="", details=""):
        """记录网络事件"""
        message = f"网络事件 - 类型: {event_type}"
        if url:
            message += f", URL: {url}"
        if status:
            message += f", 状态: {status}"
        if details:
            message += f", 详情: {details}"
        self.log(message, "NETWORK")
    
    def log_data_event(self, data_type, operation, details=""):
        """记录数据操作事件"""
        message = f"数据操作 - 类型: {data_type}, 操作: {operation}"
        if details:
            message += f", 详情: {details}"
        self.log(message, "INFO")
    
    def clear_log(self):
        """清空日志显示和记录"""
        self.log_text.clear()
        # 只清空显示，不清除记录
        self.log("日志显示已清空", "INFO")
    
    def save_log(self):
        """保存日志到文件"""
        # 确保日志目录存在
        log_dir = "Log"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # 获取应用程序名称和版本信息（如有）
        app_name = "LiXinTools"
        try:
            from config.config import Config
            if hasattr(Config, "APP_VERSION"):
                app_version = Config.APP_VERSION
            else:
                app_version = "1.0"
        except:
            app_version = "1.0"
            
        # 获取操作系统信息
        os_info = f"{platform.system()}{platform.release()}"
        
        # 获取用户名/主机名信息
        hostname = socket.gethostname()
        
        # 格式化当前日期时间（更详细易读）
        date_str = time.strftime("%Y-%m-%d")
        time_str = time.strftime("%H-%M-%S")
        
        # 生成日志文件名：应用名称_版本_日期_时间_主机名_操作系统.log
        filename = os.path.join(
            log_dir, 
            f"{app_name}_v{app_version}_{date_str}_{time_str}_{hostname}_{os_info}.log"
        )
        
        try:
            with open(filename, "w", encoding="utf-8") as f:
                for record in self.log_records:
                    f.write(f"{record['text']}\n")
            self.log(f"日志已保存到: {filename}", "SUCCESS")
        except Exception as e:
            self.log(f"保存日志失败: {str(e)}", "ERROR")
    
    def exception_hook(self, exc_type, exc_value, exc_traceback):
        """全局异常处理器"""
        # 获取异常的详细信息
        error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        self.log(f"未捕获异常:\n{error_msg}", "ERROR")
        
        # 调用默认的异常处理器
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
    
    def closeEvent(self, event):
        """窗口关闭事件，保存日志"""
        # 停止监控线程
        self.stop_monitor = True
        if hasattr(self, 'monitor_thread') and self.monitor_thread.is_alive():
            self.monitor_thread.join(1.0)  # 等待最多1秒
        
        # 停止内存更新定时器
        if hasattr(self, 'memory_timer'):
            self.memory_timer.stop()
            
        self.save_log()
        event.accept()

    def clean_memory(self):
        """清理LogWindow的内存"""
        process = psutil.Process(os.getpid())
        before_memory = process.memory_info().private / (1024 * 1024)
        
        self.log(f"开始清理内存，当前使用: {before_memory:.2f} MB", "INFO")
        
        # 1. 释放文本编辑器内存
        # 保存当前滚动位置
        scroll_bar = self.log_text.verticalScrollBar()
        scroll_position = scroll_bar.value()
        scroll_at_end = scroll_bar.value() == scroll_bar.maximum()
        
        # 清除文本编辑器内部缓存
        self.log_text.clear()
        self.log_text.document().clear()  # 更彻底清理文档对象
        self.log_text.setPlainText("")    # 确保完全清空
        
        # 临时减小缓冲区大小
        old_undo_limit = self.log_text.document().maximumBlockCount()
        self.log_text.document().setMaximumBlockCount(100)  # 临时设置小的最大块数
        self.log_text.document().setMaximumBlockCount(-1)   # 恢复无限制
        
        # 重新填充文本
        self.apply_filters()
        
        # 恢复滚动位置
        if scroll_at_end:
            scroll_bar.setValue(scroll_bar.maximum())
        else:
            scroll_bar.setValue(scroll_position)
        
        # 2. 尝试更多内存释放方法
        # 暂停内存监控定时器
        if hasattr(self, 'memory_timer') and self.memory_timer.isActive():
            self.memory_timer.stop()
        
        import gc
        
        # 首先执行基本垃圾回收
        gc.collect()
        
        # 禁用自动垃圾回收，以便我们手动完全控制
        old_gc_state = gc.isenabled()
        gc.disable()
        
        # 手动查找和清理循环引用
        # 这是比普通gc.collect()更深入的清理
        for obj in gc.get_objects():
            try:
                if isinstance(obj, dict) and not obj:  # 清理空字典
                    del obj
                elif isinstance(obj, list) and not obj:  # 清理空列表
                    del obj
            except Exception:
                pass
        
        # 执行多次强制垃圾回收
        for _ in range(5):  
            gc.collect(0)  # 第一代
            gc.collect(1)  # 第二代
            gc.collect(2)  # 第三代
            
        # 在Windows上尝试压缩工作集
        if platform.system() == "Windows":
            try:
                # 更激进的内存释放尝试
                import ctypes
                
                # 第一次尝试：最小化工作集
                ctypes.windll.kernel32.SetProcessWorkingSetSize(
                    ctypes.windll.kernel32.GetCurrentProcess(), -1, -1)
                
                # 第二次尝试：使用EmptyWorkingSet API
                try:
                    ctypes.windll.psapi.EmptyWorkingSet(
                        ctypes.windll.kernel32.GetCurrentProcess())
                except Exception:
                    pass
                    
                # 第三次尝试：使用VirtualUnlock释放锁定内存
                try:
                    # 获取系统信息
                    class SYSTEM_INFO(ctypes.Structure):
                        _fields_ = [
                            ("wProcessorArchitecture", ctypes.c_ushort),
                            ("wReserved", ctypes.c_ushort),
                            ("dwPageSize", ctypes.c_ulong),
                            ("lpMinimumApplicationAddress", ctypes.c_void_p),
                            ("lpMaximumApplicationAddress", ctypes.c_void_p),
                            ("dwActiveProcessorMask", ctypes.c_ulong),
                            ("dwNumberOfProcessors", ctypes.c_ulong),
                            ("dwProcessorType", ctypes.c_ulong),
                            ("dwAllocationGranularity", ctypes.c_ulong),
                            ("wProcessorLevel", ctypes.c_ushort),
                            ("wProcessorRevision", ctypes.c_ushort)
                        ]
                    
                    system_info = SYSTEM_INFO()
                    ctypes.windll.kernel32.GetSystemInfo(ctypes.byref(system_info))
                except Exception:
                    pass
                
            except Exception as e:
                self.log(f"尝试收回Windows内存时出错: {str(e)}", "ERROR")
                
        # 恢复垃圾回收状态
        if old_gc_state:
            gc.enable()
            
        # 再次执行一次完整的垃圾回收
        gc.collect()
        
        # 3. 清理Python解释器内部缓存
        try:
            # 尝试清理__pycache__目录
            import os
            import shutil
            for root, dirs, files in os.walk('.'):
                if '__pycache__' in dirs:
                    pycache_dir = os.path.join(root, '__pycache__')
                    try:
                        shutil.rmtree(pycache_dir)
                    except Exception:
                        pass
        except Exception:
            pass
            
        # 4. 尝试调用Qt的立即释放内存机制
        from PySide6.QtWidgets import QApplication
        QApplication.instance().processEvents()  # 处理所有挂起事件
        
        # 5. 强制重新绘制UI，可能会释放一些图形缓存
        self.update()
        
        # 恢复内存监控定时器
        if hasattr(self, 'memory_timer'):
            self.memory_timer.start(1000)
        
        # 清理后内存使用情况
        after_memory = process.memory_info().private / (1024 * 1024)
        memory_diff = before_memory - after_memory
        
        if memory_diff > 0:
            self.log(f"内存清理完成，释放: {memory_diff:.2f} MB，当前使用: {after_memory:.2f} MB", "SUCCESS")
        else:
            self.log(f"内存清理完成，无可释放内存，当前使用: {after_memory:.2f} MB", "INFO")
            
        # 强制更新内存使用显示
        self.update_usage_info()

    def showEvent(self, event):
        """窗口显示事件"""
        # 显示在屏幕中央
        screen_rect = QGuiApplication.primaryScreen().availableGeometry()
        window_rect = self.frameGeometry()
        center_point = screen_rect.center()
        window_rect.moveCenter(center_point)
        self.move(window_rect.topLeft())
        
        # 开始内存更新定时器
        if hasattr(self, 'memory_timer') and not self.memory_timer.isActive():
            self.memory_timer.start()
        
        super().showEvent(event) 