from flask import jsonify
import sys
import os
# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from utils.analysis_electricity import ElectricityAnalysis
from ..config import DB_CONFIG, CACHE_TIMES
from ..cache import cache_with_redis
from . import electricity_bp

@electricity_bp.route('/api/latest_query_time')
@cache_with_redis(expire=CACHE_TIMES['latest_query_time'])
def get_latest_query_time():
    """获取最新的查询时间"""
    analyzer = ElectricityAnalysis(
        DB_CONFIG['host'], 
        DB_CONFIG['user'], 
        DB_CONFIG['password']
    )
    query_time = analyzer.get_latest_query_time()
    return jsonify({'query_time': query_time or "暂无查询记录"})

@electricity_bp.route('/api/electricity_data')
@cache_with_redis(expire=CACHE_TIMES['electricity_data'])
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

@electricity_bp.route('/api/analysis')
@cache_with_redis(expire=CACHE_TIMES['analysis'])
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

@electricity_bp.route('/api/building_data')
@cache_with_redis(expire=CACHE_TIMES['building_data'])
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