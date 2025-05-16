import redis
import pickle
from functools import wraps
from .config import REDIS_CONFIG

# 创建Redis连接
try:
    redis_client = redis.Redis(**REDIS_CONFIG)
    redis_enabled = True
    print("Redis连接成功")
except Exception as e:
    print(f"Redis连接失败: {str(e)}")
    redis_enabled = False

# 缓存装饰器
def cache_with_redis(expire=300):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 如果Redis不可用，直接调用原函数
            if not redis_enabled:
                return f(*args, **kwargs)
                
            # 创建缓存键
            cache_key = f.__name__ + str(args) + str(kwargs)
            
            try:
                # 尝试从Redis获取缓存
                cached_result = redis_client.get(cache_key)
                if cached_result:
                    print(f"使用缓存数据: {f.__name__}")
                    return pickle.loads(cached_result)
                    
                # 如果没有缓存，执行原函数
                print(f"无缓存，执行查询: {f.__name__}")
                result = f(*args, **kwargs)
                
                # 存储结果到Redis
                redis_client.setex(cache_key, expire, pickle.dumps(result))
                return result
            except Exception as e:
                print(f"Redis缓存错误: {str(e)}")
                # 出错时，回退到原函数
                return f(*args, **kwargs)
                
        return decorated_function
    return decorator

# 清除特定前缀的缓存
def clear_cache_prefix(prefix):
    if not redis_enabled:
        return False
    
    try:
        # 查找所有匹配前缀的键
        keys = redis_client.keys(f"{prefix}*")
        
        # 如果有键，删除它们
        if keys:
            redis_client.delete(*keys)
            print(f"已清除前缀为 {prefix} 的缓存")
            return True
        
        return False
    except Exception as e:
        print(f"清除缓存错误: {str(e)}")
        return False

# 清除所有缓存
def clear_all_cache():
    if not redis_enabled:
        return False
    
    try:
        redis_client.flushdb()
        print("已清除所有缓存")
        return True
    except Exception as e:
        print(f"清除所有缓存错误: {str(e)}")
        return False 