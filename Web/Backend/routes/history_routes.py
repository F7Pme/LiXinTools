from flask import jsonify, request
import urllib.parse
import pymysql
import datetime
from ..config import DB_CONFIG, CACHE_TIMES
from ..cache import cache_with_redis
from ..database import get_db_connection, get_query_history_records
from . import history_bp

@history_bp.route('/api/query_history')
@cache_with_redis(expire=CACHE_TIMES['query_history'])
def get_query_history():
    """获取查询历史记录"""
    try:
        history = get_query_history_records(limit=10)
        return jsonify({'history': history})
    except Exception as e:
        return jsonify({'error': str(e)})

@history_bp.route('/api/history_times')
@cache_with_redis(expire=CACHE_TIMES['history_times'])
def get_history_times():
    """获取所有历史查询时间点"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        # 调试信息
        debug_info = {}
        
        # 统计记录总数
        cursor.execute("SELECT COUNT(*) AS count FROM electricity_records")
        result = cursor.fetchone()
        record_count = result['count'] if result else 0
        debug_info['total_records'] = record_count
        
        print(f"开始查询历史时间点，共有 {record_count} 条记录")
        
        # 使用简单的SQL查询获取历史时间点
        try:
            cursor.execute("""
                SELECT 
                    DATE_FORMAT(query_time, '%Y%m%d%H%i') AS time_id_format,
                    DATE_FORMAT(query_time, '%Y-%m-%d %H:%i') AS formatted_time,
                    COUNT(*) AS record_count,
                    MAX(query_time) AS latest_time
                FROM 
                    electricity_records
                GROUP BY 
                    time_id_format, formatted_time
                ORDER BY 
                    latest_time DESC
                LIMIT 100
            """)
            
            time_points = cursor.fetchall()
            debug_info['query_result_count'] = len(time_points)
            print(f"查询到 {len(time_points)} 个不同的时间点")
            
        except Exception as query_error:
            print(f"历史时间点查询出错: {str(query_error)}")
            debug_info['query_error'] = str(query_error)
            time_points = []
        
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
            # 从格式化字段提取时间ID (使用time_id_format字段)
            time_id_raw = point.get('time_id_format')
            formatted_time = point.get('formatted_time')
            record_count = point.get('record_count', 0)
            
            # 确保time_id是一个有效的字符串
            if not time_id_raw or time_id_raw == 'None' or time_id_raw == 'null':
                print(f"警告：跳过无效的time_id: {time_id_raw}")
                continue
                
            # 强制转换为字符串并移除任何空白字符
            time_id_str = str(time_id_raw).strip()
            
            # 创建包含有效time_id的记录
            time_record = {
                'time_id': time_id_str,  # 确保这是一个字符串
                'query_time': formatted_time,
                'description': f"电量记录 ({record_count}条)",
                'record_count': record_count,
                'id': 0
            }
            
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
            except Exception as qh_error:
                debug_info['query_history_error'] = str(qh_error)
                print(f"  查询历史记录出错: {str(qh_error)}")
            
            valid_times.append(time_record)
            
        cursor.close()
        conn.close()
        
        # 返回结果
        result = {
            'history_times': valid_times,
            'count': len(valid_times),
            'debug_info': debug_info
        }
        
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

@history_bp.route('/api/history_data/<path:time_id>')
@cache_with_redis(expire=CACHE_TIMES['history_data'])
def get_history_data(time_id):
    """获取指定时间点的电量数据"""
    try:
        # 添加详细的调试日志
        print(f"\n=======================================")
        print(f"收到API请求：/api/history_data/{time_id}")
        print(f"原始time_id参数: [{time_id}], 类型: {type(time_id).__name__}")
        
        # URL解码
        decoded_time_id = urllib.parse.unquote(str(time_id)).strip()
        print(f"URL解码后: [{decoded_time_id}]")
        
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 调试信息
        debug_info = {
            'time_id_raw': time_id,
            'time_id_decoded': decoded_time_id,
            'time_id_type': type(time_id).__name__,
            'function': 'get_history_data'
        }
        
        # 记录详细调试信息
        print(f"-------- 开始处理历史数据请求 --------")
        
        # 验证time_id
        if not decoded_time_id or decoded_time_id == 'undefined' or decoded_time_id == 'null':
            print(f"无效的时间ID: [{decoded_time_id}]")
            return jsonify({
                'error': '无效的时间ID',
                'query_time': '未知时间',
                'debug_info': debug_info
            })
            
        # 确保time_id是字符串类型
        time_id = decoded_time_id
        debug_info['time_id_final'] = time_id
        
        # 处理时间ID
        try:
            print(f"处理time_id: [{time_id}], 长度: {len(time_id)}, 是数字: {time_id.isdigit()}")
            
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
                           CONCAT(
                                YEAR(query_time), '-',
                                LPAD(MONTH(query_time), 2, '0'), '-',
                                LPAD(DAY(query_time), 2, '0'), ' ',
                                LPAD(HOUR(query_time), 2, '0'), ':',
                                LPAD(MINUTE(query_time), 2, '0'), ':',
                                LPAD(SECOND(query_time), 2, '0')
                           ) AS query_time
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
                
                # 查询指定分钟的数据 - 使用CONCAT替代DATE_FORMAT
                cursor.execute("""
                    SELECT building, room, electricity, 
                          CONCAT(
                               YEAR(query_time), '-',
                               LPAD(MONTH(query_time), 2, '0'), '-',
                               LPAD(DAY(query_time), 2, '0'), ' ',
                               LPAD(HOUR(query_time), 2, '0'), ':',
                               LPAD(MINUTE(query_time), 2, '0'), ':',
                               LPAD(SECOND(query_time), 2, '0')
                          ) AS query_time
                    FROM electricity_records
                    WHERE CONCAT(
                             YEAR(query_time),
                             LPAD(MONTH(query_time), 2, '0'),
                             LPAD(DAY(query_time), 2, '0'),
                             LPAD(HOUR(query_time), 2, '0'),
                             LPAD(MINUTE(query_time), 2, '0')
                         ) = %s
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
                                           CONCAT(
                                                YEAR(query_time), '-',
                                                LPAD(MONTH(query_time), 2, '0'), '-',
                                                LPAD(DAY(query_time), 2, '0'), ' ',
                                                LPAD(HOUR(query_time), 2, '0'), ':',
                                                LPAD(MINUTE(query_time), 2, '0'), ':',
                                                LPAD(SECOND(query_time), 2, '0')
                                           ) AS query_time
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
                'electricity_data': formatted_data,  # 添加electricity_data字段以兼容前端
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

@history_bp.route('/api/room_history/<building>/<room>')
@cache_with_redis(expire=CACHE_TIMES['room_history'])
def get_room_history(building, room):
    """获取特定房间的历史电量数据"""
    try:
        conn = get_db_connection()
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