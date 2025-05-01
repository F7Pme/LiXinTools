from flask import Flask, render_template, jsonify
import pymysql
import datetime
import sys
import os

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
        conn = pymysql.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database']
        )
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        # 调试信息
        debug_info = {}
        
        # 统计记录总数
        cursor.execute("SELECT COUNT(*) AS count FROM electricity_records")
        result = cursor.fetchone()
        record_count = result['count'] if result else 0
        debug_info['total_records'] = record_count
        
        print(f"开始查询历史时间点，共有 {record_count} 条记录")
        
        # 按更细粒度的时间分组（年月日时分），而不是只按日期
        cursor.execute("""
            SELECT 
                DATE_FORMAT(query_time, '%Y%m%d%H%i') AS time_id,
                DATE_FORMAT(query_time, '%Y-%m-%d %H:%i') AS formatted_time,
                COUNT(*) AS record_count,
                MAX(query_time) AS latest_time
            FROM 
                electricity_records
            GROUP BY 
                time_id, formatted_time
            ORDER BY 
                time_id DESC
            LIMIT 100
        """)
        
        time_points = cursor.fetchall()
        debug_info['query_result_count'] = len(time_points)
        print(f"查询到 {len(time_points)} 个不同的时间点")
        
        if not time_points:
            print("没有找到任何时间点记录")
            return jsonify({
                'history_times': [],
                'debug_info': debug_info,
                'error': '没有找到任何时间点记录'
            })
        
        # 处理查询结果
        valid_times = []
        
        for point in time_points:
            time_id = point['time_id']          # 格式：YYYYMMDDHHmm
            formatted_time = point['formatted_time']  # 格式：YYYY-MM-DD HH:mm
            record_count = point['record_count']
            
            # 确保time_id是一个字符串并且不是'undefined'
            if time_id == 'undefined' or time_id is None:
                print(f"警告：发现无效的time_id: {time_id}")
                continue
                
            time_id_str = str(time_id)
            
            # 确保time_id不为undefined
            time_record = {
                'time_id': time_id_str,
                'query_time': formatted_time,
                'description': f"电量记录 ({record_count}条)",
                'record_count': record_count,
                'id': 0
            }
            
            print(f"时间点: time_id={time_id_str}, formatted_time={formatted_time}, 记录数={record_count}")
            
            # 尝试从query_history找到对应的描述
            try:
                # 使用时间范围查询，匹配同一分钟内的查询历史
                minute_start = formatted_time + ":00"
                minute_end = formatted_time + ":59"
                
                cursor.execute("""
                    SELECT id, query_time, description 
                    FROM query_history 
                    WHERE query_time BETWEEN %s AND %s
                    ORDER BY query_time DESC
                    LIMIT 1
                """, (minute_start, minute_end))
                
                history_record = cursor.fetchone()
                
                # 如果找到了匹配的查询历史记录，更新描述信息
                if history_record:
                    time_record['id'] = history_record['id']
                    
                    # 使用更精确的时间
                    if history_record['query_time']:
                        time_record['query_time'] = history_record['query_time'].strftime('%Y-%m-%d %H:%M:%S')
                    
                    if history_record['description']:
                        time_record['description'] = f"{history_record['description']} ({record_count}条)"
                    print(f"  找到查询历史记录: id={history_record['id']}, 描述={history_record['description']}")
            except Exception as qh_error:
                debug_info['query_history_error'] = str(qh_error)
                print(f"  查询历史记录出错: {str(qh_error)}")
            
            valid_times.append(time_record)
            
        cursor.close()
        conn.close()
        
        # 打印返回的数据结构示例
        if valid_times:
            print("返回的第一个时间点数据示例:")
            print(f"  time_id = {valid_times[0]['time_id']}")
            print(f"  query_time = {valid_times[0]['query_time']}")
            print(f"  description = {valid_times[0]['description']}")
        
        print(f"共返回 {len(valid_times)} 个有效时间点")
        
        # 返回结果
        result = {
            'history_times': valid_times,
            'count': len(valid_times),
            'debug_info': debug_info
        }
        
        # 返回结果
        return jsonify(result)
        
    except Exception as e:
        # 捕获并返回详细错误信息
        print(f"获取历史时间点出错: {str(e)}")
        error_info = {
            'error': str(e),
            'location': 'get_history_times',
            'type': str(type(e))
        }
        
        # 如果是可追踪的错误，添加行号信息
        if hasattr(e, '__traceback__'):
            tb = e.__traceback__
            while tb.tb_next:
                tb = tb.tb_next
            error_info['line'] = tb.tb_lineno
            
        return jsonify({
            'error': str(e),
            'history_times': [],
            'debug_info': error_info
        })

@app.route('/api/history_data/<time_id>')
def get_history_data(time_id):
    """获取指定时间点的电量数据"""
    try:
        print(f"收到请求：/api/history_data/{time_id}")
        
        conn = pymysql.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database']
        )
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 调试信息
        debug_info = {
            'time_id': time_id,
            'time_id_type': type(time_id).__name__
        }
        
        # 验证time_id
        if not time_id or time_id == 'undefined' or time_id == 'null':
            print(f"无效的时间ID: {time_id}")
            return jsonify({
                'error': '无效的时间ID',
                'query_time': '未知时间',
                'debug_info': debug_info
            })
            
        # 确保time_id是字符串类型
        time_id = str(time_id).strip()
        debug_info['cleaned_time_id'] = time_id
        
        # 处理时间ID
        try:
            print(f"处理时间ID: {time_id}, 长度: {len(time_id)}, 是数字: {time_id.isdigit()}")
            
            # 验证time_id格式 - 支持两种格式：YYYYMMDD 或 YYYYMMDDHHmm
            if len(time_id) == 8 and time_id.isdigit():
                # 按日期查询 - YYYYMMDD格式
                year = time_id[0:4]
                month = time_id[4:6]
                day = time_id[6:8]
                
                # 构建查询条件和显示时间
                formatted_date = f"{year}-{month}-{day}"
                debug_info['formatted_date'] = formatted_date
                print(f"按日期查询：{formatted_date}")
                
                # 查询该日期的所有数据
                cursor.execute("""
                    SELECT building, room, electricity, 
                           DATE_FORMAT(query_time, '%Y-%m-%d %H:%i:%s') AS query_time
                    FROM electricity_records
                    WHERE DATE(query_time) = %s
                    ORDER BY query_time DESC
                """, (formatted_date,))
                
                # 设置显示时间为该天
                display_time = formatted_date
                debug_info['query_type'] = 'by_date'
                
            elif len(time_id) == 12 and time_id.isdigit():
                # 按时间点查询 - YYYYMMDDHHmm格式
                year = time_id[0:4]
                month = time_id[4:6]
                day = time_id[6:8]
                hour = time_id[8:10]
                minute = time_id[10:12]
                
                # 构建查询条件和显示时间
                formatted_datetime = f"{year}-{month}-{day} {hour}:{minute}"
                debug_info['formatted_datetime'] = formatted_datetime
                print(f"按时间点查询：{formatted_datetime}")
                
                # 查询指定分钟的数据
                cursor.execute("""
                    SELECT building, room, electricity, 
                           DATE_FORMAT(query_time, '%Y-%m-%d %H:%i:%s') AS query_time
                    FROM electricity_records
                    WHERE DATE_FORMAT(query_time, '%%Y%%m%%d%%H%%i') = %s
                    ORDER BY query_time DESC
                """, (time_id,))
                
                # 设置显示时间为该分钟
                display_time = formatted_datetime
                debug_info['query_type'] = 'by_minute'
                
            else:
                # 尝试兼容处理 - 可能前端传递了非标准格式
                print(f"非标准时间ID格式: {time_id}")
                
                # 如果time_id包含-或:，可能是格式化的日期时间字符串
                if '-' in time_id:
                    try:
                        # 尝试提取日期部分
                        date_parts = time_id.split(' ')[0].split('-')
                        if len(date_parts) == 3:
                            year, month, day = date_parts
                            # 构建YYYYMMDD格式
                            date_id = f"{year}{month}{day}"
                            if len(date_id) == 8 and date_id.isdigit():
                                print(f"从日期字符串提取日期ID: {date_id}")
                                formatted_date = f"{year}-{month}-{day}"
                                
                                # 查询该日期的所有数据
                                cursor.execute("""
                                    SELECT building, room, electricity, 
                                           DATE_FORMAT(query_time, '%Y-%m-%d %H:%i:%s') AS query_time
                                    FROM electricity_records
                                    WHERE DATE(query_time) = %s
                                    ORDER BY query_time DESC
                                """, (formatted_date,))
                                
                                display_time = formatted_date
                                debug_info['query_type'] = 'by_date_string'
                                debug_info['extracted_date_id'] = date_id
                            else:
                                raise ValueError("无法提取有效的日期")
                        else:
                            raise ValueError("日期格式错误")
                    except Exception as e:
                        debug_info['date_extraction_error'] = str(e)
                        raise ValueError(f"时间ID格式不正确: {time_id}")
                else:
                    raise ValueError(f"时间ID格式不正确，应为8位(YYYYMMDD)或12位(YYYYMMDDHHmm)数字: {time_id}")
            
            rows = cursor.fetchall()
            
            # 记录SQL查询结果
            debug_info['sql_query_rows'] = len(rows)
            print(f"SQL查询返回 {len(rows)} 行数据")
            
            # 检查是否有数据
            if not rows:
                debug_info['error'] = "查询没有返回任何数据"
                print(f"未找到对应时间点的记录: {time_id}")
                return jsonify({
                    'error': '未找到对应时间点的记录',
                    'query_time': display_time,
                    'debug_info': debug_info
                })
            
            debug_info['rows_count'] = len(rows)
            debug_info['display_time'] = display_time
            
            # 处理数据，处理重复的房间号并确保电量值为浮点数
            building_room_data = {}  # 用于去重
            
            for row in rows:
                building = row['building']
                room = row['room']
                electricity = row['electricity']
                row_time = row['query_time']
                
                # 构建唯一键
                key = f"{building}-{room}"
                
                try:
                    electricity_value = float(electricity) if electricity is not None else 0.0
                    
                    # 如果该房间已存在记录，仅保留最新的数据
                    if key in building_room_data:
                        existing_time = building_room_data[key]['time']
                        # 只有更新的记录才替换
                        if row_time > existing_time:
                            building_room_data[key] = {
                                'building': building,
                                'room': room,
                                'electricity': electricity_value,
                                'time': row_time
                            }
                    else:
                        building_room_data[key] = {
                            'building': building,
                            'room': room,
                            'electricity': electricity_value,
                            'time': row_time
                        }
                except (ValueError, TypeError) as e:
                    debug_info['errors'] = debug_info.get('errors', []) + [f"电量值转换失败 {key}: {str(e)}"]
                    continue
            
            # 转换为列表
            formatted_data = []
            for key, data in building_room_data.items():
                formatted_data.append({
                    'building': data['building'],
                    'room': data['room'],
                    'electricity': data['electricity']
                })
            
            # 按照电量值排序
            formatted_data.sort(key=lambda x: x['electricity'])
            
            debug_info['unique_rooms'] = len(formatted_data)
            print(f"处理后共 {len(formatted_data)} 个唯一房间")
            
            # 返回结果
            response_data = {
                'query_time': display_time,
                'data': formatted_data,
                'count': len(formatted_data),
                'debug_info': debug_info
            }
            print(f"返回结果：query_time={display_time}, 数据条数={len(formatted_data)}")
            return jsonify(response_data)
            
        except ValueError as e:
            debug_info['value_error'] = str(e)
            print(f"时间格式错误: {str(e)}")
            return jsonify({
                'error': f'时间格式错误: {str(e)}',
                'query_time': time_id,
                'debug_info': debug_info
            })
        
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        print(f"查询出错: {str(e)}")
        error_info = {
            'error': str(e),
            'time_id': time_id
        }
        
        # 如果是可追踪的错误，添加行号信息
        if hasattr(e, '__traceback__'):
            tb = e.__traceback__
            while tb.tb_next:
                tb = tb.tb_next
            error_info['line'] = tb.tb_lineno
            
        return jsonify({
            'error': f'查询出错: {str(e)}',
            'query_time': time_id,
            'debug_info': error_info
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
                SELECT DATE_FORMAT(er.query_time, '%%Y-%%m-%%d %%H:%%i:%%s') as query_time, er.electricity 
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