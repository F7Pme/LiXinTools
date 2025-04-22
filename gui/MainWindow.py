from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QTextEdit, QApplication, QSplitter
from PySide6.QtCore import QTimer, Qt, QEvent, QObject
from .BaseWindow import BaseWindow
from .TitleBar import TitleBar
from .SideBar import SideBar
from .SideBar_info import SideBarInfo
from .SideBar_bill import SideBarBill
from .SideBar_electricity import SideBarElectricity
from .SideBar_author import SideBarAuthor
from .SideBar_xxt import SideBarXxt
import gc
import psutil
import os
import platform

# 导入log_window为全局变量
global log_window
from gui.LoginWindow import log_window

# 存储MainWindow的单例实例
_main_window_instance = None

class MainWindow(BaseWindow):
    def __init__(self, bill_query=None):
        # 检查是否已经存在实例
        global _main_window_instance
        if _main_window_instance is not None:
            raise RuntimeError("MainWindow实例已经存在，请使用get_instance()获取")
            
        super().__init__()
        self.current_content = None
        self.side_bar_info = SideBarInfo()
        self.side_bar_bill = SideBarBill()
        self.side_bar_electricity = SideBarElectricity()
        self.side_bar_author = SideBarAuthor()
        self.side_bar_xxt = SideBarXxt()
        self.login_window = None  # 引用LoginWindow实例
        
        # 创建电费分析结果显示区域
        self.electricity_result_area = None
        
        # 重新导入log_window以确保获取最新实例
        try:
            from gui.LoginWindow import log_window
            self.log_window = log_window
            if self.log_window:
                self.log_window.log("主窗口(MainWindow)初始化", "INFO")
        except Exception:
            self.log_window = None
        
        if bill_query:
            self.set_bill_query(bill_query)
                
        self.setup_ui()
        # 设置初始选中状态
        self.side_bar.btn_info.setChecked(True)
        self.switch_content(self.side_bar_info)
        
        # 保存单例引用
        _main_window_instance = self

    @staticmethod
    def get_instance(bill_query=None):
        """获取MainWindow的单例实例"""
        global _main_window_instance
        if _main_window_instance is None:
            _main_window_instance = MainWindow(bill_query=bill_query)
        return _main_window_instance
        
    def set_bill_query(self, bill_query):
        """设置账单查询对象，可被外部调用以刷新会话"""
        self.side_bar_bill.set_bill_query(bill_query)
        try:
            if self.log_window:
                self.log_window.log("账单查询对象已设置到侧边栏", "INFO")
        except Exception:
            pass
            
    def refresh_bill_query(self, bill_query):
        """刷新账单查询对象和所有相关数据"""
        self.set_bill_query(bill_query)
        # 重置其他可能缓存了数据的组件
        if hasattr(self.side_bar_electricity, 'reset'):
            self.side_bar_electricity.reset()
        # 触发界面更新
        self.side_bar.btn_info.setChecked(True)
        self.switch_content(self.side_bar_info)

    def setup_ui(self):
        # 创建主水平布局
        main_layout = QHBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 添加侧边栏
        self.side_bar = SideBar()
        self.side_bar.btn_info.clicked.connect(self.show_info_content)
        self.side_bar.btn_bill.clicked.connect(self.show_bill_content)
        self.side_bar.btn_electricity.clicked.connect(self.show_electricity_content)
        self.side_bar.btn_author.clicked.connect(self.show_author_content)
        self.side_bar.btn_xxt.clicked.connect(self.show_xxt_content)
        
        # 设置侧边栏对账单侧边栏的引用
        self.side_bar.set_sidebar_bill(self.side_bar_bill)
        
        main_layout.addWidget(self.side_bar)

        # 创建右侧垂直布局
        right_layout = QVBoxLayout()
        right_layout.setSpacing(0)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # 添加标题栏
        self.title_bar = TitleBar(show_back_button=True)
        self.title_bar.minimizeClicked.connect(self.showMinimized)
        self.title_bar.closeClicked.connect(self.close)
        self.title_bar.backClicked.connect(self.handle_back_click)
        right_layout.addWidget(self.title_bar)

        # 主内容区域
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("background: #FDFDFD;")
        self.content_layout = QHBoxLayout()  # 改为水平布局以支持分割
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_widget.setLayout(self.content_layout)
        right_layout.addWidget(self.content_widget, stretch=1)

        # 将右侧布局添加到主布局
        main_layout.addLayout(right_layout)

        # 设置布局到中央部件
        self.centralWidget().layout().addLayout(main_layout)

        # 设置圆角裁剪
        self.setup_round_corners()
        
        # 记录UI设置完成
        try:
            if self.log_window:
                self.log_window.log_ui_event("MainWindow", "UI设置完成")
        except Exception:
            pass

    def handle_back_click(self):
        """处理返回按钮点击事件"""
        try:
            if self.log_window:
                self.log_window.log_ui_event("MainWindow", "返回按钮点击", "返回到登录窗口")
        except Exception:
            pass
            
        # 切换回登录窗口而不是创建新实例
        if self.login_window:
            self.login_window.show()
            self.login_window.activateWindow()
            self.login_window.raise_()
            self.hide()  # 只隐藏，不关闭
        else:
            # 向后兼容，以防登录窗口引用丢失
            from gui.LoginWindow import LoginWindow
            try:
                # 尝试获取单例实例
                login_window = LoginWindow.get_instance()
                self.login_window = login_window  # 保存引用
                login_window.show()
                self.hide()
            except:
                # 如果单例获取失败，创建新实例(旧方式)
                login_window = LoginWindow()
                login_window.show()
                self.close()

    def setup_round_corners(self):
        pass

    def show_info_content(self):
        """显示信息面板内容"""
        try:
            if self.log_window:
                self.log_window.log_ui_event("MainWindow", "切换内容", "个人信息面板")
        except Exception:
            pass
        self.switch_content(self.side_bar_info)

    def show_bill_content(self):
        """显示账单面板内容"""
        try:
            if self.log_window:
                self.log_window.log_ui_event("MainWindow", "切换内容", "账单面板")
        except Exception:
            pass
            
        # 先切换到账单面板，确保UI已正确显示
        self.switch_content(self.side_bar_bill)
        
        # 使用QTimer延迟执行查询，确保界面已完全加载
        # 同时检查是否已有数据，避免重复查询
        if not hasattr(self.side_bar_bill, 'has_queried_once') or not self.side_bar_bill.has_queried_once:
            QTimer.singleShot(100, self.side_bar.sidebar_bill.handle_query)
            if hasattr(self.side_bar_bill, 'has_queried_once'):
                self.side_bar_bill.has_queried_once = True
            else:
                # 添加标志属性
                self.side_bar_bill.has_queried_once = True

    def show_electricity_content(self):
        """显示电费面板内容"""
        try:
            if self.log_window:
                self.log_window.log_ui_event("MainWindow", "切换内容", "电费面板")
        except Exception:
            pass
        
        # 确保电费分析结果区域已初始化
        if not self.electricity_result_area:
            # 创建结果显示区域
            self.electricity_result_area = QTextEdit()
            self.electricity_result_area.setReadOnly(True)
            self.electricity_result_area.setMinimumWidth(400)
            self.electricity_result_area.setMinimumHeight(500)
            
            # 不再使用事件过滤器控制滚动条显示
            # 直接设置滚动条始终显示
            self.electricity_result_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
            self.electricity_result_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            
            # 应用更美观的样式 - 调整滚动条样式但保持始终可见
            self.electricity_result_area.setStyleSheet("""
                QTextEdit {
                    background-color: #F5F5F5;
                    color: #333333;
                    border: 1px solid #E0E0E0;
                    border-radius: 4px;
                    padding: 15px;
                    line-height: 1.5;
                    font-family: "Microsoft YaHei";
                    font-size: 14px;
                }
                QScrollBar:vertical {
                    width: 10px;
                    background: #F0F0F0;
                    margin: 0px;
                    border: none;
                }
                QScrollBar::handle:vertical {
                    background-color: #AAAAAA;
                    min-height: 20px;
                    border-radius: 5px;
                }
                QScrollBar::handle:vertical:hover {
                    background-color: #888888;
                }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                    height: 0px;
                }
                QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                    background: none;
                }
                QScrollBar:horizontal {
                    height: 10px;
                    background: #F0F0F0;
                    margin: 0px;
                    border: none;
                }
                QScrollBar::handle:horizontal {
                    background-color: #AAAAAA;
                    min-width: 20px;
                    border-radius: 5px;
                }
                QScrollBar::handle:horizontal:hover {
                    background-color: #888888;
                }
                QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                    width: 0px;
                }
                QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                    background: none;
                }
            """)
            
            # 初始文本
            self.electricity_result_area.setText("点击分析按钮查看电费分析结果")
            
            # 连接电费分析完成信号
            self.side_bar_electricity.analysis_result_ready.connect(self.update_electricity_analysis_result)
        
        # 切换到含有分割器的布局
        self.switch_content_with_result_area(self.side_bar_electricity, self.electricity_result_area)

    def update_electricity_analysis_result(self, result):
        """更新电费分析结果"""
        if self.electricity_result_area:
            self.electricity_result_area.setText(result)
            
    def switch_content_with_result_area(self, content, result_area):
        """切换到带有结果区域的内容布局"""
        # 首先清除当前内容
        if self.current_content:
            if hasattr(self, 'splitter') and self.splitter is not None:
                # 检查确保splitter不是None再移除
                try:
                    self.content_layout.removeWidget(self.splitter)
                except Exception as e:
                    print(f"移除分割器出错: {e}")
                
                # 先将组件从分割器中移除，确保不被删除
                try:
                    if content.parent() == self.splitter:
                        content.setParent(None)
                    if result_area.parent() == self.splitter:
                        result_area.setParent(None)
                except Exception as e:
                    print(f"从分割器移除组件出错: {e}")
                
                # 安全删除分割器
                try:
                    self.splitter.deleteLater()
                except Exception as e:
                    print(f"删除分割器出错: {e}")
            else:
                try:
                    # 确保当前内容不是None
                    if self.current_content is not None:
                        self.content_layout.removeWidget(self.current_content)
                except Exception as e:
                    print(f"移除当前内容出错: {e}")
            
            # 隐藏当前内容
            try:
                if self.current_content is not None:
                    self.current_content.hide()
            except Exception as e:
                print(f"隐藏当前内容出错: {e}")
        
        try:
            # 创建新分割器组件
            self.splitter = QSplitter(Qt.Horizontal)
            self.splitter.setParent(self.content_widget)  # 确保分割器有正确的父对象
            
            # 确保组件有正确的父对象
            if content is not None:
                content.setParent(self.splitter)
                self.splitter.addWidget(content)
                
            if result_area is not None:
                result_area.setParent(self.splitter)
                self.splitter.addWidget(result_area)
            
            # 设置分割器初始位置 - 调整比例为30:70，让右侧结果区域更宽
            self.splitter.setSizes([int(self.width() * 0.3), int(self.width() * 0.7)])
            
            # 将分割器添加到内容布局
            self.content_layout.addWidget(self.splitter)
            
            # 显示内容
            if content is not None:
                content.show()
            if result_area is not None:
                result_area.show()
                
            self.current_content = content
            
            # 更新按钮选中状态
            self.side_bar.btn_info.setChecked(content == self.side_bar_info)
            self.side_bar.btn_bill.setChecked(content == self.side_bar_bill)
            self.side_bar.btn_electricity.setChecked(content == self.side_bar_electricity)
            self.side_bar.btn_author.setChecked(content == self.side_bar_author)
            self.side_bar.btn_xxt.setChecked(content == self.side_bar_xxt)
        except Exception as e:
            print(f"创建分割器布局出错: {e}")
            # 失败时的降级策略 - 直接切换到常规内容
            if content is not None:
                self.switch_content(content)

    def show_author_content(self):
        """显示作者信息面板内容"""
        try:
            if self.log_window:
                self.log_window.log_ui_event("MainWindow", "切换内容", "作者信息面板")
        except Exception:
            pass
        self.switch_content(self.side_bar_author)
        
    def show_xxt_content(self):
        """显示学习通面板内容"""
        try:
            if self.log_window:
                self.log_window.log_ui_event("MainWindow", "切换内容", "学习通面板")
        except Exception:
            pass
        
        # 调整切换内容前，调整标题栏样式以配合学习通界面
        try:
            if hasattr(self, 'title_bar'):
                # 这里可以考虑在未来添加特殊的标题栏样式，配合学习通界面
                pass
        except Exception:
            pass
            
        # 切换到学习通内容
        self.switch_content(self.side_bar_xxt)

    def switch_content(self, new_content):
        """通用内容切换方法"""
        # 记录内容切换详细信息
        try:
            if self.log_window:
                old_content_name = "无" if not self.current_content else self.get_content_name(self.current_content)
                new_content_name = self.get_content_name(new_content)
                self.log_window.log_ui_event("MainWindow", "内容切换", f"从 {old_content_name} 切换到 {new_content_name}")
        except Exception:
            pass
            
        # 移除现有内容（包括可能存在的分割器）
        try:
            if self.current_content is not None:
                if hasattr(self, 'splitter') and self.splitter is not None:
                    try:
                        self.content_layout.removeWidget(self.splitter)
                    except Exception as e:
                        print(f"移除分割器出错: {e}")
                    
                    # 安全地从分割器中移除组件
                    try:
                        if self.current_content.parent() == self.splitter:
                            self.current_content.setParent(None)
                        if hasattr(self, 'electricity_result_area') and self.electricity_result_area and self.electricity_result_area.parent() == self.splitter:
                            self.electricity_result_area.setParent(None)
                    except Exception as e:
                        print(f"从分割器移除组件出错: {e}")
                    
                    # 安全删除分割器
                    try:
                        self.splitter.deleteLater()
                    except Exception as e:
                        print(f"删除分割器出错: {e}")
                    self.splitter = None
                else:
                    try:
                        self.content_layout.removeWidget(self.current_content)
                    except Exception as e:
                        print(f"移除当前内容出错: {e}")
                
                # 隐藏当前内容，但不设置父对象为None
                try:
                    self.current_content.hide()
                except Exception as e:
                    print(f"隐藏当前内容出错: {e}")
        except Exception as e:
            print(f"切换内容时出错: {e}")
        
        try:
            # 设置新内容的父对象并添加到布局
            if new_content is not None:
                new_content.setParent(self.content_widget)
                
                # 添加新内容
                self.current_content = new_content
                self.content_layout.addWidget(self.current_content)
                self.current_content.show()
                
                # 更新按钮选中状态
                self.side_bar.btn_info.setChecked(new_content == self.side_bar_info)
                self.side_bar.btn_bill.setChecked(new_content == self.side_bar_bill)
                self.side_bar.btn_electricity.setChecked(new_content == self.side_bar_electricity)
                self.side_bar.btn_author.setChecked(new_content == self.side_bar_author)
                self.side_bar.btn_xxt.setChecked(new_content == self.side_bar_xxt)
        except Exception as e:
            print(f"添加新内容时出错: {e}")
    
    def get_content_name(self, content):
        """获取内容面板的名称"""
        if content == self.side_bar_info:
            return "个人信息面板"
        elif content == self.side_bar_bill:
            return "账单面板"
        elif content == self.side_bar_electricity:
            return "电费面板"
        elif content == self.side_bar_author:
            return "作者信息面板"
        elif content == self.side_bar_xxt:
            return "学习通面板"
        else:
            return "未知面板"
        
    def closeEvent(self, event):
        """窗口关闭事件，处理资源释放和内存清理"""
        try:
            if self.log_window:
                self.log_window.log("主窗口(MainWindow)关闭", "INFO")
        except Exception:
            pass
        
        # 断开所有信号连接
        try:
            # 断开标题栏信号
            if hasattr(self, 'title_bar'):
                try:
                    self.title_bar.backClicked.disconnect()
                    self.title_bar.minimizeClicked.disconnect()
                    self.title_bar.closeClicked.disconnect()
                except:
                    pass
            
            # 断开侧边栏信号
            if hasattr(self, 'side_bar'):
                try:
                    self.side_bar.btn_info.clicked.disconnect()
                    self.side_bar.btn_bill.clicked.disconnect()
                    self.side_bar.btn_electricity.clicked.disconnect()
                    self.side_bar.btn_author.clicked.disconnect()
                    self.side_bar.btn_xxt.clicked.disconnect()
                except:
                    pass
        except Exception:
            pass
        
        # 停止所有计时器
        try:
            for child in self.findChildren(QTimer):
                child.stop()
        except Exception:
            pass
            
        # 如果应用程序正在退出，才真正释放资源
        if not QApplication.instance() or QApplication.instance().closingDown():
            # 清除单例引用
            global _main_window_instance
            _main_window_instance = None
            
            # 显式删除大型组件
            try:
                # 释放内容区域
                if hasattr(self, 'content_layout') and self.current_content:
                    self.content_layout.removeWidget(self.current_content)
                    if self.current_content:
                        self.current_content.setParent(None)
                        self.current_content.deleteLater()
                        self.current_content = None
                
                # 释放侧边栏组件
                if hasattr(self, 'side_bar'):
                    self.side_bar.setParent(None)
                    self.side_bar.deleteLater()
                
                if hasattr(self, 'side_bar_info'):
                    self.side_bar_info.setParent(None)
                    self.side_bar_info.deleteLater()
                    
                if hasattr(self, 'side_bar_bill'):
                    self.side_bar_bill.setParent(None)
                    self.side_bar_bill.deleteLater()
                    
                if hasattr(self, 'side_bar_electricity'):
                    self.side_bar_electricity.setParent(None)
                    self.side_bar_electricity.deleteLater()
                    
                if hasattr(self, 'side_bar_author'):
                    self.side_bar_author.setParent(None)
                    self.side_bar_author.deleteLater()
                    
                if hasattr(self, 'side_bar_xxt'):
                    self.side_bar_xxt.setParent(None)
                    self.side_bar_xxt.deleteLater()
            except Exception:
                pass
                
            # 清理内存
            try:
                import gc
                gc.collect()
            except Exception:
                pass
        
        # 调用父类的关闭事件处理
        super().closeEvent(event)

    # 添加更新头像的方法
    def update_avatar(self, avatar_url, user_name=None):
        """更新标题栏中的头像"""
        if hasattr(self, 'title_bar') and self.title_bar:
            # 获取学号信息
            student_id = ""
            if hasattr(self, 'side_bar_info'):
                try:
                    # 从学工号标签中提取学号
                    id_text = self.side_bar_info.id_label.text()
                    
                    # 处理两种可能的分隔符
                    if "学工号:" in id_text:
                        student_id = id_text.split("学工号:")[1].strip()
                    elif "学工号: " in id_text:
                        student_id = id_text.split("学工号: ")[1].strip()
                    else:
                        # 尝试更一般的分割方式
                        parts = id_text.split(":")
                        if len(parts) > 1:
                            student_id = parts[1].strip()
                except Exception as e:
                    if self.log_window:
                        self.log_window.log(f"提取学号失败: {str(e)}", "ERROR")
            
            # 如果有学号和用户名，将它们组合显示
            display_name = user_name
            if user_name and student_id:
                display_name = f"{user_name} {student_id}"
            
            # 更新标题栏
            self.title_bar.update_avatar(avatar_url, display_name)
            
            try:
                if self.log_window:
                    self.log_window.log_ui_event("MainWindow", "更新头像", f"头像URL: {avatar_url}, 显示名称: {display_name}")
            except Exception:
                pass