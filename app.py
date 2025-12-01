"""
Flask应用: 提供Web界面，集成现有的视频组织功能
"""
from flask import Flask, render_template, request, jsonify, redirect, url_for
import os
import json
from pathlib import Path
from typing import List, Dict, Any

from config import Config
from core.logger import logger
from core.planner import OperationPlanner
from core.executor import OperationExecutor
from core.scraper import JavDBScraper

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['JSON_AS_ASCII'] = False

# 创建全局实例
config = Config.load_config()
planner = OperationPlanner(config)
executor = OperationExecutor(config)
scraper = JavDBScraper()

# 功能名称映射
FUNCTION_NAMES = {
    'func1': '清理非视频文件夹',
    'func2': '清理视频文件夹内文件',
    'func3': '视频重命名',
    'func4': '按演员分类视频',
    'func5': '识别超宽视频',
    'func6': '电影文件夹智能整理'
}

# 功能描述映射
FUNCTION_DESCRIPTIONS = {
    'func1': '清理根目录下不包含视频文件的文件夹，可自动移动到回收区域',
    'func2': '清理视频文件夹内的临时文件和无关文件，保留视频和重要媒体文件',
    'func3': '根据配置的规则重命名视频文件，便于统一管理和查找',
    'func4': '根据演员信息将视频分类到相应目录，自动处理不同命名风格',
    'func5': '识别超过设定宽度的视频文件，可将其移动到指定的大尺寸目录',
    'func6': '使用AI智能分析电影信息，统一整理为规范命名格式（中文名.英文名 (年份)），支持系列电影扁平化'
}

# 设置全局模板变量
@app.context_processor
def inject_globals():
    return {
        'FUNCTION_NAMES': FUNCTION_NAMES,
        'get_function_description': get_function_description
    }

@app.route('/')
def index():
    """首页"""
    return render_template('index.html')

@app.route('/config', methods=['GET', 'POST'])
def config_page():
    """配置页面"""
    config_items = get_config_items()
    save_success = False
    
    if request.method == 'POST':
        # 更新配置
        for key, value in request.form.items():
            if key in config_items:
                # 根据类型转换值
                if isinstance(config_items[key]['value'], bool):
                    setattr(config.__class__, key, value.lower() == 'true')
                elif isinstance(config_items[key]['value'], int):
                    setattr(config.__class__, key, int(value))
                elif isinstance(config_items[key]['value'], float):
                    setattr(config.__class__, key, float(value))
                elif isinstance(config_items[key]['value'], list) or isinstance(config_items[key]['value'], set):
                    # 处理列表/集合，值以逗号分隔
                    items = [item.strip() for item in value.split(',')]
                    if isinstance(config_items[key]['value'], set):
                        setattr(config.__class__, key, set(items))
                    else:
                        setattr(config.__class__, key, items)
                else:
                    # 字符串
                    setattr(config.__class__, key, value)
        
        save_success = True
        # 重新获取配置项，以便显示更新后的值
        config_items = get_config_items()
        logger.info("配置已更新")
        
    return render_template('config.html', 
                          config_items=config_items,
                          save_success=save_success)

@app.route('/function/<func_id>')
def function_page(func_id):
    """功能页面"""
    if func_id not in FUNCTION_NAMES:
        return redirect(url_for('index'))
        
    return render_template('function.html', 
                          func_id=func_id,
                          func_name=FUNCTION_NAMES[func_id])

@app.route('/api/plan/<func_id>', methods=['GET'])
def get_operations(func_id):
    """获取操作计划"""
    operations = []
    
    try:
        if func_id == 'func1':
            operations = planner.generate_clean_folders_plan()
        elif func_id == 'func2':
            operations = planner.generate_clean_files_plan()
        elif func_id == 'func3':
            operations = planner.generate_rename_plan()
        elif func_id == 'func4':
            operations = planner.generate_actor_classify_plan()
        elif func_id == 'func5':
            operations = planner.generate_big_video_plan()
        elif func_id == 'func6':
            operations = planner.generate_movie_organize_plan()
        else:
            return jsonify({"error": "未知功能"}), 400
        
        # 检查ROOT_DIR是否存在
        root_dir = Path(config.ROOT_DIR)
        if not root_dir.exists():
            return jsonify({
                "error": f"根目录不存在: {config.ROOT_DIR}",
                "suggestion": "请在配置页面修改ROOT_DIR为有效路径"
            }), 400
            
        # 如果操作列表为空但没有错误，返回空列表
        if not operations:
            logger.info(f"功能 {func_id} 没有找到需要执行的操作")
            return jsonify([])
            
        return jsonify(operations)
        
    except Exception as e:
        logger.error(f"生成操作计划时出错: {str(e)}")
        return jsonify({
            "error": f"生成操作计划失败: {str(e)}",
            "suggestion": "请检查系统配置和文件路径"
        }), 500

@app.route('/api/execute', methods=['POST'])
def execute_operations():
    """执行操作"""
    data = request.json
    if not data or 'operations' not in data:
        return jsonify({"error": "无效请求"}), 400
        
    operations = data['operations']
    if not operations:
        return jsonify({"message": "没有操作需要执行"}), 200
        
    success, failure = executor.execute_operations(operations)
    
    return jsonify({
        "success": success,
        "failure": failure,
        "message": f"执行完成: {success}个成功, {failure}个失败"
    })

@app.route('/api/config', methods=['GET'])
def get_config():
    """获取配置"""
    return jsonify(get_config_items())

@app.route('/api/test_plan/<func_id>', methods=['GET'])
def get_test_operations(func_id):
    """获取测试操作计划 - 仅用于前端调试"""
    # 创建测试数据
    test_operations = []
    
    # 根据不同功能返回不同的测试数据
    if func_id == 'func1':  # 清理非视频文件夹
        test_operations = [
            {"action": "MOVE", "source": "D:/Videos/Empty_Folder", "destination": "D:/Videos/.delete/Empty_Folder", "file_size": 0},
            {"action": "MOVE", "source": "D:/Videos/Image_Only", "destination": "D:/Videos/.delete/Image_Only", "file_size": 23.5},
            {"action": "MOVE", "source": "D:/Videos/Small_Files", "destination": "D:/Videos/.delete/Small_Files", "file_size": 45.2}
        ]
    elif func_id == 'func2':  # 清理视频文件夹内文件
        test_operations = [
            {"action": "MOVE", "source": "D:/Videos/Movie1/temp.txt", "destination": "D:/Videos/.delete/Movie1_temp.txt", "file_size": 0.1},
            {"action": "MOVE", "source": "D:/Videos/Movie2/sample.exe", "destination": "D:/Videos/.delete/Movie2_sample.exe", "file_size": 15.6},
            {"action": "MOVE", "source": "D:/Videos/Series1/subtitle.unknown", "destination": "D:/Videos/.delete/Series1_subtitle.unknown", "file_size": 1.2}
        ]
    elif func_id == 'func3':  # 视频重命名
        test_operations = [
            {"action": "RENAME", "source": "D:/Videos/movie_01.mp4", "destination": "D:/Videos/Movie (2023) 01.mp4", "file_size": 1250.8},
            {"action": "RENAME", "source": "D:/Videos/series_s01e02.mkv", "destination": "D:/Videos/Series (2022) S01E02.mkv", "file_size": 850.3},
            {"action": "RENAME", "source": "D:/Videos/untitled.avi", "destination": "D:/Videos/Untitled Movie (2021).avi", "file_size": 720.1}
        ]
    elif func_id == 'func4':  # 按演员分类视频
        test_operations = [
            {"action": "MOVE", "source": "D:/Videos/Actor1_Movie.mp4", "destination": "D:/Videos/Actors/A/Actor1/Actor1_Movie.mp4", "file_size": 1800.2},
            {"action": "MOVE", "source": "D:/Videos/Actor2_Movie.mp4", "destination": "D:/Videos/Actors/B/Actor2/Actor2_Movie.mp4", "file_size": 1450.7},
            {"action": "MOVE", "source": "D:/Videos/Unknown_Movie.mp4", "destination": "D:/Videos/Actors/99/Unknown/Unknown_Movie.mp4", "file_size": 960.4}
        ]
    elif func_id == 'func5':  # 识别超宽视频
        test_operations = [
            {"action": "MOVE", "source": "D:/Videos/Widescreen1.mp4", "destination": "D:/Videos/BIG/Widescreen1.mp4", "file_size": 2500.6},
            {"action": "MOVE", "source": "D:/Videos/Widescreen2.mkv", "destination": "D:/Videos/BIG/Widescreen2.mkv", "file_size": 3250.8},
            {"action": "MOVE", "source": "D:/Videos/UltraWide.mp4", "destination": "D:/Videos/BIG/UltraWide.mp4", "file_size": 4120.3}
        ]
    
    # 添加更多测试数据 - 每个功能各复制3次，总共12条记录
    if test_operations:
        extended_operations = test_operations.copy()
        for i in range(3):
            for op in test_operations:
                new_op = op.copy()
                new_op["source"] = f"{new_op['source']}_{i+1}"
                new_op["destination"] = f"{new_op['destination']}_{i+1}"
                extended_operations.append(new_op)
        test_operations = extended_operations
    
    return jsonify(test_operations)

def get_function_description(func_id):
    """获取功能描述"""
    return FUNCTION_DESCRIPTIONS.get(func_id, "无功能描述")

def get_config_items():
    """获取配置项"""
    config_items = {}
    
    # 获取所有大写的类属性
    for key in dir(config):
        if key.isupper() and not key.startswith('_'):
            value = getattr(config, key)
            
            # 处理集合类型，转换为列表便于JSON序列化
            if isinstance(value, set):
                value = list(value)
                
            # 添加到配置项字典
            config_items[key] = {
                'value': value,
                'type': type(value).__name__,
                'description': get_config_description(key)
            }
            
    return config_items

def get_config_description(key):
    """获取配置项描述"""
    descriptions = {
        'ROOT_DIR': '视频根目录路径',
        'VIDEO_EXTENSIONS': '视频文件扩展名列表',
        'MIN_VIDEO_SIZE_MB': '最小视频文件大小(MB)',
        'IMAGE_EXTENSIONS': '图片文件扩展名列表',
        'VALID_IMAGE_KEYWORDS': '有效图片关键词列表',
        'NFO_MATCH_LENGTH': 'NFO文件匹配长度',
        'RENAME_PATTERNS': '重命名序号规则选项',
        'DEFAULT_RENAME_PATTERN': '默认重命名规则',
        'DELETE_DIR_NAME': '删除文件存放目录名',
        'JSON_OUTPUT_DIR': 'JSON操作文件输出目录',
        'JSON_BATCH_SIZE': 'JSON文件批次大小',
        'BIG_VIDEO_DIR': '超宽视频存放目录',
        'BIG_VIDEO_WIDTH_THRESHOLD': '超宽视频宽度阈值',
        'UNKNOWN_ACTOR_CATEGORY': '未知演员分类',
        'JAPANESE_ACTOR_CATEGORY': '日文名演员分类',
        'TITLE_MAX_LENGTH': '标题最大长度',
        'OPENROUTER_API_KEY': 'OpenRouter API密钥',
        'OPENROUTER_MODEL': 'OpenRouter使用的模型名称',
        'OPENROUTER_API_URL': 'OpenRouter API端点URL',
        'MOVIE_DIR': '电影整理功能专用目录（为空则使用ROOT_DIR）',
        'MOVIE_FORCE_REORGANIZE': '是否强制重新整理已整理的文件夹',
        'MOVIE_NAME_EXTRACTION_PROMPT': '电影名称提取的AI提示词模板'
    }
    return descriptions.get(key, '未知配置项')

if __name__ == '__main__':
    # 确保模板目录存在
    templates_dir = Path('templates')
    if not templates_dir.exists():
        templates_dir.mkdir()
        
    # 确保静态文件目录存在
    static_dir = Path('static')
    if not static_dir.exists():
        static_dir.mkdir()
        
    app.run(debug=True, port=5050) 