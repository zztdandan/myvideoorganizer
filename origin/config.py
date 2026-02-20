"""
配置文件: 支持多环境配置继承
"""
from pathlib import Path
from typing import List, Dict, Set
import os

class BaseConfig:
    """基础配置类，定义所有配置项"""
    
    # 根目录配置
    ROOT_DIR: str = "/path/to/videos"  # 实际使用时替换为真实路径
    
    # 视频文件相关配置
    VIDEO_EXTENSIONS: Set[str] = {
        '.mp4', '.mkv', '.avi', '.wmv', '.mov', 
        '.flv', '.rmvb', '.rm', '.3gp', '.m4v','.m2ts','.ts','.mpg'
    }
    MIN_VIDEO_SIZE_MB: int = 300
    
    # 图片文件相关配置
    IMAGE_EXTENSIONS: Set[str] = {
        '.jpg', '.jpeg', '.png', '.gif', 
        '.bmp', '.webp', '.tiff'
    }
    VALID_IMAGE_KEYWORDS: Set[str] = {
        'poster', 'movie', 'folder', 'cover', 
        'fanart', 'banner', 'clearart', 'thumb',
        'landscape', 'logo', 'clearlogo', 'disc',
        'discart','backdrop', 'keyart'
    }
    
    # NFO文件配置
    NFO_MATCH_LENGTH: int = 5  # 视频文件名匹配前N个字符
    
    # 重命名序号规则选项
    RENAME_PATTERNS: Dict[str, List[str]] = {
        'number': [str(i) for i in range(1, 100)],  # 1, 2, 3...
        'letter': [chr(i) for i in range(65, 91)],  # A, B, C...
        'number2': [f"{i:02d}" for i in range(1, 100)]  # 01, 02, 03...
    }
    # 默认使用的重命名规则
    DEFAULT_RENAME_PATTERN: str = 'number2'
    
    # 删除文件存放相关配置
    DELETE_DIR_NAME: str = '.delete'
    
    # JSON操作文件相关配置
    JSON_OUTPUT_DIR: str = 'operations'
    JSON_BATCH_SIZE: int = 200  # 每个JSON文件包含的最大任务数
    
    # 超宽视频相关配置
    BIG_VIDEO_DIR: str = 'BIG'  # 超宽视频存放目录
    BIG_VIDEO_WIDTH_THRESHOLD: int = 2000  # 超宽视频宽度阈值
    
    # 演员分类相关配置
    UNKNOWN_ACTOR_CATEGORY: str = '99'  # 未知演员分类
    JAPANESE_ACTOR_CATEGORY: str = '0'  # 日文名演员分类
    TITLE_MAX_LENGTH: int = 10  # 标题最大长度（用于文件夹命名）
    
    # OpenRouter API相关配置
    OPENROUTER_API_KEY: str = "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"  # OpenRouter API密钥
    OPENROUTER_MODEL: str = "google/gemini-2.0-flash-001"  # 使用的模型名称
    OPENROUTER_API_URL: str = "https://openrouter.ai/api/v1/chat/completions"  # API端点URL
    
    # 电影整理功能专用配置
    MOVIE_DIR: str = ""  # 电影目录路径，为空则使用ROOT_DIR
    MOVIE_FORCE_REORGANIZE: bool = False  # 是否强制重新整理已整理的文件夹
    
    MOVIE_NAME_EXTRACTION_PROMPT: str = """请分析以下单个电影的信息，提取准确的中文名、英文名和年份。

文件夹名称: {folder_name}
视频文件名: {video_files}
NFO内容摘要: {nfo_content}

注意：
1. 这是一个电影，不是多个电影
2. 文件夹名可能包含网站信息、发布组等无关内容，请忽略
3. 英文名使用点分隔单词（如The.Hobbit.An.Unexpected.Journey）
4. 如果没有中文名，chinese_name可以为null

请只返回一个JSON对象（不是数组），格式如下：
{{
  "chinese_name": "电影的中文名称或null",
  "english_name": "The.Movie.Name",
  "year": 2023,
  "confidence": 0.95
}}

只返回JSON对象，不要包含markdown代码块标记或其他文字。"""
    
    @classmethod
    def get_delete_base_dir(cls) -> Path:
        """获取删除文件的基础目录"""
        return Path(cls.ROOT_DIR) / cls.DELETE_DIR_NAME
        
    @classmethod
    def get_big_video_dir(cls) -> Path:
        """获取超宽视频存放目录"""
        return Path(cls.ROOT_DIR) / cls.BIG_VIDEO_DIR

class DevConfig(BaseConfig):
    """开发环境配置"""
    # 可以覆盖基础配置的任何属性
    ROOT_DIR="Z:/JELLYFIN/JAV/atmp"
    MOVIE_DIR="Z:/JELLYFIN/MOVIE"  # 电影整理功能使用此目录
    DEFAULT_RENAME_PATTERN='number'
class Config:
    """配置加载器"""
    
    @staticmethod
    def load_config():
        """根据环境变量加载对应配置"""
        env = os.getenv('ENV', 'dev').lower()
        if env == 'dev':
            return DevConfig
        # 后续可以添加其他环境的配置
        return DevConfig