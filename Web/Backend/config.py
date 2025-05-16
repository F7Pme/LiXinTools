import os
import sys

# 添加项目根目录到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 从密码文件读取数据库密码
def get_db_password():
    password_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "config", "db_password.txt")
    try:
        if os.path.exists(password_file):
            with open(password_file, "r") as f:
                return f.read().strip()
        else:
            return "123456"  # 默认密码，本地开发使用
    except Exception as e:
        print(f"读取密码文件出错: {str(e)}")
        return "123456"  # 出错时使用默认密码

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'elecuser',
    'password': get_db_password(),
    'database': 'electricity_data'
}

# Redis配置
REDIS_CONFIG = {
    'host': 'localhost',
    'port': 6379,
    'password': None,  # 设置为您的Redis密码，如果有的话
    'db': 0,
    'decode_responses': False  # 存储二进制数据时需要设为False
}

# 缓存过期时间配置（秒）
CACHE_TIMES = {
    'latest_query_time': 60,       # 最新查询时间缓存1分钟
    'electricity_data': 300,       # 电量数据缓存5分钟
    'analysis': 600,               # 分析结果缓存10分钟
    'query_history': 300,          # 查询历史缓存5分钟
    'building_data': 600,          # 楼栋数据缓存10分钟
    'history_times': 300,          # 历史时间点缓存5分钟
    'history_data': 600,           # 历史数据缓存10分钟
    'room_history': 600            # 房间历史数据缓存10分钟
} 