from flask import jsonify, request
import datetime
import pymysql
from ..config import DB_CONFIG
from ..database import get_db_connection, get_db_tables, get_table_structure, get_sample_data
from . import debug_bp

@debug_bp.route('/api/debug/database_info')
def debug_database_info():
    """调试端点：获取数据库表结构和部分数据"""
    try:
        # 获取数据库中所有表
        tables = get_db_tables()
        
        result = {
            'tables': tables,
            'table_structures': {},
            'sample_data': {}
        }
        
        # 对每个表获取结构和样本数据
        for table in tables:
            result['table_structures'][table] = get_table_structure(table)
            result['sample_data'][table] = get_sample_data(table, limit=5)
            
            # 如果是electricity_history表，获取特殊信息
            if table == 'electricity_history':
                conn = get_db_connection()
                cursor = conn.cursor()
                
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

@debug_bp.route('/api/fix_history_data', methods=['POST'])
def fix_history_data():
    """修复历史电量数据问题"""
    try:
        conn = get_db_connection()
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