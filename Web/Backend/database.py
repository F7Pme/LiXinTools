import pymysql
import datetime
from .config import DB_CONFIG

# 获取数据库连接
def get_db_connection():
    """创建并返回一个数据库连接"""
    try:
        conn = pymysql.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database']
        )
        return conn
    except Exception as e:
        print(f"数据库连接失败: {str(e)}")
        raise

# 获取查询历史记录
def get_query_history_records(limit=10):
    """获取最近的查询历史记录"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 获取最近10次查询历史
        cursor.execute("SELECT id, query_time, description FROM query_history ORDER BY query_time DESC LIMIT %s", (limit,))
        history = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # 将datetime对象转换为字符串
        for item in history:
            item['query_time'] = item['query_time'].strftime('%Y-%m-%d %H:%M:%S')
        
        return history
    except Exception as e:
        print(f"获取查询历史失败: {str(e)}")
        return []

# 获取数据库表信息
def get_db_tables():
    """获取数据库中的所有表名"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取数据库中所有表
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        return tables
    except Exception as e:
        print(f"获取数据库表失败: {str(e)}")
        return []

# 获取表结构信息
def get_table_structure(table_name):
    """获取指定表的结构信息"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取表结构
        cursor.execute(f"DESCRIBE {table_name}")
        columns = cursor.fetchall()
        
        # 转换为更友好的格式
        structure = [
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
        
        cursor.close()
        conn.close()
        
        return structure
    except Exception as e:
        print(f"获取表结构失败: {str(e)}")
        return []

# 获取表中的样本数据
def get_sample_data(table_name, limit=5):
    """获取指定表的样本数据"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 获取列名
        cursor.execute(f"SHOW COLUMNS FROM {table_name}")
        columns = [col[0] for col in cursor.fetchall()]
        
        # 获取样本数据
        cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
        rows = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # 将datetime转换为字符串
        for row in rows:
            for key, value in row.items():
                if isinstance(value, datetime.datetime):
                    row[key] = value.strftime('%Y-%m-%d %H:%M:%S')
        
        return rows
    except Exception as e:
        print(f"获取样本数据失败: {str(e)}")
        return [] 