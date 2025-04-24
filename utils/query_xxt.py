import requests
from config.config import Config
from utils.data_parser import DataParser

class XxtQuery:
    """学习通查询工具
    
    用于获取学习通相关数据，包括课程列表、作业信息等
    """
    
    def __init__(self, session):
        """初始化学习通查询工具
        
        Args:
            session (requests.Session): 一个已登录的会话对象
        """
        self.session = session
        self.original_headers = session.headers.copy()
        self.is_logged_in = False  # 添加登录状态标志
    
    def _set_xxt_headers(self):
        """设置请求学习通的headers"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Linux; Android 9; SKW-A0 Build/PQ3B.190801.04011825; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/91.0.4472.114 Mobile Safari/537.36 SuperApp',
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Accept': 'text/html, */*; q=0.01',
        })
    
    def _restore_headers(self):
        """恢复原始headers"""
        self.session.headers = self.original_headers.copy()
    
    def login_to_xxt(self):
        """登录到学习通并返回登录后的HTML内容"""
        try:
            # 如果已登录，直接返回成功标志
            if self.is_logged_in:
                try:
                    from gui.LoginWindow import log_window
                    if log_window:
                        log_window.log("已登录学习通，不需要重新登录", "INFO")
                except ImportError:
                    pass
                return "已登录状态"
                
            # 保存原始headers
            original_headers = self.session.headers.copy()
            
            # 设置适合学习通的headers
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Linux; Android 9; SKW-A0 Build/PQ3B.190801.04011825; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/91.0.4472.114 Mobile Safari/537.36 SuperApp',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'X-Requested-With': 'com.supwisdom.lixin'
            })
            
            # 第一步：访问学习通SSO入口
            try:
                from gui.LoginWindow import log_window
                if log_window:
                    log_window.log("正在请求学习通SSO入口...", "INFO")
            except ImportError:
                pass
            resp1 = self.session.get("http://lixin.fysso.chaoxing.com/sso/lixinnew", allow_redirects=True)
            
            # 如果已经是登录状态，可能直接跳转到学习通首页
            if "lixin.fanya.chaoxing.com/portal" in resp1.url:
                try:
                    from gui.LoginWindow import log_window
                    if log_window:
                        log_window.log("已登录状态，直接获取学习通页面", "INFO")
                except ImportError:
                    pass
                self.is_logged_in = True  # 设置登录标志
                return resp1.text
            
            # 第二步：我们可能需要通过CAS登录
            if "cas.paas.lixin.edu.cn/cas/login" in resp1.url:
                try:
                    from gui.LoginWindow import log_window
                    if log_window:
                        log_window.log("需要CAS登录...", "INFO")
                except ImportError:
                    pass
                
                # 从当前会话中提取id_token，通常在Cookie中或请求头中
                id_token = None
                for cookie in self.session.cookies:
                    if cookie.name == "userToken" or cookie.name == "TGC":
                        id_token = cookie.value
                        break
                
                if not id_token:
                    # 如果找不到token，需要重新登录获取
                    raise Exception("未找到有效的登录凭证，请重新登录")
                    
                # 构造CAS登录URL
                service_url = "https://fysso.chaoxing.com/sso/lixinnew"
                cas_url = f"https://cas.paas.lixin.edu.cn/cas/login?idToken={id_token}&service={service_url}"
                
                # 请求CAS登录
                resp2 = self.session.get(cas_url, allow_redirects=True)
                
                # 检查是否成功跳转到学习通
                if "lixin.fanya.chaoxing.com" not in resp2.url:
                    raise Exception(f"CAS登录失败，当前URL: {resp2.url}")
                
                # 设置登录标志
                self.is_logged_in = True
                
                # 返回最终页面内容
                return resp2.text
            
            # 如果已经在学习通页面，直接返回内容
            try:
                from gui.LoginWindow import log_window
                if log_window:
                    log_window.log("已成功跳转到学习通", "INFO")
            except ImportError:
                pass
            self.is_logged_in = True  # 设置登录标志
            return resp1.text
            
        except Exception as e:
            try:
                from gui.LoginWindow import log_window
                if log_window:
                    log_window.log(f"学习通登录失败: {str(e)}", "ERROR")
            except ImportError:
                pass
            self.is_logged_in = False  # 设置登录失败标志
            return f"<html><body><h1>登录失败</h1><p>{str(e)}</p></body></html>"
        finally:
            # 恢复原始headers
            self.session.headers = original_headers
    
    def get_courses(self):
        """获取学习通课程列表
        
        Returns:
            list: 课程信息列表，解析失败则返回空列表
            str: 原始HTML响应，如果需要进一步处理
        """
        try:
            # 设置请求头
            self._set_xxt_headers()
            
            try:
                from gui.LoginWindow import log_window
                if log_window:
                    log_window.log("正在获取学习通课程列表...", "INFO")
            except ImportError:
                pass
            
            # 检查登录状态，如果未登录则进行登录
            if not self.is_logged_in:
                self.login_to_xxt()
                if not self.is_logged_in:
                    raise Exception("登录失败，无法获取课程列表")
            
            # 访问课程列表数据接口
            course_data = {
                'courseType': '1',
                'courseFolderId': '0',
                'query': '',
                'pageHeader': '-1',
                'single': '0',
                'superstarClass': '0'
            }
            
            resp = self.session.post(
                "https://mooc2-ans.chaoxing.com/mooc2-ans/visit/courselistdata",
                data=course_data,
                timeout=Config.TIMEOUT
            )
            
            if not resp.ok:
                raise Exception(f"获取课程列表失败，状态码：{resp.status_code}")
            
            # 解析课程数据
            courses = DataParser.parse_xxt_courses(resp.text)
            
            return courses, resp.text
            
        except Exception as e:
            try:
                from gui.LoginWindow import log_window
                if log_window:
                    log_window.log(f"获取学习通课程列表失败: {str(e)}", "ERROR")
            except ImportError:
                pass
            return [], f"<html><body><h1>获取课程列表失败</h1><p>{str(e)}</p></body></html>"
        finally:
            # 恢复原始headers
            self._restore_headers()
    
    def get_notices(self):
        """获取学习通作业和通知列表
        
        Returns:
            list: 通知信息列表，解析失败则返回空列表
            str: 原始JSON响应，如果需要进一步处理
        """
        try:
            # 设置请求头
            self._set_xxt_headers()
            
            try:
                from gui.LoginWindow import log_window
                if log_window:
                    log_window.log("正在获取学习通作业和通知列表...", "INFO")
            except ImportError:
                pass
            
            # 检查登录状态，如果未登录则进行登录
            if not self.is_logged_in:
                login_result = self.login_to_xxt()
                if "登录失败" in login_result or not self.is_logged_in:
                    raise Exception("获取通知前请先登录学习通")
            
            # 访问通知列表接口
            notice_data = {
                'type': '2',  # 2表示收件箱
                'notice_type': '',
                'lastValue': '',
                'sort': '',
                'folderUUID': '',
                'kw': '',
                'startTime': '',
                'endTime': '',
                'gKw': '',
                'gName': '',
                'year': '2025',  # 当前年份
                'tag': '',
                'fidsCode': '',
                'queryFolderNoticePrevYear': '0'
            }
            
            # 设置更精确的头部信息
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Origin': 'https://notice.chaoxing.com',
                'Referer': 'https://notice.chaoxing.com/pc/notice/myNotice',
                'X-Requested-With': 'XMLHttpRequest',
            }
            
            # 更新当前会话的headers
            original_headers = self.session.headers.copy()
            self.session.headers.update(headers)
            
            resp = self.session.post(
                "https://notice.chaoxing.com/pc/notice/getNoticeList",
                data=notice_data,
                timeout=Config.TIMEOUT
            )
            
            # 恢复原始headers
            self.session.headers = original_headers
            
            if not resp.ok:
                raise Exception(f"获取通知列表失败，状态码：{resp.status_code}")
            
            # 解析通知数据
            notices = DataParser.parse_xxt_notices(resp.text)
            
            return notices, resp.text
            
        except Exception as e:
            try:
                from gui.LoginWindow import log_window
                if log_window:
                    log_window.log(f"获取学习通通知列表失败: {str(e)}", "ERROR")
            except ImportError:
                pass
            return [], f"{{'error': '{str(e)}'}}"
        finally:
            # 恢复原始headers
            self._restore_headers()
    
    def get_course_detail(self, course_id, clazz_id, person_id):
        """获取课程详情
        
        Args:
            course_id (str): 课程ID
            clazz_id (str): 班级ID
            person_id (str): 个人ID
        
        Returns:
            str: 课程详情HTML
        """
        try:
            # 设置请求头
            self._set_xxt_headers()
            
            # 检查登录状态，如果未登录则进行登录
            if not self.is_logged_in:
                self.login_to_xxt()
                if not self.is_logged_in:
                    raise Exception("登录失败，无法获取课程详情")
            
            # 构造课程详情URL
            url = f"https://mooc1.chaoxing.com/visit/stucoursemiddle?courseid={course_id}&clazzid={clazz_id}&cpi={person_id}&ismooc2=1"
            
            # 发送请求
            resp = self.session.get(url, timeout=Config.TIMEOUT)
            resp.raise_for_status()
            
            return resp.text
            
        except Exception as e:
            # 使用日志窗口记录错误，而不是打印到控制台
            try:
                from gui.LoginWindow import log_window
                if log_window:
                    log_window.log(f"获取课程详情失败: {str(e)}", "ERROR")
            except ImportError:
                pass
            return f"<html><body><h1>获取课程详情失败</h1><p>{str(e)}</p></body></html>"
        finally:
            # 恢复原始headers
            self._restore_headers() 