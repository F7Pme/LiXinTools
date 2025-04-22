import os
import requests
from core.auth import SessionManager
from core.display import DisplayHandler
from utils.query_electricity import ElectricityQuery
from utils.query_bill import BillQuery
from config.config import Config
from utils.data_parser import DataParser



class MainApp:
    def __init__(self):
        # 只创建cookies目录，不再创建room_data目录
        os.makedirs(os.path.dirname(Config.COOKIE_FILE), exist_ok=True)
        self.session_mgr = SessionManager()
        self.display = DisplayHandler()
        self.electricity_query = ElectricityQuery()
        self.bill_query = None

    def show_mode_status(self):
        mode = "完整功能模式" if self.bill_query else "免登录模式"
        print(f"\n当前模式：{mode}")
    
    def _clean_choice_input(self, raw_input):
        """清理用户输入"""
        return raw_input.lower().strip().replace(' ', '')
    
    def select_login_mode(self):
        """新版登录模式选择"""
        while True:
            print("\n请选择登录方式：")
            print("1. 一卡通账号登录（完整功能）")
            print("2. 免登录模式（仅电费查询）")
            choice = input("请输入选项 (1/2/q退出): ").strip().lower()
            
            if choice in ('1', '2', 'q'):
                return choice
            print("无效输入，请重新输入")
            
    def handle_login(self):
        choice = self.select_login_mode()
        if choice == 'q':
            return False
        if choice == '1':
            return self.handle_full_login()
        print("\n【免登录模式】仅支持电费查询功能")
        return True
    
    def handle_full_login(self):
        """处理完整登录模式"""
        accounts = self.session_mgr.load_cookies()
        valid_users = []

        # 验证所有账户的有效性
        for user_id, data in accounts.items():
            temp_session = requests.Session()
            temp_session.cookies = requests.utils.cookiejar_from_dict(data["cookies"])
            temp_session.headers.update({"User-Agent": Config.USER_AGENT})
            if self.validate_temp_session(temp_session):
                valid_users.append(user_id)

        if valid_users:
            print("\n发现有效会话账户:")
            for idx, user_id in enumerate(valid_users, 1):
                print(f"{idx}. {user_id}")
            print("n. 登录新账户")
            choice = input("请选择账户 (输入编号/n): ").strip().lower()
            
            if choice == 'n':
                return self.handle_new_login()
            else:
                try:
                    idx = int(choice) - 1
                    selected_user = valid_users[idx]
                    self.session_mgr.current_user = selected_user
                    self.session_mgr.session.cookies = requests.utils.cookiejar_from_dict(
                        accounts[selected_user]["cookies"]
                    )
                    if self.fetch_basic_data():  # 调用获取用户信息的逻辑
                        self.bill_query = BillQuery(self.session_mgr.session)
                    return True
                except (ValueError, IndexError):
                    print("无效选择，需要重新登录")
                    return self.handle_new_login()
        else:
            print("没有发现有效会话")
            return self.handle_new_login()

    def validate_temp_session(self, session):
        """验证临时会话有效性"""
        try:
            resp = session.get(
                "https://yktepay.lixin.edu.cn/ykt/h5/index",
                timeout=Config.TIMEOUT//2
            )
            return resp.ok and "一卡通" in resp.text
        except requests.RequestException:
            return False

    def handle_new_login(self):
        user_id = self.session_mgr.create_new_session()
        if user_id:
            self.session_mgr.current_user = user_id  # 设置新登录用户的ID
            self.bill_query = BillQuery(self.session_mgr.session)
            return True
        return False
           
    def initialize_full_session(self):
        """完整登录模式初始化"""
        if not self.initialize_session():
            return False
        if not self.fetch_basic_data():
            return False
        self.bill_query = BillQuery(self.session_mgr.session)
        return True
         
    def initialize_session(self):
        cookies = self.session_mgr.load_cookies()
        if cookies:
            self.session_mgr.session.cookies.update(cookies)
            if self.session_mgr.validate_session():
                print("检测到有效会话")
                # 新增用户选择提示
                choice = input("是否使用当前会话？(y/n，默认y): ").strip().lower()
                if choice != 'n':
                    return True
                else:
                    # 用户选择重新登录
                    print("需要重新授权")
                    if self.session_mgr.create_new_session():
                        return True
                    return False
        
        # 没有有效cookie或用户选择重新登录
        print("需要重新授权")
        if self.session_mgr.create_new_session():
            return True
        return False

    def fetch_basic_data(self):
        try:
            index_res = self.session_mgr.session.get("https://yktepay.lixin.edu.cn/ykt/h5/index", timeout=Config.TIMEOUT)
            account_res = self.session_mgr.session.get("https://yktepay.lixin.edu.cn/ykt/h5/accountinfo", timeout=Config.TIMEOUT)
            index_res.raise_for_status()
            account_res.raise_for_status()
            
            account_data = DataParser.parse_account(account_res.text)
            self.display.show_index(account_data)
            return True
        except requests.RequestException as e:
            print(f"数据获取失败: {str(e)}")
            return False

    def run(self):
        """主运行逻辑"""
        if not self.handle_login():
            return
        try:
            while True:
                # 动态生成菜单选项
                menu_options = []
                if self.bill_query is not None:
                    menu_options.append("1.账单")
                menu_options.append("2.电费")
                
                menu_prompt = "\n请输入操作编号（{} q.退出）: ".format(" ".join(menu_options))
                choice = input(menu_prompt).strip().lower()
                
                if choice == 'q':
                    break
                
                if choice == '1' and self.bill_query is not None:
                    self.handle_bill_query()
                elif choice == '2':
                    self.handle_electricity_query()
                else:
                    available = [opt[0] for opt in menu_options]
                    print(f"无效输入，当前可用选项：{', '.join(available)}, q")
        finally:
            if self.session_mgr.current_user is not None:
                self.session_mgr.save_cookies(self.session_mgr.current_user)

    def handle_bill_query(self):
        try:
            # 首次查询获取总页数，并缓存第一页数据
            first_page_items, total_page = self.bill_query.query_page(1)
            
            # 动态生成输入提示
            page_input = input(f"请输入查询页数（默认1，支持1-{total_page}）: ").strip()
            page_no = int(page_input) if page_input else 1
            
            # 验证页数范围
            if not 1 <= page_no <= total_page:
                print(f"页数范围1-{total_page}")
                return
            
            # 复用第一页数据或查询指定页
            if page_no == 1:
                bill_items = first_page_items
            else:
                bill_items, total_page = self.bill_query.query_page(page_no)
            
            # 显示结果
            self.display.show_bill(bill_items, page_no, total_page)
        except ValueError:
            print("请输入有效数字")

    def handle_electricity_query(self):
        try:
            building = int(input("请输入新苑楼号（1-6）: "))
            if building not in Config.BUILDING_MAP:
                print("错误：无效的楼号")
                return
            
            room = input("请输入宿舍号（如309或4-101）: ").strip()
            # 自动补充楼层前缀
            if '-' not in room:
                room = f"{building}-{room}"
            
            result = self.electricity_query.query(building, room)
            print(f"\n{result}")
        except ValueError:
            print("错误：请输入数字形式的楼号")