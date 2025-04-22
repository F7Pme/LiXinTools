import os
import json
import sys

class Config:
    # Cookie配置
    COOKIE_FILE = os.path.join("cookies", "session_cookies.json")
    
    # 房间数据配置 - 直接使用资源文件路径，不再创建目录
    @staticmethod
    def get_room_data_folder():
        """获取房间数据文件夹路径，优先使用PyInstaller打包后的资源路径"""
        if getattr(sys, 'frozen', False):
            # 在PyInstaller打包环境中，使用_MEIPASS指向包内资源
            return os.path.join(sys._MEIPASS, "config", "room_data")
        else:
            # 在开发环境中，使用相对路径
            return os.path.join("config", "room_data")
    
    # 网络配置
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0"
    TIMEOUT = 10
    
    # 楼宇映射配置
    BUILDING_NAME_MAP = {1: "一", 2: "二", 3: "三", 4: "四", 5: "五", 6: "六"}
    BUILDING_MAP = {
        1: (11, 4, 0),
        2: (12, 4, 0),
        3: (13, 4, 0),
        4: (1391, 3, 2),
        5: (1844, 3, 2),
        6: (2296, 3, 2),
    }
    
    # 配置键名
    DEVELOPER_MODE_KEY = "developer_mode"
    CURRENT_ACCOUNT_KEY = "current_account"
    
    # 账单表格模板常量
    BILL_TABLE_TEMPLATE = {
        "height": 284,
        "widths": [40, 129, 204, 120, 59]
    }
    
    # 内存中的配置存储
    _config = {
        DEVELOPER_MODE_KEY: False,
        CURRENT_ACCOUNT_KEY: ""
    }
    
    @classmethod
    def get_config(cls, key, default=None):
        """从内存中获取配置项的值"""
        if key in cls._config:
            return cls._config[key]
        return default
    
    @classmethod
    def set_config(cls, key, value):
        """将配置项的值保存到内存中"""
        cls._config[key] = value
        return True
    
    @classmethod
    def save_developer_mode(cls, is_enabled):
        """保存开发者模式状态"""
        return cls.set_config(cls.DEVELOPER_MODE_KEY, is_enabled)
    
    @classmethod
    def get_developer_mode(cls):
        """获取开发者模式状态"""
        return cls.get_config(cls.DEVELOPER_MODE_KEY)
        
    @classmethod
    def save_current_account(cls, account_id):
        """保存当前账户ID"""
        return cls.set_config(cls.CURRENT_ACCOUNT_KEY, account_id)
        
    @classmethod
    def get_current_account(cls):
        """获取当前账户ID"""
        return cls.get_config(cls.CURRENT_ACCOUNT_KEY, "")
    
    @classmethod
    def load_all_config(cls):
        """获取所有配置"""
        return cls._config.copy()
    
    @classmethod
    def save_all_config(cls, config_dict):
        """保存所有配置"""
        cls._config.update(config_dict)
        return True