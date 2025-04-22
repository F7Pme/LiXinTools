import time
from collections import defaultdict, Counter
import concurrent.futures
import gc
from PySide6.QtCore import Qt, Signal, QObject, QThread
from gui.LoginWindow import log_window

class BillAnalysisWorker(QObject):
    """账单分析工作线程信号对象"""
    finished = Signal(dict)
    progress = Signal(int, int)  # 当前页码，总页数
    log_signal = Signal(str, str, str)  # 发送日志信号：消息，类型，额外信息
    
    def __init__(self, bill_query):
        super().__init__()
        self.bill_query = bill_query
        self.stop_flag = False
        self.max_workers = 12  # 增加并行查询的最大线程数
        
    def write_log(self, message, level="INFO", extra_info=""):
        """发送日志信号，确保日志在主线程中处理"""
        # 直接使用信号发送日志
        self.log_signal.emit(message, level, extra_info)
        
    def query_page_with_log(self, page):
        """查询指定页码的账单，并记录日志"""
        try:
            self.write_log(f"查询账单第 {page} 页", "INFO")
                
            items, _ = self.bill_query.query_page(page)
            
            self.write_log(f"第 {page} 页查询完成，获取 {len(items)} 条记录", "INFO")
                
            return items
        except Exception as e:
            self.write_log(f"查询第 {page} 页失败: {str(e)}", "ERROR")
            return []
        
    def run(self):
        """执行查询所有账单并分析操作"""
        try:
            # 记录开始日志
            self.write_log("开始查询全部账单并分析", "INFO")
            
            # 先查询第一页获取总页数
            start_time = time.time()
            items, total_pages = self.bill_query.query_page(1)
            
            self.write_log(f"获取到总共 {total_pages} 页账单数据", "INFO")
            
            # 发送进度信号
            self.progress.emit(1, total_pages)
            
            # 存储所有账单 - 优化为直接使用列表而不是复制
            all_items = []
            all_items.extend(items)
            
            # 主动释放不需要的引用以减少内存占用
            del items
            
            # 尝试强制垃圾回收
            gc.collect()
            
            if total_pages > 1:
                # 增加批次大小以减少循环次数，提高效率
                batch_size = 15  # 增加到15
                # 为避免一次性创建过多线程，设置每批最大线程数
                max_batch_threads = min(self.max_workers, 15)  # 限制每批最多15个线程
                
                for batch_start in range(2, total_pages + 1, batch_size):
                    if self.stop_flag:
                        break
                        
                    # 计算当前批次结束页
                    batch_end = min(batch_start + batch_size - 1, total_pages)
                    
                    # 只查询当前批次的页面
                    pages_to_query = list(range(batch_start, batch_end + 1))
                    batch_results = []
                    
                    # 使用线程池并行处理当前批次
                    with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(pages_to_query), max_batch_threads)) as executor:
                        # 提交当前批次的查询任务
                        future_to_page = {executor.submit(self.query_page_with_log, page): page for page in pages_to_query}
                        
                        # 处理完成的查询任务
                        completed_in_batch = 0
                        for future in concurrent.futures.as_completed(future_to_page):
                            if self.stop_flag:
                                for f in future_to_page:
                                    if not f.done():
                                        f.cancel()
                                break
                                
                            page = future_to_page[future]
                            try:
                                page_items = future.result()
                                batch_results.extend(page_items)
                                
                                # 更新已完成页数
                                completed_in_batch += 1
                                total_completed = batch_start - 2 + completed_in_batch
                                self.progress.emit(total_completed + 1, total_pages)  # +1 因为第一页已经完成
                                
                                # 减少日志输出频率，只在关键节点记录
                                if total_completed % 5 == 0 or total_completed + 1 == total_pages:
                                    self.write_log(f"已完成 {total_completed + 1}/{total_pages} 页查询", "INFO")
                                
                            except Exception as e:
                                self.write_log(f"处理第 {page} 页数据失败: {str(e)}", "ERROR")
                    
                    # 将当前批次结果添加到总结果中
                    all_items.extend(batch_results)
                    
                    # 清理当前批次数据减少内存占用
                    del batch_results
                    gc.collect()
            
            query_time = time.time() - start_time
            self.write_log(f"账单查询完成，用时 {query_time:.2f} 秒，共获取 {len(all_items)} 条记录，开始分析...", "INFO")
            
            # 分析数据
            analysis_start_time = time.time()
            
            # 使用优化后的分析方法，减少内存占用
            analysis_result = BillAnalyzer.analyze(all_items, self)
            
            # 主动释放原始数据
            all_items = []
            gc.collect()
            
            analysis_time = time.time() - analysis_start_time
            
            self.write_log(f"账单分析完成，分析用时 {analysis_time:.2f} 秒，总用时 {(query_time + analysis_time):.2f} 秒，共分析 {analysis_result.get('total_count', 0)} 条记录", "INFO")
            
            # 发送完成信号并附带分析结果
            self.finished.emit(analysis_result)
            
        except Exception as e:
            # 发生异常时记录日志并返回空结果
            error_msg = f"账单分析发生错误: {str(e)}"
            self.write_log(error_msg, "ERROR")
            self.finished.emit({})
    
    def stop(self):
        """设置停止标志，中断查询"""
        self.stop_flag = True
        self.write_log("用户取消账单分析操作", "INFO")


class BillAnalyzer:
    """账单数据分析器"""
    
    @staticmethod
    def analyze(bills, worker=None):
        """
        分析账单数据
        :param bills: 账单列表
        :param worker: 工作线程对象，用于记录日志
        :return: 分析结果字典
        """
        # 记录分析开始
        if worker:
            worker.write_log(f"开始分析 {len(bills)} 条账单数据", "INFO")
            
        if not bills:
            if worker:
                worker.write_log("没有账单数据可分析", "WARNING")
                
            return {
                "total_count": 0,
                "total_amount": 0,
                "date_stats": {},
                "type_stats": {},
                "daily_stats": {},
                "status_stats": {},
                "raw_data": []
            }
        
        # 存储分析结果 - 优化存储方式，不保存原始数据以减少内存占用
        result = {
            "total_count": len(bills),  # 总交易数
            "total_amount": 0,  # 总金额
            "type_stats": defaultdict(int),  # 每种交易类型的次数
            "type_amount": defaultdict(float),  # 每种交易类型的金额
            "date_stats": defaultdict(int),  # 每天的交易次数
            "daily_stats": defaultdict(float),  # 每天的交易金额
            "status_stats": Counter(),  # 交易状态统计
            "raw_data": bills  # 保存原始数据以便翻页
        }
        
        # 优化：预处理数据，提取公共操作以减少循环内部操作
        for i, bill in enumerate(bills):
            # 解析金额 - 优化字符串处理
            amount_str = bill.get("amount", "￥0.00")
            amount = float(amount_str.replace("￥", "").replace(",", ""))
            
            # 累加总金额
            result["total_amount"] += amount
            
            # 获取交易类型并统计
            trans_type = bill.get("type", "未知")
            result["type_stats"][trans_type] += 1
            result["type_amount"][trans_type] += amount
            
            # 获取交易日期（只保留年月日）
            time_str = bill.get("time", "")
            date_str = time_str.split(" ")[0] if " " in time_str else "未知日期"
            result["date_stats"][date_str] += 1
            result["daily_stats"][date_str] += amount
            
            # 统计交易状态
            status = bill.get("status", "未知")
            result["status_stats"][status] += 1
            
            # 每处理1000条记录报告一次进度
            if worker and (i+1) % 1000 == 0:
                worker.write_log(f"已分析 {i+1}/{len(bills)} 条记录", "INFO")
        
        # 记录分析进度
        if worker:
            worker.write_log(f"已统计 {len(bills)} 条交易数据", "INFO")
        
        # 将默认字典转换为普通字典
        result["type_stats"] = dict(result["type_stats"])
        result["type_amount"] = dict(result["type_amount"])
        result["date_stats"] = dict(result["date_stats"])
        result["daily_stats"] = dict(result["daily_stats"])
        result["status_stats"] = dict(result["status_stats"])
        
        # 记录分析完成
        if worker:
            worker.write_log(f"数据分析完成，总金额：￥{result['total_amount']:.2f}", "INFO")
            
        return result 