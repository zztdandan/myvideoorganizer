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
        '.flv', '.rmvb', '.rm', '.3gp', '.m4v'
    }
    MIN_VIDEO_SIZE_MB: int = 500
    
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
    
    @classmethod
    def get_delete_base_dir(cls) -> Path:
        """获取删除文件的基础目录"""
        return Path(cls.ROOT_DIR) / cls.DELETE_DIR_NAME

class DevConfig(BaseConfig):
    """开发环境配置"""
    # 可以覆盖基础配置的任何属性
    ROOT_DIR="Z:/JAV/atmp"
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