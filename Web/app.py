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
    'user': 'root',
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

if __name__ == '__main__':
    app.run(debug=True) 