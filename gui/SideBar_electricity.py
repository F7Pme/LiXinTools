from PySide6.QtWidgets import (QWidget, QLabel, QVBoxLayout, QHBoxLayout, 
                              QComboBox, QLineEdit, QPushButton, QMessageBox, QApplication,
                              QDialog, QFormLayout, QDialogButtonBox, QCheckBox, QScrollArea, QTextEdit)
from PySide6.QtCore import Qt, Signal, QObject, QThread, QEvent
from utils.query_electricity import ElectricityQuery
from utils.analysis_electricity import ElectricityAnalysis
from config.config import Config
from gui.LoadWindow import show_loading, LoadingWindow
from gui.MessageWindow import show_message
import time
import datetime

# 确保log_window可以被所有类使用
global log_window
from gui.LoginWindow import log_window

class ElectricityQueryWorker(QObject):
    """电费查询工作线程信号对象"""
    finished = Signal(str)
    
    def __init__(self, query, building, room):
        super().__init__()
        self.query = query
        self.building = building
        self.room = room
        
    def run(self):
        """执行查询操作"""
        # 查询单个宿舍不记录日志，避免影响性能
        try:
            result = self.query.query(self.building, self.room)
            self.finished.emit(result)
        except Exception as e:
            self.finished.emit(f"查询失败: {str(e)}")

class AllRoomsQueryWorker(QObject):
    """查询所有宿舍的工作线程信号对象"""
    progress = Signal(str, int, int)
    finished = Signal(dict, str, int, int)  # 添加总数和成功数参数
    
    def __init__(self, query):
        super().__init__()
        self.query = query
        
    def update_progress_with_log(self, message, total, current):
        """更新进度但不记录日志"""
        # 仅发送进度信号，不再记录日志
        self.progress.emit(message, total, current)
        
    def run(self):
        """执行查询所有宿舍操作"""
        from gui.LoginWindow import log_window
        
        # 只记录开始日志
        try:
            if log_window:
                log_window.log("电费批量查询开始，使用多线程并发", "INFO")
        except Exception:
            pass
            
        try:
            # 传递自定义的进度回调函数
            results, query_time = self.query.query_all_rooms(self.update_progress_with_log)
            
            # 将查询结果保存到历史数据库，作为新列
            try:
                # 使用新方法保存批量查询结果
                self.query.save_batch_to_history_database(query_time, results)
                if log_window:
                    log_window.log(f"电费批量查询结果已保存为历史记录列", "INFO")
            except Exception as save_error:
                if log_window:
                    log_window.log(f"保存电费批量查询历史记录失败: {str(save_error)}", "ERROR")
            
            # 从结果中获取统计数据（适应新格式）
            total_rooms = 0
            success_rooms = 0
            
            if isinstance(results, dict):
                if 'stats' in results:
                    # 使用返回的统计数据
                    total_rooms = results['stats'].get('total_count', 0)
                    success_rooms = results['stats'].get('success_count', 0)
                    
                    # 获取真正的数据部分
                    data = results.get('data', {})
                elif 'data' not in results:
                    # 旧格式，直接统计
                    data = results
                    for building, rooms in data.items():
                        total_rooms += len(rooms)
                        for room, result in rooms.items():
                            if "查询失败" not in result and "查询异常" not in result and "处理错误" not in result:
                                success_rooms += 1
                else:
                    # 已经包含data字段，但没有stats
                    data = results.get('data', {})
                    for building, rooms in data.items():
                        total_rooms += len(rooms)
                        for room, result in rooms.items():
                            if "查询失败" not in result and "查询异常" not in result and "处理错误" not in result:
                                success_rooms += 1
            else:
                # 不是字典格式，使用空数据
                data = {}
            
            # 只记录结束日志
            try:
                if log_window:
                    log_window.log(f"电费批量查询完成: 共{total_rooms}个房间, 成功{success_rooms}个", "INFO")
            except Exception:
                pass
                
            # 发送结果和统计数据
            self.finished.emit(data, query_time, total_rooms, success_rooms)
            
        except Exception as e:
            # 只记录错误日志
            try:
                if log_window:
                    log_window.log(f"电费批量查询失败: {str(e)}", "ERROR")
            except Exception:
                pass
            
            self.progress.emit(f"查询失败: {str(e)}", 0, 0)
            # 发送空结果和统计数据
            self.finished.emit({}, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 0, 0)

class AnalysisWorker(QObject):
    """电量数据分析线程信号对象"""
    finished = Signal(str)
    
    def __init__(self, host, user, password):
        super().__init__()
        self.host = host
        self.user = user
        self.password = password
        
    def run(self):
        """执行分析操作"""
        try:
            analyzer = ElectricityAnalysis(self.host, self.user, self.password)
            result = analyzer.analyze_data()
            self.finished.emit(result)
        except Exception as e:
            self.finished.emit(f"分析失败: {str(e)}")

class SideBarElectricity(QWidget):
    # 添加信号，用于将分析结果发送到主窗口
    analysis_result_ready = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.query = ElectricityQuery()
        self.loading_indicator = None
        self.query_in_progress = False  # 标记查询是否正在进行
        
        try:
            if log_window:
                log_window.log_ui_event("SideBarElectricity", "初始化")
        except Exception:
            pass
            
        self.setup_ui()

    def setup_ui(self):
        # 主布局
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(10)
        layout.setContentsMargins(30, 30, 10, 10)

        # 标题
        self.title = QLabel("电费查询")
        self.title.setStyleSheet("font-size: 18px; font-weight: bold; color: #0078D4;")
        layout.addWidget(self.title)

        # 楼号选择
        self.building_label = QLabel("楼号:")
        self.building_label.setStyleSheet("font-size: 14px; color: #000000;")
        
        self.building_combo = QComboBox()
        self.building_combo.setFixedWidth(120)
        self.building_combo.setStyleSheet("""
            font-size: 14px;
            color: #000000;
        """)
        self.building_combo.setCursor(Qt.PointingHandCursor)
        for num, name in Config.BUILDING_NAME_MAP.items():
            self.building_combo.addItem(f"新苑{name}号楼", num)
        layout.addWidget(self.building_label)
        layout.addWidget(self.building_combo)

        # 宿舍号输入
        self.room_label = QLabel("宿舍号:")
        self.room_label.setStyleSheet("font-size: 14px; color: #000000;")
        
        self.room_input = QLineEdit()
        self.room_input.setFixedWidth(120)
        self.room_input.setPlaceholderText("如: 309 或 4-101")
        self.room_input.setStyleSheet("""
            font-size: 14px;
            color: #000000;
        """)
        layout.addWidget(self.room_label)
        layout.addWidget(self.room_input)

        # 按钮布局 - 使用左对齐以保持紧凑
        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignLeft)
        button_layout.setSpacing(10)  # 设置按钮之间的间距
        
        # 查询按钮
        self.query_btn = QPushButton("查询")
        self.query_btn.setFixedSize(90, 40)
        
        # 添加悬停样式
        self.query_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                background-color: #0078D4;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #499DDD;
            }
        """)
        
        self.query_btn.setCursor(Qt.PointingHandCursor)
        self.query_btn.clicked.connect(self.execute_query)
        button_layout.addWidget(self.query_btn)
        
        # 查询所有宿舍按钮
        self.query_all_btn = QPushButton("查询所有宿舍")
        self.query_all_btn.setFixedSize(120, 40)
        
        # 添加悬停样式
        self.query_all_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                background-color: #107C10;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #2A852A;
            }
        """)
        
        self.query_all_btn.setCursor(Qt.PointingHandCursor)
        self.query_all_btn.clicked.connect(self.execute_query_all)
        button_layout.addWidget(self.query_all_btn)
        
        # 添加分析按钮
        self.analysis_btn = QPushButton("分析")
        self.analysis_btn.setFixedSize(90, 40)
        self.analysis_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                background-color: #0078D4;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #499DDD;
            }
        """)
        self.analysis_btn.setCursor(Qt.PointingHandCursor)
        self.analysis_btn.clicked.connect(self.execute_analysis)
        button_layout.addWidget(self.analysis_btn)
        
        layout.addLayout(button_layout)

        # 添加单个宿舍查询结果显示区域
        self.query_result_label = QLabel("输入宿舍信息点击查询")
        self.query_result_label.setWordWrap(True)
        self.query_result_label.setMinimumHeight(80)
        self.query_result_label.setStyleSheet("""
            font-size: 14px;
            color: #333333;
            padding: 10px;
            margin-top: 10px;
        """)
        layout.addWidget(self.query_result_label)

        # 设置布局
        self.setLayout(layout)
        
        try:
            if log_window:
                log_window.log_ui_event("SideBarElectricity", "UI设置完成")
        except Exception:
            pass

    def execute_query(self):
        # 避免重复点击，如果查询正在进行，直接返回
        if self.query_in_progress:
            return
            
        self.query_in_progress = True
        
        building = self.building_combo.currentData()
        room = self.room_input.text().strip()
        
        if not room:
            # 使用MessageBox而不是result_text显示错误
            show_message(
                parent=self.window(),
                message="请输入宿舍号",
                icon_type="warning",
                auto_close=True,
                duration=2000
            )
            self.query_in_progress = False
            return
            
        # 自动补充楼层前缀
        if '-' not in room:
            room = f"{building}-{room}"
        
        # 显示加载指示器
        main_window = self.window()  # 获取主窗口
        self.loading_indicator = show_loading(main_window, "正在查询电费...")
        
        # 创建查询工作线程
        self.thread = QThread()
        self.worker = ElectricityQueryWorker(self.query, building, room)
        self.worker.moveToThread(self.thread)
        
        # 连接信号
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_query_completed)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(lambda: setattr(self, 'query_in_progress', False))
        
        # 启动线程
        self.thread.start()
    
    def execute_query_all(self):
        # 避免重复点击，如果查询正在进行，直接返回
        if self.query_in_progress:
            return
            
        # 先获取MySQL凭据
        credentials_dialog = MySQLCredentialsDialog(self.window())
        if credentials_dialog.exec():
            # 获取凭据
            credentials = credentials_dialog.get_credentials()
            
            # 设置数据库凭据
            self.query.db_host = credentials['host']
            self.query.db_user = credentials['username']
            self.query.db_password = credentials['password']
            
            # 测试数据库连接
            try:
                import pymysql
                conn = pymysql.connect(
                    host=credentials['host'],
                    user=credentials['username'],
                    password=credentials['password'],
                    connect_timeout=5
                )
                conn.close()
            except Exception as e:
                # 连接失败，显示错误信息并返回
                error_message = f"数据库连接失败: {str(e)}"
                show_message(
                    parent=self.window(),
                    message=error_message,
                    icon_type="error",
                    auto_close=False,
                    duration=5000
                )
                return
            
            # 弹出确认对话框
            reply = QMessageBox.question(
                self.window(), 
                "确认查询", 
                "查询所有宿舍会花费较长时间，且会大量占用系统资源，确定要继续吗？",
                QMessageBox.Yes | QMessageBox.No, 
                QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return
            
            self.query_in_progress = True
            
            # 记录开始查询的日志
            try:
                if log_window:
                    log_window.log("开始执行电费批量查询", "INFO")
            except Exception:
                pass
            
            # 创建进度对话框 - 替换为LoadWindow样式的进度显示
            self.loading_indicator = LoadingWindow(self.window(), "正在查询电费数据...\n(0/0)", True)
            self.loading_indicator.setMinimumWidth(300)
            self.loading_indicator.show()
            
            # 创建查询工作线程
            self.all_thread = QThread()
            self.all_worker = AllRoomsQueryWorker(self.query)
            
            self.all_worker.moveToThread(self.all_thread)
            
            # 连接信号
            self.all_thread.started.connect(self.all_worker.run)
            self.all_worker.progress.connect(self.update_loading_progress)
            self.all_worker.finished.connect(self.on_query_all_completed)
            self.all_worker.finished.connect(self.all_thread.quit)
            self.all_worker.finished.connect(self.all_worker.deleteLater)
            self.all_thread.finished.connect(self.all_thread.deleteLater)
            self.all_thread.finished.connect(lambda: setattr(self, 'query_in_progress', False))
            
            # 启动线程
            self.all_thread.start()
    
    def update_loading_progress(self, message, total, current):
        """更新加载窗口的进度显示"""
        if self.loading_indicator:
            try:
                # 确保当前进度不超过总数
                if current > total and total > 0:
                    current = total

                # 创建格式化的进度文本
                progress_text = f"正在查询电费数据...\n({current}/{total})"
                if "错误" in message or "失败" in message:
                    progress_text += f"\n{message}"
                
                # 更新加载窗口文本
                self.loading_indicator.set_text(progress_text)
                
                # 强制处理事件，确保UI响应
                QApplication.processEvents()
            except Exception:
                pass
    
    def on_query_all_completed(self, results, query_time, total_rooms, success_rooms):
        """查询所有宿舍完成后的回调 - 修改为直接接收总数和成功数"""
        # 关闭进度对话框
        if hasattr(self, 'loading_indicator') and self.loading_indicator:
            self.loading_indicator.close()
            self.loading_indicator = None
        
        # 直接使用传入的统计数据，不再计算
        
        # 记录查询完成的日志
        try:
            if log_window:
                log_window.log(f"电费批量查询完成: {success_rooms}/{total_rooms}", "INFO")
        except Exception:
            pass
        
        # 显示结果消息框
        result_message = (
            f"已查询完成所有宿舍电费\n"
            f"查询时间: {query_time}\n"
            f"共查询 {total_rooms} 个宿舍\n"
            f"成功查询 {success_rooms} 个宿舍\n"
            f"数据已保存到数据库:\n"
            f"- 原格式: electricity_data.all_room\n"
            f"- 新格式: electricity_data.electricity_history"
        )
        
        # 使用MessageWindow替代QMessageBox
        show_message(
            parent=self.window(),
            message=result_message,
            icon_type="success",
            auto_close=False,
            duration=5000
        )
        
        # 重置查询状态
        self.query_in_progress = False

    def on_query_completed(self, result):
        """查询完成后的回调"""
        # 关闭加载指示器
        if self.loading_indicator:
            self.loading_indicator.close()
            self.loading_indicator = None
        
        # 更新界面上的结果标签
        self.query_result_label.setText(result)
        
        # 根据结果设置不同的样式
        if "剩余电量" in result:
            # 查询成功 - 绿色
            self.query_result_label.setStyleSheet("""
                font-size: 14px;
                color: #107C10;
                padding: 10px;
                margin-top: 10px;
            """)
        else:
            # 查询失败 - 红色
            self.query_result_label.setStyleSheet("""
                font-size: 14px;
                color: #E74C3C;
                padding: 10px;
                margin-top: 10px;
            """)
        
        # 显示单个房间查询结果
        show_message(
            parent=self.window(),
            message=result,
            icon_type="success" if "剩余电量" in result else "error",
            auto_close=True,
            duration=3000
        )
        
        # 重置查询状态
        self.query_in_progress = False

    def execute_analysis(self):
        """执行电量数据分析"""
        # 避免重复点击，如果查询/分析正在进行，直接返回
        if self.query_in_progress:
            return
            
        # 先获取MySQL凭据
        credentials_dialog = MySQLCredentialsDialog(self.window())
        if credentials_dialog.exec():
            # 获取凭据
            credentials = credentials_dialog.get_credentials()
            
            # 测试数据库连接
            try:
                import pymysql
                conn = pymysql.connect(
                    host=credentials['host'],
                    user=credentials['username'],
                    password=credentials['password'],
                    connect_timeout=5
                )
                conn.close()
            except Exception as e:
                # 连接失败，显示错误信息并返回
                error_message = f"数据库连接失败: {str(e)}"
                show_message(
                    parent=self.window(),
                    message=error_message,
                    icon_type="error",
                    auto_close=False,
                    duration=5000
                )
                return
                
            self.query_in_progress = True
            
            # 显示加载指示器
            self.loading_indicator = show_loading(self.window(), "正在分析电量数据...")
            
            # 创建分析工作线程
            self.analysis_thread = QThread()
            self.analysis_worker = AnalysisWorker(
                credentials['host'],
                credentials['username'],
                credentials['password']
            )
            self.analysis_worker.moveToThread(self.analysis_thread)
            
            # 连接信号
            self.analysis_thread.started.connect(self.analysis_worker.run)
            self.analysis_worker.finished.connect(self.on_analysis_completed)
            self.analysis_worker.finished.connect(self.analysis_thread.quit)
            self.analysis_worker.finished.connect(self.analysis_worker.deleteLater)
            self.analysis_thread.finished.connect(self.analysis_thread.deleteLater)
            self.analysis_thread.finished.connect(lambda: setattr(self, 'query_in_progress', False))
            
            # 启动线程
            self.analysis_thread.start()
            
    def on_analysis_completed(self, result):
        """分析完成后的回调"""
        # 关闭加载指示器
        if self.loading_indicator:
            self.loading_indicator.close()
            self.loading_indicator = None
        
        # 发送分析结果信号到MainWindow
        self.analysis_result_ready.emit(result)
        
        # 重置查询状态
        self.query_in_progress = False
        
        # 成功完成分析
        show_message(
            parent=self.window(),
            message="电量数据分析完成",
            icon_type="success",
            auto_close=True,
            duration=2000
        )

class MySQLCredentialsDialog(QDialog):
    """MySQL 凭据输入对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("MySQL 数据库连接")
        self.resize(350, 200)
        
        layout = QVBoxLayout(self)
        
        # 表单布局
        form_layout = QFormLayout()
        
        # 主机
        self.host_input = QLineEdit("localhost")
        form_layout.addRow("主机地址:", self.host_input)
        
        # 用户名
        self.username_input = QLineEdit("root")
        form_layout.addRow("用户名:", self.username_input)
        
        # 密码 - 改为普通文本显示，不再隐藏
        self.password_input = QLineEdit("123456")
        # 不再使用密码模式
        # self.password_input.setEchoMode(QLineEdit.Password)
        form_layout.addRow("密码:", self.password_input)
        
        # 记住凭据选项
        self.remember_credentials = QCheckBox("记住凭据")
        self.remember_credentials.setChecked(True)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        layout.addLayout(form_layout)
        layout.addWidget(self.remember_credentials)
        layout.addWidget(button_box)
    
    def get_credentials(self):
        """获取输入的凭据"""
        return {
            'host': self.host_input.text(),
            'username': self.username_input.text(),
            'password': self.password_input.text(),
            'remember': self.remember_credentials.isChecked()
        }
