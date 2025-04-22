import os
import sys
import csv
import requests
import pymysql
import datetime
import concurrent.futures
import time
from bs4 import BeautifulSoup
from config.config import Config

class ElectricityQuery:
    def __init__(self):
        self.room_mappings = self.load_room_mappings()
        # 用于控制查询速度的延迟
        self.query_delay = 0.2  # 查询间隔时间(秒)，适当减少
        # 默认并发线程数调整为较高值，提高查询速度
        self.max_workers = 60  # 提高到60个并发线程
        # 查询超时参数
        self.query_timeout = 8  # 保持8秒查询超时
        
        # 数据库连接参数，默认值
        self.db_host = 'localhost'
        self.db_user = 'root'
        self.db_password = '123456'

    @staticmethod
    def resource_path(relative_path):
        base_path = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    def load_room_mappings(self):
        mappings = {}
        for num, chinese in Config.BUILDING_NAME_MAP.items():
            try:
                file_path = os.path.join(Config.get_room_data_folder(), f"新苑{chinese}号楼房间数据.csv")
                if os.path.exists(file_path):
                    with open(file_path, "r", encoding="utf-8") as f:
                        reader = csv.DictReader(f)
                        mappings[num] = {row["实际房间"]: row["roomid"] for row in reader}
            except Exception as e:
                print(f"加载 {chinese} 号楼数据失败: {str(e)}")
        return mappings

    def query(self, building, room):
        try:
            roomid = self.room_mappings.get(building, {}).get(room)
            if not roomid:
                return f"未找到宿舍 {room} 的配置信息"
            
            buildid, sysid, areaid = Config.BUILDING_MAP[building]
            url = f"https://yktepay.lixin.edu.cn/ykt/h5/eleresult?sysid={sysid}&roomid={roomid}&areaid={areaid}&buildid={buildid}"
            resp = requests.get(url, timeout=Config.TIMEOUT)
            
            if resp.ok:
                soup = BeautifulSoup(resp.text, 'html.parser')
                if elem := soup.find("div", string="剩余电量"):
                    electricity_text = elem.find_next('div').text.strip()
                    # 清洗数据 - 移除"度"字
                    electricity = electricity_text.replace('度', '').strip()
                    return f"宿舍 {room} 剩余电量: {electricity}"
            return "查询失败，请稍后重试"
        except Exception as e:
            return f"查询异常: {str(e)}"
            
    def _process_room(self, args):
        """处理单个房间查询的工作函数"""
        building, room, roomid, callback, total_count, processed_count = args
        
        try:
            # 添加随机延迟，避免请求过于集中
            time.sleep(self.query_delay)
            
            buildid, sysid, areaid = Config.BUILDING_MAP[building]
            url = f"https://yktepay.lixin.edu.cn/ykt/h5/eleresult?sysid={sysid}&roomid={roomid}&areaid={areaid}&buildid={buildid}"
            
            # 调用回调函数更新进度
            if callback:
                callback(f"正在查询: {building}-{room}", total_count, processed_count)
                
            resp = requests.get(url, timeout=self.query_timeout)
            
            if resp.ok:
                soup = BeautifulSoup(resp.text, 'html.parser')
                if elem := soup.find("div", string="剩余电量"):
                    electricity_text = elem.find_next('div').text.strip()
                    # 清洗数据 - 移除"度"字
                    electricity = electricity_text.replace('度', '').strip()
                    return {
                        'building': building,
                        'room': room,
                        'electricity': electricity,
                        'status': 'success'
                    }
            
            return {
                'building': building,
                'room': room,
                'electricity': "查询失败",
                'status': 'failed'
            }
        except Exception as e:
            return {
                'building': building,
                'room': room,
                'electricity': f"查询异常: {str(e)}",
                'status': 'error'
            }

    def query_all_rooms(self, callback=None):
        """查询所有宿舍的电费并保存到数据库，使用并发提高速度"""
        results = {}
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 确保数据库存在
        self.init_database()
        
        # 准备所有查询任务
        all_tasks = []
        total_count = 0
        
        for building, rooms in self.room_mappings.items():
            results[building] = {}
            for room, roomid in rooms.items():
                all_tasks.append((building, room, roomid, callback, total_count + 1, 0))
                total_count += 1
        
        # 确保任务数量合理
        if total_count == 0:
            if callback:
                callback("未找到有效的宿舍数据，请检查配置", 1, 0)
            return {}, current_time
            
        success_count = 0
        processed_count = 0
        
        # 使用线程池执行查询，使用成员变量控制并发数
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 将任务分批次提交，避免一次性创建过多线程
            batch_size = 50  # 每批50个任务
            
            # 创建统一的结果字典
            all_futures = {}
            
            # 分批提交任务
            for i in range(0, len(all_tasks), batch_size):
                # 每批任务之间增加延迟，避免过度请求
                if i > 0:
                    time.sleep(1.5)  # 批次间隔1.5秒
                    
                batch_tasks = all_tasks[i:i+batch_size]
                batch_futures = {executor.submit(self._process_room, task): task for task in batch_tasks}
                all_futures.update(batch_futures)
            
            # 统一处理所有任务完成的结果
            for future in concurrent.futures.as_completed(all_futures):
                task = all_futures[future]
                building, room = task[0], task[1]
                
                processed_count += 1
                # 确保进度不会超过总数
                progress = min(processed_count, total_count)
                
                try:
                    result = future.result()
                    results[building][room] = result['electricity']
                    
                    # 如果查询成功，保存到数据库
                    if result['status'] == 'success':
                        success_count += 1
                        try:
                            self.save_to_database(current_time, building, room, result['electricity'])
                        except Exception as db_error:
                            print(f"保存到数据库失败: {str(db_error)}")
                    
                    # 更新进度
                    if callback:
                        callback(f"已处理: {progress}/{total_count}", total_count, progress)
                        
                except Exception as e:
                    results[building][room] = f"处理错误: {str(e)}"
                    if callback:
                        callback(f"处理房间 {building}-{room} 时出错: {str(e)}", total_count, progress)
        
        # 完成回调
        if callback:
            callback(f"查询完成，共查询{total_count}个房间，成功{success_count}个", total_count, total_count)
            
        # 保存统计数据到结果中
        result_with_stats = {
            'data': results,
            'stats': {
                'total_count': total_count,
                'success_count': success_count
            }
        }
            
        return result_with_stats, current_time
    
    def init_database(self):
        """初始化数据库和表"""
        try:
            # 连接MySQL服务器（数据库可能不存在）
            conn = pymysql.connect(host=self.db_host, user=self.db_user, password=self.db_password)
            cursor = conn.cursor()
            
            # 创建数据库（如果不存在）
            cursor.execute("CREATE DATABASE IF NOT EXISTS electricity_data")
            
            # 使用数据库
            cursor.execute("USE electricity_data")
            
            # 创建原有的表（如果不存在）- 保留向后兼容性
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS all_room (
                id INT AUTO_INCREMENT PRIMARY KEY,
                query_time DATETIME NOT NULL,
                building VARCHAR(10) NOT NULL,
                room VARCHAR(20) NOT NULL,
                electricity VARCHAR(50) NOT NULL
            )
            """)
            
            # 创建新的查询历史记录表 - 用于记录每次查询的时间
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS query_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                query_time DATETIME NOT NULL,
                description VARCHAR(100),
                UNIQUE KEY unique_query_time (query_time)
            )
            """)
            
            # 创建新的电量数据表 - 以房间为主键，每次查询为单独列
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS electricity_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                building VARCHAR(10) NOT NULL,
                room VARCHAR(20) NOT NULL,
                UNIQUE KEY unique_room (building, room)
            )
            """)
            
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"初始化数据库失败: {str(e)}")
            return False
    
    def save_to_database(self, query_time, building, room, electricity):
        """保存查询结果到数据库"""
        try:
            # 尝试将电量转换为数字格式保存（去掉"度"字）
            clean_electricity = electricity.replace('度', '').strip()
            
            conn = pymysql.connect(host=self.db_host, user=self.db_user, password=self.db_password, database='electricity_data')
            cursor = conn.cursor()
            
            # 旧方式: 插入数据到原有表
            sql = "INSERT INTO all_room (query_time, building, room, electricity) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (query_time, building, room, clean_electricity))
            
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"保存到数据库失败: {str(e)}")
            return False
            
    def save_batch_to_history_database(self, query_time, results):
        """将批量查询结果作为新列保存到历史数据库"""
        try:
            conn = pymysql.connect(host=self.db_host, user=self.db_user, password=self.db_password, database='electricity_data')
            cursor = conn.cursor()
            
            # 1. 将查询时间添加到查询历史表
            try:
                description = f"批量查询 {datetime.datetime.strptime(query_time, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M')}"
                cursor.execute("INSERT INTO query_history (query_time, description) VALUES (%s, %s)", 
                              (query_time, description))
                
                # 2. 检查electricity_history表中是否存在以查询时间命名的列
                column_name = f"e_{datetime.datetime.strptime(query_time, '%Y-%m-%d %H:%M:%S').strftime('%Y%m%d%H%M%S')}"
                
                # 检查列是否存在
                cursor.execute(f"SHOW COLUMNS FROM electricity_history LIKE '{column_name}'")
                column_exists = cursor.fetchone()
                
                # 如果列不存在，添加新列
                if not column_exists:
                    cursor.execute(f"ALTER TABLE electricity_history ADD COLUMN {column_name} VARCHAR(50)")
                
                # 3. 遍历结果并更新数据
                if isinstance(results, dict) and 'data' in results:
                    data = results['data']
                else:
                    data = results
                    
                for building, rooms in data.items():
                    for room, electricity in rooms.items():
                        # 清洗电量数据
                        if isinstance(electricity, str):
                            clean_electricity = electricity.replace('度', '').strip()
                            # 检查是否为错误消息
                            if "查询失败" in clean_electricity or "查询异常" in clean_electricity or "处理错误" in clean_electricity:
                                clean_electricity = "NULL"  # 使用NULL表示查询失败
                        else:
                            clean_electricity = "NULL"
                            
                        # 先检查房间是否存在于表中
                        cursor.execute("SELECT id FROM electricity_history WHERE building = %s AND room = %s", 
                                     (building, room))
                        room_exists = cursor.fetchone()
                        
                        if room_exists:
                            # 更新现有房间的电量值
                            if clean_electricity != "NULL":
                                cursor.execute(f"UPDATE electricity_history SET {column_name} = %s WHERE building = %s AND room = %s", 
                                             (clean_electricity, building, room))
                        else:
                            # 插入新房间记录
                            if clean_electricity != "NULL":
                                cursor.execute(f"INSERT INTO electricity_history (building, room, {column_name}) VALUES (%s, %s, %s)", 
                                             (building, room, clean_electricity))
                            else:
                                cursor.execute(f"INSERT INTO electricity_history (building, room) VALUES (%s, %s)", 
                                             (building, room))
                
                conn.commit()
                return True
            except Exception as inner_e:
                conn.rollback()
                print(f"保存批量查询结果到历史数据库失败: {str(inner_e)}")
                return False
        except Exception as e:
            print(f"连接数据库失败: {str(e)}")
            return False
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()
            if 'conn' in locals() and conn:
                conn.close()
