import os
import json
import requests
import datetime
import re
from config.config import Config
from utils.query_xxt import XxtQuery

class SessionManager:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": Config.USER_AGENT})
        self.current_user = None
        self.xxt_query = None  # 学习通查询工具实例
        self.user_avatar_url = None  # 用户头像URL
        self.user_name = None  # 用户名称

    def load_cookies(self):
        """加载所有账户的Cookie数据"""
        if os.path.exists(Config.COOKIE_FILE):
            try:
                with open(Config.COOKIE_FILE, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                print("警告：Cookie文件异常")
        return {}

    def save_cookies(self, user_id):
        """保存当前会话到指定用户ID"""
        os.makedirs(os.path.dirname(Config.COOKIE_FILE), exist_ok=True)
        all_data = self.load_cookies()
        all_data[user_id] = {
            "cookies": requests.utils.dict_from_cookiejar(self.session.cookies),
            "last_update": datetime.datetime.now().isoformat()
        }
        with open(Config.COOKIE_FILE, "w") as f:
            json.dump(all_data, f, indent=2)
        print(f"[√] 账户 {user_id} 的会话已保存")

    def validate_session(self):
        """验证当前会话是否有效"""
        try:
            resp = self.session.get(
                "https://yktepay.lixin.edu.cn/ykt/h5/index",
                timeout=Config.TIMEOUT//2
            )
            return resp.ok and "一卡通" in resp.text
        except requests.RequestException:
            return False
    
    def create_new_session(self):
        """创建新会话并返回用户ID"""
        try:
            username = input("请输入一卡通账号: ").strip()
            password = input("请输入密码: ").strip()
            if not (username and password):
                print("账号密码不能为空")
                return None
                
            if self.login_with_credentials(username, password):
                self.current_user = username
                self.save_cookies(username)
                return username
            return None
        except Exception as e:
            print(f"[!] 登录失败: {str(e)}")
            return None

        
    
    def login_with_credentials(self, username, password):
        # 清除现有会话数据
        self.session.cookies.clear()
        self.session.headers.clear()
        original_headers = self.session.headers.copy()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Linux; Android 9; SKW-A0 Build/PQ3B.190801.04011825; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/91.0.4472.114 Mobile Safari/537.36 SWSuperApp/2.0.4',
            'X-Device-Info': 'BlackSharkSKW-A01.9.9.81096',
            'Accept': 'application/json, text/plain, */*'
        })
        original_headers = self.session.headers.copy()
        try:
            # 密码登录获取idToken
            login_params = {
                'username': username,
                'password': password,
                'appId': 'com.supwisdom.lixin',
                'deviceId': 'Z/ezCvRHWboDAN/7421UuQlV',
                'osType': 'android'
            }
            login_resp = self.session.post(
                'https://cas.paas.lixin.edu.cn/token/password/passwordLogin',
                params=login_params
            )
            login_resp.raise_for_status()
            
            if login_resp.json().get('code') != 0:
                raise Exception(f'登录失败: {login_resp.text}')
            
            id_token = login_resp.json()['data']['idToken']
            print(f"[√] 成功获取id_token: {id_token[:20]}...")

            # CAS跳转获取会话
            service_url = 'https://yktepay.lixin.edu.cn/ykt/sso/login.jsp?targetUrl=base64aHR0cHM6Ly95a3RlcGF5LmxpeGluLmVkdS5jbi95a3QvaDUvaW5kZXg='
            cas_url = f'https://cas.paas.lixin.edu.cn/cas/login?idToken={id_token}&service={service_url}'
            
            # 执行自动跳转
            resp = self.session.get(cas_url, allow_redirects=True)
            if 'ykt/h5/index' not in resp.url:
                raise Exception("CAS跳转验证失败")
                
            print("[√] 一卡通会话创建成功")
            
            # 初始化学习通查询工具
            self.xxt_query = XxtQuery(self.session)
            
            return True

        except Exception as e:
            raise Exception(f"登录流程异常: {str(e)}")
        finally:
            # 恢复原始headers
            self.session.headers = original_headers
            
    def login_to_xxt(self):
        """登录到学习通并返回登录后的HTML内容"""
        # 确保XxtQuery实例已创建
        if self.xxt_query is None:
            self.xxt_query = XxtQuery(self.session)
        
        # 调用XxtQuery的登录方法
        return self.xxt_query.login_to_xxt()
            
    def get_xxt_courses(self):
        """获取学习通课程列表"""
        # 确保XxtQuery实例已创建
        if self.xxt_query is None:
            self.xxt_query = XxtQuery(self.session)
        
        # 调用XxtQuery的获取课程方法
        courses, html = self.xxt_query.get_courses()
        return html  # 保持与原有接口一致，返回HTML

    def get_user_avatar_url(self):
        """获取学习通用户头像URL和用户名"""
        try:
            # 访问学习通门户页面
            response = self.session.get("https://lixin.fanya.chaoxing.com/portal", timeout=Config.TIMEOUT)
            response.raise_for_status()
            
            # 使用正则表达式提取头像URL和用户名
            avatar_pattern = r'<a class="log_tit".*?>\s*<img src="(http://photo\.chaoxing\.com/p/\d+_\d+)"/>(.*?)\s*</a>'
            match = re.search(avatar_pattern, response.text)
            
            if match:
                self.user_avatar_url = match.group(1)
                self.user_name = match.group(2).strip()
                # 使用日志窗口记录成功信息
                try:
                    from gui.LoginWindow import log_window
                    if log_window:
                        log_window.log(f"成功获取用户头像: {self.user_avatar_url}", "INFO")
                        log_window.log(f"用户名: {self.user_name}", "INFO")
                except ImportError:
                    pass
                return self.user_avatar_url, self.user_name
            else:
                # 使用日志窗口记录警告信息
                try:
                    from gui.LoginWindow import log_window
                    if log_window:
                        log_window.log("未能找到用户头像", "WARNING")
                except ImportError:
                    pass
                return None, None
        except Exception as e:
            # 使用日志窗口记录错误信息
            try:
                from gui.LoginWindow import log_window
                if log_window:
                    log_window.log(f"获取用户头像失败: {str(e)}", "ERROR")
            except ImportError:
                pass
            return None, None