from flask import Flask, render_template, jsonify
import pymysql
import datetime
import sys
import os
import re
import traceback

# 添加项目根目录到系统路径，确保可以导入项目模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.analysis_electricity import ElectricityAnalysis

app = Flask(__name__)

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'elecuser',
    'password': '123456',
    'database': 'electricity_data'
}

@app.route('/')
def index():
    """渲染主页"""
    return render_template('index.html')

@app.route('/api/latest_query_time')
def get_latest_query_time():
    """获取最新的查询时间"""
    analyzer = ElectricityAnalysis(
        DB_CONFIG['host'], 
        DB_CONFIG['user'], 
        DB_CONFIG['password']
    )
    query_time = analyzer.get_latest_query_time()
    return jsonify({'query_time': query_time or "暂无查询记录"})

@app.route('/api/electricity_data')
def get_electricity_data():
    """获取电量数据"""
    analyzer = ElectricityAnalysis(
        DB_CONFIG['host'], 
        DB_CONFIG['user'], 
        DB_CONFIG['password']
    )
    data, query_time = analyzer.get_latest_data()
    
    # 处理为前端可用的格式
    formatted_data = []
    for building, rooms in data.items():
        for room, electricity in rooms.items():
            formatted_data.append({
                'building': building,
                'room': room,
                'electricity': electricity
            })
    
    # 按照电量值排序
    formatted_data.sort(key=lambda x: x['electricity'])
    
    return jsonify({
        'query_time': query_time,
        'data': formatted_data
    })

@app.route('/api/analysis')
def get_analysis():
    """获取分析结果"""
    analyzer = ElectricityAnalysis(
        DB_CONFIG['host'], 
        DB_CONFIG['user'], 
        DB_CONFIG['password']
    )
    analysis_result = analyzer.analyze_data()
    # 将分析结果拆分为行，便于前端展示
    analysis_lines = analysis_result.split('\n')
    return jsonify({
        'analysis_lines': analysis_lines
    })

@app.route('/api/query_history')
def get_query_history():
    """获取查询历史记录"""
    try:
        conn = pymysql.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database']
        )
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 获取最近10次查询历史
        cursor.execute("SELECT id, query_time, description FROM query_history ORDER BY query_time DESC LIMIT 10")
        history = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # 将datetime对象转换为字符串
        for item in history:
            item['query_time'] = item['query_time'].strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify({'history': history})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/building_data')
def get_building_data():
    """获取楼栋数据"""
    analyzer = ElectricityAnalysis(
        DB_CONFIG['host'], 
        DB_CONFIG['user'], 
        DB_CONFIG['password']
    )
    data, query_time = analyzer.get_latest_data()
    
    building_stats = []
    for building, rooms in data.items():
        if rooms:
            electricity_values = list(rooms.values())
            avg_electricity = sum(electricity_values) / len(electricity_values)
            min_electricity = min(electricity_values)
            max_electricity = max(electricity_values)
            
            building_stats.append({
                'building': building,
                'count': len(rooms),
                'average': avg_electricity,
                'min': min_electricity,
                'max': max_electricity
            })
    
    # 按照楼栋编号排序
    building_stats.sort(key=lambda x: x['building'])
    
    return jsonify({
        'query_time': query_time,
        'building_stats': building_stats
    })

@app.route('/api/history_times')
def get_history_times():
    """获取所有历史查询时间点"""
    try:
        # 添加调试日志
        print("正在获取历史查询时间点...")
        
        # 数据库连接
        conn = pymysql.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database'],
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        cursor = conn.cursor()
        
        # 检查electricity_records表是否存在
        cursor.execute("SHOW TABLES LIKE 'electricity_records'")
        table_exists = cursor.fetchone() is not None
        
        history_times = []
        
        if table_exists:
            print("找到electricity_records表，使用新方法获取时间点...")
            
            # 查询所有时间点，按分钟分组，只取每分钟的最新一条记录
            query = """
            SELECT 
                DATE_FORMAT(query_time, '%Y-%m-%d %H:%i:00') as minute_time, 
                MAX(query_time) as latest_time,
                COUNT(*) as record_count
            FROM electricity_records
            GROUP BY minute_time
            ORDER BY minute_time DESC
            """
            cursor.execute(query)
            
            minutes = cursor.fetchall()
            print(f"找到 {len(minutes)} 个不同的分钟时间点")
            
            # 对于每个分钟，获取对应的查询历史描述
            for minute_data in minutes:
                minute_time = minute_data['minute_time']
                latest_time = minute_data['latest_time']
                record_count = minute_data['record_count']
                
                # 查询该时间点对应的查询历史记录
                cursor.execute("""
                SELECT id, query_time, description FROM query_history 
                WHERE DATE_FORMAT(query_time, '%Y-%m-%d %H:%i') = DATE_FORMAT(%s, '%Y-%m-%d %H:%i')
                ORDER BY query_time DESC LIMIT 1
                """, (latest_time,))
                
                history_record = cursor.fetchone()
                
                if history_record:
                    hist_id = history_record['id']
                    query_time = history_record['query_time']
                    description = history_record['description']
                    
                    # 从datetime格式提取数字，形成timeId (YYYYMMDDHHmm)
                    if isinstance(query_time, str):
                        date_match = re.match(r'(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):\d{2}', query_time)
                        if date_match:
                            year, month, day, hour, minute = date_match.groups()
                            time_id = f"{year}{month}{day}{hour}{minute}"
                        else:
                            # 如果无法解析时间，使用一个默认格式
                            time_id = query_time.replace('-', '').replace(':', '').replace(' ', '')[:12]
                    else:
                        # 处理datetime对象
                        time_id = query_time.strftime('%Y%m%d%H%M')
                        query_time = query_time.strftime('%Y-%m-%d %H:%M:%S')
                    
                    # 返回更详细的描述信息
                    item = {
                        "time_id": time_id,
                        "query_time": query_time,
                        "description": description or f"批量查询 {minute_time[:-3]} ({record_count}条)"
                    }
                    history_times.append(item)
                    print(f"添加时间点: {query_time}, time_id={time_id}, 描述={description or '无'}, 记录数={record_count}")
        else:
            print("未找到electricity_records表，检查历史表...")
            
            # 检查electricity_history表是否存在
            cursor.execute("SHOW TABLES LIKE 'electricity_history'")
            history_table_exists = cursor.fetchone() is not None
            
            if history_table_exists:
                # 获取electricity_history表中所有以e_开头的列（历史电量数据列）
                cursor.execute("SHOW COLUMNS FROM electricity_history")
                columns = [column['Field'] for column in cursor.fetchall() if column['Field'].startswith('e_')]
                
                if not columns:
                    return jsonify({"history_times": [], "message": "没有历史数据"})
                
                # 对于每个e_列，查找对应的查询历史记录
                for column_name in columns:
                    # 从列名中提取时间字符串，例如: e_20250501223001 -> 20250501223001
                    time_str = column_name[2:]
                    
                    # 转换为标准的datetime格式
                    if len(time_str) >= 14:  # 确保时间字符串足够长
                        formatted_time = f"{time_str[0:4]}-{time_str[4:6]}-{time_str[6:8]} {time_str[8:10]}:{time_str[10:12]}:{time_str[12:14]}"
                    else:
                        # 如果时间格式不对，跳过
                        continue
                    
                    # 从datetime格式提取数字，形成timeId (YYYYMMDDHHmm)
                    date_match = re.match(r'(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):\d{2}', formatted_time)
                    if date_match:
                        year, month, day, hour, minute = date_match.groups()
                        time_id = f"{year}{month}{day}{hour}{minute}"
                    else:
                        # 如果无法解析时间，使用列名中的时间部分
                        time_id = time_str[:12]
                    
                    # 查询该时间点对应的查询历史记录
                    cursor.execute("""
                    SELECT id, query_time, description FROM query_history 
                    WHERE DATE_FORMAT(query_time, '%Y-%m-%d %H:%i') = DATE_FORMAT(%s, '%Y-%m-%d %H:%i')
                    ORDER BY query_time DESC LIMIT 1
                    """, (formatted_time,))
                    
                    history_record = cursor.fetchone()
                    description = None
                    
                    if history_record:
                        hist_id = history_record['id']
                        query_time = history_record['query_time']
                        description = history_record['description']
                        
                        # 转换datetime对象为字符串
                        if not isinstance(query_time, str):
                            query_time = query_time.strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        query_time = formatted_time
                    
                    # 计算该列中非空值的数量
                    cursor.execute(f"SELECT COUNT(*) as count FROM electricity_history WHERE {column_name} IS NOT NULL")
                    count_result = cursor.fetchone()
                    count = count_result['count'] if count_result else 0
                    
                    # 返回包含列名、查询时间和描述的对象
                    history_times.append({
                        "column_name": column_name,
                        "time_id": time_id,
                        "query_time": query_time,
                        "description": description or f"批量查询 {query_time[:-3]} ({count}条)"
                    })
        
        # 按时间倒序排序
        history_times = sorted(history_times, key=lambda x: x["query_time"], reverse=True)
        
        print(f"总共找到 {len(history_times)} 个历史时间点")
        
        conn.close()
        return jsonify({"history_times": history_times})
    
    except Exception as e:
        print(f"获取历史时间点出错: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e), "history_times": []})

@app.route('/api/history_data/<path:time_id>')
def get_history_data(time_id):
    """获取指定时间点的电量数据"""
    try:
        # 调试信息
        debug_info = {
            'raw_param': time_id,
            'time_id': time_id,
            'time_id_type': str(type(time_id).__name__)
        }
        
        print(f"请求历史数据: time_id={time_id}, 类型={type(time_id).__name__}")
        
        # 验证time_id格式
        # 支持两种格式: YYYYMMDD (8位) 或 YYYYMMDDHHmm (12位)
        if not isinstance(time_id, str):
            time_id = str(time_id)
        
        if not time_id.isdigit():
            return jsonify({
                'error': '无效的时间ID',
                'query_time': '未知时间',
                'debug_info': debug_info
            })
        
        # 设置查询时间格式
        date_format = ""
        date_filter = ""
        
        # 处理不同长度的time_id
        if len(time_id) == 8:  # YYYYMMDD
            debug_info['format'] = 'YYYYMMDD (日期)'
            year = time_id[0:4]
            month = time_id[4:6]
            day = time_id[6:8]
            formatted_date = f"{year}-{month}-{day}"
            query_time_str = f"{formatted_date} 00:00:00"
            date_format = "%Y-%m-%d"
            date_filter = f"DATE(query_time) = '{formatted_date}'"
            
        elif len(time_id) == 12:  # YYYYMMDDHHmm
            debug_info['format'] = 'YYYYMMDDHHmm (日期时间)'
            year = time_id[0:4]
            month = time_id[4:6]
            day = time_id[6:8]
            hour = time_id[8:10]
            minute = time_id[10:12]
            formatted_date = f"{year}-{month}-{day}"
            formatted_time = f"{hour}:{minute}"
            query_time_str = f"{formatted_date} {formatted_time}:00"
            date_format = "%Y-%m-%d %H:%i"
            date_filter = f"DATE_FORMAT(query_time, '%Y-%m-%d %H:%i') = '{formatted_date} {formatted_time}'"
            
        else:
            return jsonify({
                'error': f'无效的时间ID格式 (长度: {len(time_id)})',
                'query_time': '未知时间',
                'debug_info': debug_info
            })
        
        debug_info['formatted_time'] = query_time_str
        debug_info['date_filter'] = date_filter
        
        conn = pymysql.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database']
        )
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 检查electricity_records表是否存在
        cursor.execute("SHOW TABLES LIKE 'electricity_records'")
        table_exists = cursor.fetchone() is not None
        
        room_data = []
        found_time = False
        
        if table_exists:
            print(f"找到electricity_records表，开始查询: {date_filter}")
            debug_info['table'] = 'electricity_records'
            
            # 查询指定时间点的记录
            query = f"""
            SELECT 
                r.room_id,
                b.building_number as building,
                r.room_number as room,
                e.electricity
            FROM 
                electricity_records e
            JOIN 
                rooms r ON e.room_id = r.id
            JOIN 
                buildings b ON r.building_id = b.id
            WHERE 
                {date_filter}
            ORDER BY 
                b.building_number, r.room_number
            """
            
            print(f"执行SQL: {query}")
            debug_info['sql'] = query
            
            cursor.execute(query)
            records = cursor.fetchall()
            
            debug_info['record_count'] = len(records)
            print(f"查询到 {len(records)} 条记录")
            
            if records:
                # 获取实际的查询时间
                cursor.execute(f"""
                SELECT MAX(query_time) as actual_time
                FROM electricity_records
                WHERE {date_filter}
                """)
                time_result = cursor.fetchone()
                query_time = time_result['actual_time'] if time_result else query_time_str
                
                if not isinstance(query_time, str):
                    query_time = query_time.strftime('%Y-%m-%d %H:%M:%S')
                
                found_time = True
                
                # 处理查询结果，确保房间号唯一
                room_dict = {}
                for record in records:
                    room_key = f"{record['building']}-{record['room']}"
                    if room_key not in room_dict:
                        room_data.append({
                            'building': record['building'],
                            'room': record['room'],
                            'electricity': record['electricity']
                        })
                        room_dict[room_key] = True
            else:
                print(f"未找到时间 {query_time_str} 的记录")
                
        else:
            # 检查旧的表结构
            print("未找到electricity_records表，检查旧的表结构")
            debug_info['table'] = 'electricity_history (legacy)'
            
            # 构造列名
            # 根据time_id长度决定列名格式
            if len(time_id) == 8:  # YYYYMMDD
                cursor.execute(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'electricity_history' 
                AND column_name LIKE 'e_{time_id}%'
                ORDER BY column_name DESC
                LIMIT 1
                """)
                column_result = cursor.fetchone()
                
                if not column_result:
                    print(f"未找到与日期 {time_id} 匹配的列")
                    return jsonify({
                        'error': f'未找到该日期的数据',
                        'query_time': formatted_date,
                        'debug_info': debug_info
                    })
                
                column_name = column_result['column_name']
                debug_info['column_name'] = column_name
                
            elif len(time_id) == 12:  # YYYYMMDDHHmm
                # 查找最接近的列名
                cursor.execute(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'electricity_history' 
                AND column_name LIKE 'e_{time_id}%'
                ORDER BY column_name ASC
                LIMIT 1
                """)
                column_result = cursor.fetchone()
                
                if not column_result:
                    print(f"未找到与时间 {time_id} 匹配的列")
                    return jsonify({
                        'error': f'未找到该时间点的数据',
                        'query_time': f"{formatted_date} {formatted_time}",
                        'debug_info': debug_info
                    })
                
                column_name = column_result['column_name']
                debug_info['column_name'] = column_name
            
            # 从electricity_history获取数据
            cursor.execute(f"""
            SELECT 
                eh.building, 
                eh.room, 
                eh.{column_name} as electricity 
            FROM 
                electricity_history eh 
            WHERE 
                eh.{column_name} IS NOT NULL
            ORDER BY 
                eh.building, eh.room
            """)
            
            records = cursor.fetchall()
            
            debug_info['record_count'] = len(records)
            print(f"从列 {column_name} 查询到 {len(records)} 条记录")
            
            if records:
                # 尝试从列名中提取时间
                time_str = column_name[2:]  # 移除前缀 'e_'
                
                # 转换为标准时间格式
                if len(time_str) >= 14:  # e_YYYYMMDDHHmmSS
                    query_time = f"{time_str[0:4]}-{time_str[4:6]}-{time_str[6:8]} {time_str[8:10]}:{time_str[10:12]}:{time_str[12:14]}"
                else:
                    query_time = query_time_str
                
                found_time = True
                
                # 处理查询结果
                for record in records:
                    room_data.append({
                        'building': record['building'],
                        'room': record['room'],
                        'electricity': record['electricity']
                    })
            else:
                print(f"列 {column_name} 中没有非空值")
        
        cursor.close()
        conn.close()
        
        # 如果未找到任何数据，返回错误
        if not room_data:
            return jsonify({
                'error': '未找到该时间点的电量数据',
                'query_time': query_time_str if not found_time else query_time,
                'debug_info': debug_info
            })
        
        return jsonify({
            'data': room_data,
            'query_time': query_time_str if not found_time else query_time,
            'count': len(room_data),
            'debug_info': debug_info
        })
        
    except Exception as e:
        print(f"获取历史数据出错: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'error': str(e),
            'query_time': '未知时间',
            'debug_info': {
                'raw_param': time_id if 'time_id' in locals() else None,
                'exception_type': str(type(e).__name__),
                'exception': str(e)
            }
        })

@app.route('/api/debug/database_info')
def debug_database_info():
    """调试端点：获取数据库表结构和部分数据"""
    try:
        conn = pymysql.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database']
        )
        cursor = conn.cursor()
        
        # 获取数据库中所有表
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor.fetchall()]
        
        result = {
            'tables': tables,
            'table_structures': {},
            'sample_data': {}
        }
        
        # 对每个表获取结构
        for table in tables:
            cursor.execute(f"DESCRIBE {table}")
            columns = cursor.fetchall()
            result['table_structures'][table] = [
                {
                    'field': col[0],
                    'type': col[1],
                    'null': col[2],
                    'key': col[3],
                    'default': col[4],
                    'extra': col[5]
                }
                for col in columns
            ]
            
            # 获取每个表的示例数据
            cursor.execute(f"SELECT * FROM {table} LIMIT 5")
            rows = cursor.fetchall()
            
            # 获取列名
            cursor.execute(f"SHOW COLUMNS FROM {table}")
            column_names = [col[0] for col in cursor.fetchall()]
            
            # 将数据转换为字典列表
            result['sample_data'][table] = [
                dict(zip(column_names, row)) for row in rows
            ]
            
            # 如果是electricity_history表，获取所有列名
            if table == 'electricity_history':
                cursor.execute(f"SHOW COLUMNS FROM {table}")
                all_columns = [col[0] for col in cursor.fetchall()]
                result['electricity_history_columns'] = all_columns
                
                # 检查数据条数
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                result['electricity_history_count'] = cursor.fetchone()[0]
                
                # 获取动态列（电量数据列）
                dynamic_columns = [col for col in all_columns if col.startswith('e_')]
                result['dynamic_columns'] = dynamic_columns
                
                # 对每个动态列，计算非空值的数量
                non_null_counts = {}
                for col in dynamic_columns:
                    cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {col} IS NOT NULL")
                    non_null_counts[col] = cursor.fetchone()[0]
                result['dynamic_column_counts'] = non_null_counts
                
                # 获取最新的一条query_history记录
                cursor.execute("SELECT * FROM query_history ORDER BY query_time DESC LIMIT 1")
                query_row = cursor.fetchone()
                if query_row:
                    cursor.execute("SHOW COLUMNS FROM query_history")
                    query_column_names = [col[0] for col in cursor.fetchall()]
                    result['latest_query'] = dict(zip(query_column_names, query_row))
                    
                    # 从query_history提取时间戳，使用Python的strftime而不是MySQL的DATE_FORMAT
                    if 'query_time' in result['latest_query'] and isinstance(result['latest_query']['query_time'], datetime.datetime):
                        query_time = result['latest_query']['query_time']
                        expected_column = f"e_{query_time.strftime('%Y%m%d%H%M%S')}"
                        result['expected_column'] = expected_column
                        
                        # 检查该列是否存在
                        cursor.execute(f"SHOW COLUMNS FROM electricity_history LIKE '{expected_column}'")
                        result['column_exists'] = bool(cursor.fetchone())
        
        cursor.close()
        conn.close()
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/fix_history_data', methods=['POST'])
def fix_history_data():
    """修复历史电量数据问题"""
    try:
        conn = pymysql.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database']
        )
        cursor = conn.cursor()
        
        # 检查表是否存在
        cursor.execute("SHOW TABLES LIKE 'query_history'")
        if not cursor.fetchone():
            return jsonify({
                'success': False,
                'message': '查询历史表不存在，无法修复'
            })
            
        cursor.execute("SHOW TABLES LIKE 'electricity_history'")
        if not cursor.fetchone():
            return jsonify({
                'success': False,
                'message': '电量历史表不存在，无法修复'
            })
        
        # 检查是否有查询历史记录
        cursor.execute("SELECT COUNT(*) FROM query_history")
        if cursor.fetchone()[0] == 0:
            return jsonify({
                'success': False,
                'message': '查询历史表为空，无历史查询记录可以修复'
            })
            
        # 获取所有查询历史记录
        cursor.execute("SELECT id, query_time, description FROM query_history ORDER BY query_time DESC")
        query_records = cursor.fetchall()
        
        fixed_columns = 0
        skipped_columns = 0
        errors = []
        
        # 对每个查询时间尝试修复
        for record in query_records:
            query_id, query_time, description = record
            
            # 使用Python的strftime格式化时间，避免使用MySQL的DATE_FORMAT
            column_name = f"e_{query_time.strftime('%Y%m%d%H%M%S')}"
            
            # 检查是否已经有对应的列
            cursor.execute(f"SHOW COLUMNS FROM electricity_history LIKE '{column_name}'")
            
            if cursor.fetchone():
                # 列已存在，检查是否有数据
                cursor.execute(f"SELECT COUNT(*) FROM electricity_history WHERE {column_name} IS NOT NULL")
                data_count = cursor.fetchone()[0]
                
                if data_count > 0:
                    # 列已存在且有数据，跳过
                    skipped_columns += 1
                    continue
                    
            try:
                # 尝试创建或更新列
                cursor.execute(f"ALTER TABLE electricity_history ADD COLUMN IF NOT EXISTS {column_name} VARCHAR(50)")
                fixed_columns += 1
            except Exception as e:
                errors.append(f"修复列 {column_name} 时出错: {str(e)}")
        
        # 确保所有房间记录都存在于电量历史表中
        try:
            # 从 all_room 表中获取唯一的building和room组合
            cursor.execute("SELECT DISTINCT building, room FROM all_room")
            unique_rooms = cursor.fetchall()
            
            rooms_added = 0
            
            for building, room in unique_rooms:
                # 检查房间是否已存在于历史表中
                cursor.execute("SELECT COUNT(*) FROM electricity_history WHERE building = %s AND room = %s", 
                             (building, room))
                if cursor.fetchone()[0] == 0:
                    # 房间不存在，添加
                    cursor.execute("INSERT INTO electricity_history (building, room) VALUES (%s, %s)", 
                                 (building, room))
                    rooms_added += 1
        except Exception as e:
            errors.append(f"添加房间记录时出错: {str(e)}")
            
        # 如果没有错误，提交更改
        if not errors:
            conn.commit()
        else:
            conn.rollback()
            
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': len(errors) == 0,
            'message': f"修复完成: 修复了{fixed_columns}个列, 跳过了{skipped_columns}个列, 添加了{rooms_added}个房间记录",
            'errors': errors
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"修复过程出错: {str(e)}"
        })

@app.route('/api/room_history/<building>/<room>')
def get_room_history(building, room):
    """获取特定房间的历史电量数据"""
    try:
        conn = pymysql.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database']
        )
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 检查新表是否存在
        cursor.execute("SHOW TABLES LIKE 'electricity_records'")
        if cursor.fetchone():
            # 使用新表结构 - 按时间点查询
            cursor.execute("""
                SELECT 
                    CONCAT(
                        YEAR(er.query_time), '-',
                        LPAD(MONTH(er.query_time), 2, '0'), '-',
                        LPAD(DAY(er.query_time), 2, '0'), ' ',
                        LPAD(HOUR(er.query_time), 2, '0'), ':',
                        LPAD(MINUTE(er.query_time), 2, '0'), ':',
                        LPAD(SECOND(er.query_time), 2, '0')
                    ) as query_time, 
                    er.electricity 
                FROM electricity_records er
                WHERE er.building = %s AND er.room = %s
                ORDER BY er.query_time DESC
            """, (building, room))
            
            records = cursor.fetchall()
            result = []
            
            for record in records:
                try:
                    result.append({
                        'query_time': record['query_time'],
                        'electricity': float(record['electricity'])
                    })
                except (ValueError, TypeError):
                    # 跳过无效数据
                    continue
                    
            return jsonify({
                'building': building,
                'room': room,
                'history': result
            })
        else:
            # 使用旧表结构 - 保持原有逻辑
            # 获取所有电量列
            cursor.execute("SHOW COLUMNS FROM electricity_history WHERE Field LIKE 'e_%'")
            columns = cursor.fetchall()
            
            # 查询该房间的所有历史数据
            column_names = [column['Field'] for column in columns]
            if not column_names:
                return jsonify({
                    'building': building,
                    'room': room,
                    'history': []
                })
                
            query_parts = []
            for column in column_names:
                query_parts.append(f"'{column}' as col_name, {column} as electricity")
                
            query = f"""
                SELECT * FROM (
                    SELECT {', '.join(query_parts)}
                    FROM electricity_history
                    WHERE building = %s AND room = %s
                ) t
                WHERE t.electricity IS NOT NULL
            """
            
            cursor.execute(query, (building, room))
            history_records = cursor.fetchall()
            
            # 转换为前端友好格式
            result = []
            for record in history_records:
                col_name = record['col_name']
                electricity = record['electricity']
                
                # 从列名提取时间
                time_str = col_name[2:]  # 去掉e_前缀
                
                # 格式化时间字符串
                try:
                    year = time_str[0:4]
                    month = time_str[4:6]
                    day = time_str[6:8]
                    hour = time_str[8:10]
                    minute = time_str[10:12]
                    second = time_str[12:14] if len(time_str) >= 14 else "00"
                    
                    query_time = f"{year}-{month}-{day} {hour}:{minute}:{second}"
                    
                    try:
                        electricity_value = float(electricity)
                        result.append({
                            'query_time': query_time,
                            'electricity': electricity_value
                        })
                    except (ValueError, TypeError):
                        # 跳过无效数据
                        continue
                except Exception:
                    # 跳过无效时间格式
                    continue
                    
            # 按时间排序
            result.sort(key=lambda x: x['query_time'], reverse=True)
            
            return jsonify({
                'building': building,
                'room': room,
                'history': result
            })
        
        cursor.close()
        conn.close()
    except Exception as e:
        return jsonify({
            'error': str(e),
            'building': building,
            'room': room
        })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0') 