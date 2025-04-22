import requests
import time
from config.config import Config
from utils.data_parser import DataParser

class BillQuery:
    def __init__(self, session):
        self.session = session
        self.retry_count = 3  # 最大重试次数
        self.retry_delay = 1  # 重试延迟（秒）

    def query_page(self, page_no):
        """
        查询指定页码的账单数据
        
        参数:
            page_no: 页码
            
        返回:
            (账单列表, 总页数)
        """
        # 执行网络请求
        for retry in range(self.retry_count):
            try:
                headers = {
                    "Referer": "https://yktepay.lixin.edu.cn/ykt/h5/bill",
                    "X-Requested-With": "XMLHttpRequest",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36"
                }

                resp = self.session.get(
                    f"https://yktepay.lixin.edu.cn/ykt/h5/loadbill.json?pageno={page_no}",
                    headers=headers,
                    timeout=Config.TIMEOUT
                )
                resp.raise_for_status()
                
                json_data = resp.json()
                if json_data.get("retcode") == 0:
                    items = DataParser.parse_bill_json(json_data)
                    total_page = json_data.get("totalpage", 1)
                    return items, total_page
                
                error_msg = json_data.get("retmsg", "未知错误")
                print(f"服务器返回错误（尝试 {retry+1}/{self.retry_count}）：CODE {json_data.get('retcode')} - {error_msg}")
                
                # 如果是认证错误或会话过期，不再重试
                if json_data.get("retcode") in [401, 403]:
                    return [], 0
                
                # 延迟后重试
                if retry < self.retry_count - 1:
                    time.sleep(self.retry_delay)
                
            except requests.JSONDecodeError:
                print(f"JSON解析失败（尝试 {retry+1}/{self.retry_count}），请检查响应数据格式")
                if retry < self.retry_count - 1:
                    time.sleep(self.retry_delay)
                    
            except requests.RequestException as e:
                print(f"请求异常（尝试 {retry+1}/{self.retry_count}）：{str(e)}")
                if retry < self.retry_count - 1:
                    time.sleep(self.retry_delay)
        
        # 所有重试都失败，返回空结果
        return [], 0