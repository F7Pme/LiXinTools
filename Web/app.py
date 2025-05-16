#!/usr/bin/env python3
import os
import sys
import argparse

# 添加当前目录到系统路径，确保可以导入本地模块
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# 导入应用工厂函数
from Backend import create_app

# 创建Flask应用
app = create_app()

if __name__ == '__main__':
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='启动电量查询系统Web服务')
    parser.add_argument('--host', default='0.0.0.0', help='监听主机地址')
    parser.add_argument('--port', type=int, default=5000, help='监听端口')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    args = parser.parse_args()
    
    # 启动应用
    app.run(host=args.host, port=args.port, debug=args.debug) 