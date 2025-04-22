import pymysql
import datetime
import statistics
from typing import Dict, List, Tuple, Any

class ElectricityAnalysis:
    """电量数据分析类"""
    
    def __init__(self, host='localhost', user='root', password='123456'):
        """初始化分析类"""
        self.db_host = host
        self.db_user = user
        self.db_password = password
        
    def get_latest_query_time(self) -> str:
        """获取最新一次批量查询的时间"""
        try:
            conn = pymysql.connect(
                host=self.db_host, 
                user=self.db_user, 
                password=self.db_password,
                database='electricity_data'
            )
            cursor = conn.cursor()
            
            # 查询最新的记录时间
            cursor.execute("SELECT query_time FROM query_history ORDER BY query_time DESC LIMIT 1")
            result = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            if result:
                return result[0].strftime('%Y-%m-%d %H:%M:%S')
            return None
        except Exception as e:
            print(f"获取最新查询时间失败: {str(e)}")
            return None
    
    def get_latest_data(self) -> Tuple[Dict[str, Dict[str, float]], str]:
        """获取最新一次查询的电量数据"""
        try:
            conn = pymysql.connect(
                host=self.db_host, 
                user=self.db_user, 
                password=self.db_password,
                database='electricity_data'
            )
            cursor = conn.cursor()
            
            # 1. 获取最新的查询时间
            cursor.execute("SELECT query_time FROM query_history ORDER BY query_time DESC LIMIT 1")
            latest_time = cursor.fetchone()
            
            if not latest_time:
                cursor.close()
                conn.close()
                return {}, "未找到查询记录"
            
            latest_time = latest_time[0]
            
            # 2. 找到对应的列名
            column_name = f"e_{latest_time.strftime('%Y%m%d%H%M%S')}"
            
            # 3. 检查列是否存在
            cursor.execute(f"SHOW COLUMNS FROM electricity_history LIKE '{column_name}'")
            if not cursor.fetchone():
                cursor.close()
                conn.close()
                return {}, f"未找到对应的数据列: {column_name}"
            
            # 4. 查询所有电量数据
            cursor.execute(f"SELECT building, room, {column_name} FROM electricity_history WHERE {column_name} IS NOT NULL")
            results = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            # 5. 整理数据结构
            data = {}
            for row in results:
                building, room, electricity = row
                if building not in data:
                    data[building] = {}
                
                # 尝试将电量转换为浮点数，如果失败则跳过
                try:
                    electricity_value = float(electricity)
                    data[building][room] = electricity_value
                except (ValueError, TypeError):
                    continue
            
            return data, latest_time.strftime('%Y-%m-%d %H:%M:%S')
        
        except Exception as e:
            print(f"获取最新数据失败: {str(e)}")
            return {}, f"查询数据失败: {str(e)}"
    
    def analyze_data(self) -> str:
        """分析电量数据并返回分析结果文本"""
        data, query_time = self.get_latest_data()
        
        if not data:
            return f"分析失败: {query_time}"
        
        analysis_result = [f"电量数据分析 (查询时间: {query_time})\n"]
        
        # 计算总体数据
        all_values = []
        for building in data:
            all_values.extend(data[building].values())
        
        if not all_values:
            return "分析失败: 没有有效的电量数据"
        
        # 1. 总体分析
        avg_electricity = sum(all_values) / len(all_values)
        min_electricity = min(all_values)
        max_electricity = max(all_values)
        
        # 查找最低和最高电量的房间
        min_room = None
        max_room = None
        
        for building in data:
            for room, electricity in data[building].items():
                if electricity == min_electricity and not min_room:
                    min_room = f"{building}-{room}"
                if electricity == max_electricity and not max_room:
                    max_room = f"{building}-{room}"
        
        analysis_result.append("总体数据:")
        analysis_result.append(f"- 平均电量: {avg_electricity:.2f}度     总共 {len(all_values)} 个房间有数据")
        analysis_result.append(f"- 最低电量: {min_electricity:.2f}度 (房间: {min_room})")
        analysis_result.append(f"- 最高电量: {max_electricity:.2f}度 (房间: {max_room})")
        
        # 2. 按楼栋分析
        analysis_result.append("\n各楼栋数据:")
        
        # 按楼栋排序
        sorted_buildings = sorted(data.keys())
        
        # 两列布局处理
        for i in range(0, len(sorted_buildings), 2):
            building = sorted_buildings[i]
            building_values = list(data[building].values())
            
            if not building_values:
                continue
                
            building_avg = sum(building_values) / len(building_values)
            building_min = min(building_values)
            building_max = max(building_values)
            
            # 准备左侧楼栋信息
            left_info = f"新苑{building}号楼: 平均 {building_avg:.2f}度, 最低 {building_min:.2f}度, 最高 {building_max:.2f}度, {len(building_values)}个房间"
            
            # 如果有右侧楼栋，添加右侧信息
            if i + 1 < len(sorted_buildings):
                building2 = sorted_buildings[i + 1]
                building_values2 = list(data[building2].values())
                
                if building_values2:
                    building_avg2 = sum(building_values2) / len(building_values2)
                    building_min2 = min(building_values2)
                    building_max2 = max(building_values2)
                    
                    # 右侧楼栋信息
                    right_info = f"新苑{building2}号楼: 平均 {building_avg2:.2f}度, 最低 {building_min2:.2f}度, 最高 {building_max2:.2f}度, {len(building_values2)}个房间"
                    
                    # 合并一行显示 - 使用空格代替"|"分隔符
                    analysis_result.append(f"- {left_info}")
                    analysis_result.append(f"- {right_info}")
                else:
                    # 只有左侧信息
                    analysis_result.append(f"- {left_info}")
            else:
                # 只有左侧信息
                analysis_result.append(f"- {left_info}")
        
        # 3. 电量区间分布
        low_threshold = 10  # 低于10度视为电量紧张
        high_threshold = 100  # 高于100度视为电量充足
        
        low_count = sum(1 for e in all_values if e < low_threshold)
        medium_count = sum(1 for e in all_values if low_threshold <= e < high_threshold)
        high_count = sum(1 for e in all_values if e >= high_threshold)
        
        total_count = len(all_values)
        
        analysis_result.append("\n电量区间分布:")
        analysis_result.append(f"- 电量紧张 (<{low_threshold}度): {low_count}个房间 ({low_count/total_count*100:.1f}%)")
        analysis_result.append(f"- 电量一般 ({low_threshold}-{high_threshold}度): {medium_count}个房间 ({medium_count/total_count*100:.1f}%)")
        analysis_result.append(f"- 电量充足 (>{high_threshold}度): {high_count}个房间 ({high_count/total_count*100:.1f}%)")
        
        # 4. 楼层分析
        try:
            floor_data = {}
            for building in data:
                for room in data[building]:
                    # 从房间号提取楼层
                    if '-' in room:
                        floor = room.split('-')[0]
                        if floor not in floor_data:
                            floor_data[floor] = []
                        floor_data[floor].append(data[building][room])
            
            # 如果有楼层数据，添加到分析结果
            if floor_data:
                analysis_result.append("\n各楼层平均电量:")
                
                # 对楼层排序
                sorted_floors = sorted(floor_data.keys())
                
                # 每楼层一行
                for floor in sorted_floors:
                    floor_avg = sum(floor_data[floor]) / len(floor_data[floor])
                    analysis_result.append(f"- {floor}楼: {floor_avg:.2f}度 ({len(floor_data[floor])}个房间)")
        except Exception as e:
            analysis_result.append(f"\n楼层分析失败: {str(e)}")
        
        return "\n".join(analysis_result) 