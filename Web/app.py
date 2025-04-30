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
        
        # 检查新表是否存在
        cursor.execute("SHOW TABLES LIKE 'electricity_records'")
        if cursor.fetchone():
            # 调试信息: 获取记录总数
            cursor.execute("SELECT COUNT(*) as total FROM electricity_records")
            total_count = cursor.fetchone()['total']
            
            # 使用新表 - 获取所有不同日期的电量记录
            cursor.execute("""
                SELECT 
                    DATE_FORMAT(query_time, '%%Y%%m%%d') as date_id,
                    DATE_FORMAT(query_time, '%%Y-%%m-%%d') as date_str,
                    COUNT(*) as record_count
                FROM electricity_records
                GROUP BY date_id, date_str
                ORDER BY date_id DESC
            """)
            
            distinct_dates = cursor.fetchall()
            valid_times = []
            
            # 如果没有数据，添加调试信息
            if not distinct_dates:
                return jsonify({
                    'history_times': [],
                    'debug_info': {
                        'total_records': total_count,
                        'message': '没有找到任何日期记录'
                    }
                })
            
            for date_record in distinct_dates:
                date_id = date_record['date_id']  # 格式: YYYYMMDD
                date_str = date_record['date_str']  # 格式: YYYY-MM-DD
                record_count = date_record['record_count']
                
                # 查找该日期的查询历史记录
                cursor.execute("""
                    SELECT id, query_time, description
                    FROM query_history
                    WHERE DATE_FORMAT(query_time, '%%Y%%m%%d') = %s
                    ORDER BY query_time DESC
                    LIMIT 1
                """, (date_id,))
                
                qh_record = cursor.fetchone()
                
                if qh_record:
                    # 使用查询历史记录
                    valid_times.append({
                        'id': qh_record['id'],
                        'query_time': qh_record['query_time'].strftime('%Y-%m-%d %H:%M:%S'),
                        'description': qh_record['description'],
                        'time_id': date_id,
                        'record_count': record_count
                    })
                else:
                    # 没有查询历史记录，使用日期信息
                    valid_times.append({
                        'id': 0,
                        'query_time': f"{date_str} 00:00:00",
                        'description': f"{date_str} 电量记录 ({record_count}条)",
                        'time_id': date_id,
                        'record_count': record_count
                    })
            
            # 添加调试信息
            debug_info = {
                'total_records': total_count,
                'distinct_dates': len(distinct_dates),
                'valid_times': len(valid_times)
            }
            
            return jsonify({
                'history_times': valid_times,
                'debug_info': debug_info
            })
        else:
            # 使用旧表 - 保持原有逻辑
            cursor.execute("SELECT id, query_time, description FROM query_history ORDER BY query_time DESC")
            history_times = cursor.fetchall()
            
            # 检查每个时间点是否有对应的电量列
            valid_times = []
            for item in history_times:
                # 使用Python的strftime格式化时间，避免使用MySQL的DATE_FORMAT
                column_name = f"e_{item['query_time'].strftime('%Y%m%d%H%M%S')}"
                
                cursor.execute(f"SHOW COLUMNS FROM electricity_history LIKE '{column_name}'")
                if cursor.fetchone():
                    item['column_name'] = column_name
                    item['query_time'] = item['query_time'].strftime('%Y-%m-%d %H:%M:%S')
                    valid_times.append(item)
            
            return jsonify({'history_times': valid_times})
        
        cursor.close()
        conn.close()
    except Exception as e:
        return jsonify({
            'error': str(e),
            'debug_info': {
                'location': 'get_history_times',
                'exception': str(e)
            }
        })

@app.route('/api/history_data/<time_id>')
def get_history_data(time_id):
    """获取指定时间点的电量数据"""
    try:
        conn = pymysql.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database']
        )
        cursor = conn.cursor()
        
        # 调试信息
        debug_info = {
            'time_id': time_id,
            'steps': []
        }
        
        # 检查新表是否存在
        cursor.execute("SHOW TABLES LIKE 'electricity_records'")
        if cursor.fetchone():
            debug_info['steps'].append("发现electricity_records表")
            
            # 使用新表结构 - 根据日期查询
            try:
                # 确保time_id至少有8位，如果不够则处理为当天日期
                if len(time_id) < 8:
                    today = datetime.datetime.now()
                    date_only = today.strftime('%Y%m%d')
                    debug_info['steps'].append(f"时间ID不足8位，使用当天日期: {date_only}")
                else:
                    date_only = time_id[0:8]
                    debug_info['steps'].append(f"使用日期前缀: {date_only}")
                
                # 计算日期信息
                year = date_only[0:4]
                month = date_only[4:6]
                day = date_only[6:8]
                formatted_date = f"{year}-{month}-{day}"
                debug_info['formatted_date'] = formatted_date
                
                # 1. 检查该日期是否有记录
                cursor.execute("""
                    SELECT COUNT(*) as count
                    FROM electricity_records 
                    WHERE DATE(query_time) = %s
                """, (formatted_date,))
                count_result = cursor.fetchone()
                record_count = count_result[0] if count_result else 0
                debug_info['record_count'] = record_count
                
                if record_count == 0:
                    debug_info['steps'].append("没有找到该日期的记录")
                    return jsonify({
                        'error': '未找到对应日期的记录',
                        'query_time': formatted_date,
                        'debug_info': debug_info
                    })
                
                debug_info['steps'].append(f"找到该日期的{record_count}条记录")
                
                # 2. 获取该日期的所有记录
                cursor.execute("""
                    SELECT 
                        building, 
                        room, 
                        electricity,
                        DATE_FORMAT(query_time, '%%Y-%%m-%%d %%H:%%i:%%s') as formatted_time
                    FROM electricity_records 
                    WHERE DATE(query_time) = %s
                """, (formatted_date,))
                
                rows = cursor.fetchall()
                debug_info['rows_fetched'] = len(rows)
                
                # 3. 获取该日期的最新查询时间
                cursor.execute("""
                    SELECT DATE_FORMAT(MAX(query_time), '%%Y-%%m-%%d %%H:%%i:%%s') as latest_time
                    FROM electricity_records
                    WHERE DATE(query_time) = %s
                """, (formatted_date,))
                
                time_result = cursor.fetchone()
                query_time = time_result[0] if time_result and time_result[0] else formatted_date
                debug_info['display_time'] = query_time
                
                # 4. 处理数据为前端可用格式
                formatted_data = []
                building_room_data = {}  # 用于去重
                
                for row in rows:
                    building, room, electricity, row_time = row
                    key = f"{building}-{room}"
                    
                    try:
                        electricity_value = float(electricity)
                        
                        # 如果该房间已存在记录，检查时间是否更新
                        if key in building_room_data:
                            existing_time = building_room_data[key]['row_time']
                            # 只有更新的记录才替换
                            if row_time > existing_time:
                                building_room_data[key] = {
                                    'building': building,
                                    'room': room,
                                    'electricity': electricity_value,
                                    'row_time': row_time
                                }
                        else:
                            building_room_data[key] = {
                                'building': building,
                                'room': room, 
                                'electricity': electricity_value,
                                'row_time': row_time
                            }
                    except (ValueError, TypeError) as e:
                        debug_info['errors'] = debug_info.get('errors', []) + [f"电量值转换失败 {building}-{room}: {str(e)}"]
                        continue
                
                # 转换为列表
                for key, data in building_room_data.items():
                    formatted_data.append({
                        'building': data['building'],
                        'room': data['room'],
                        'electricity': data['electricity']
                    })
                
                debug_info['unique_rooms'] = len(formatted_data)
                
                # 按照电量值排序
                formatted_data.sort(key=lambda x: x['electricity'])
                
                # 返回结果
                return jsonify({
                    'query_time': query_time,
                    'data': formatted_data,
                    'debug_info': debug_info
                })
                
            except Exception as parsing_error:
                debug_info['error'] = str(parsing_error)
                debug_info['traceback'] = str(parsing_error.__traceback__.tb_lineno)
                return jsonify({
                    'error': f'解析或查询错误: {str(parsing_error)}',
                    'query_time': time_id,
                    'debug_info': debug_info
                })
        else:
            # 使用旧表结构 - 保持不变
            # 处理column_name参数
            if time_id.startswith('e_'):
                column_name = time_id
            else:
                column_name = f'e_{time_id}'
                
            # 尝试格式化时间字符串为更友好的格式
            time_str = time_id if not time_id.startswith('e_') else time_id[2:]
            formatted_time = time_str
            try:
                # 尝试将时间字符串解析为datetime并重新格式化
                year = time_str[0:4]
                month = time_str[4:6]
                day = time_str[6:8]
                hour = time_str[8:10] if len(time_str) >= 10 else "00"
                minute = time_str[10:12] if len(time_str) >= 12 else "00"
                second = time_str[12:14] if len(time_str) >= 14 else "00"
                
                formatted_time = f"{year}-{month}-{day} {hour}:{minute}:{second}"
            except Exception:
                # 如果解析失败，使用原始时间字符串
                pass
                
            # 首先验证列名是否存在
            cursor.execute(f"SHOW COLUMNS FROM electricity_history LIKE '{column_name}'")
            if not cursor.fetchone():
                return jsonify({
                    'error': '未找到对应的历史数据列',
                    'query_time': formatted_time
                })
            
            # 查询指定时间的电量数据
            cursor.execute(f"SELECT building, room, {column_name} FROM electricity_history WHERE {column_name} IS NOT NULL")
            rows = cursor.fetchall()
            
            # 获取该列对应的查询时间
            cursor.execute("SELECT query_time FROM query_history WHERE DATE_FORMAT(query_time, '%%Y%%m%%d%%H%%i%%S') = %s", (time_str,))
            time_row = cursor.fetchone()
            query_time = time_row[0].strftime('%Y-%m-%d %H:%M:%S') if time_row else formatted_time
            
            # 处理为前端可用的格式
            formatted_data = []
            for row in rows:
                building, room, electricity = row
                try:
                    electricity_value = float(electricity)
                    formatted_data.append({
                        'building': building,
                        'room': room,
                        'electricity': electricity_value
                    })
                except (ValueError, TypeError):
                    continue
                    
            # 按照电量值排序
            formatted_data.sort(key=lambda x: x['electricity'])
            
            return jsonify({
                'query_time': query_time,
                'data': formatted_data
            })
        
        cursor.close()
        conn.close()
    except Exception as e:
        debug_info = {
            'error': str(e),
            'time_id': time_id
        }
        # 确保即使出错也返回时间信息
        return jsonify({
            'error': str(e),
            'query_time': time_id,
            'debug_info': debug_info
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