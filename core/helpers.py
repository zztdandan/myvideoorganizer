"""
通用工具函数模块
"""
from pathlib import Path
from typing import List, Union
import os
from datetime import datetime

def get_file_size_mb(file_path: Union[str, Path]) -> float:
    """
    获取文件大小（MB）
    
    Args:
        file_path: 文件路径
        
    Returns:
        文件大小（MB）
    """
    return os.path.getsize(str(file_path)) / (1024 * 1024)

def format_tree_view(path: Path, prefix: str = "") -> List[str]:
    """
    生成目录树形结构的文本表示
    
    Args:
        path: 要展示的路径
        prefix: 前缀字符串（用于递归）
        
    Returns:
        树形结构的文本行列表
    """
    if not path.exists():
        return [f"{prefix}── {path.name} (not found)"]
    
    if path.is_file():
        return [f"{prefix}── {path.name}"]
        
    lines = [f"{prefix}── {path.name}/"]
    
    # 获取子项目并排序（目录在前，文件在后）
    items = list(path.iterdir())
    dirs = sorted([x for x in items if x.is_dir()])
    files = sorted([x for x in items if x.is_file()])
    
    items = dirs + files
    
    for i, item in enumerate(items):
        if i == len(items) - 1:  # 最后一项
            lines.extend(format_tree_view(item, prefix + "    "))
        else:
            lines.extend(format_tree_view(item, prefix + "│   "))
            
    return lines

def get_delete_path(root_dir: Path, source_path: Path) -> Path:
    """
    根据源文件路径生成对应的删除目录路径
    
    Args:
        root_dir: 根目录
        source_path: 源文件路径
        
    Returns:
        删除目录中的目标路径
    """
    # 获取相对于根目录的路径
    try:
        relative_path = source_path.relative_to(root_dir)
    except ValueError:
        relative_path = source_path.name
        
    # 构造删除目录路径（.delete/当前日期/原始相对路径）
    delete_base = root_dir / '.delete' / datetime.now().strftime('%Y%m%d')
    return delete_base / relative_path

def ensure_dir(path: Path) -> None:
    """
    确保目录存在，如果不存在则创建
    
    Args:
        path: 目录路径
    """
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)

def is_video_file(file_path: Path, config) -> bool:
    """
    判断文件是否为符合大小要求的视频文件
    
    Args:
        file_path: 文件路径
        config: 配置对象
        
    Returns:
        是否为符合要求的视频文件
    """
    if not file_path.is_file():
        return False
    
    if file_path.suffix.lower() not in config.VIDEO_EXTENSIONS:
        return False
        
    return get_file_size_mb(file_path) >= config.MIN_VIDEO_SIZE_MB

def is_image_file(file_path: Path, config) -> bool:
    """
    判断文件是否为图片文件
    
    Args:
        file_path: 文件路径
        config: 配置对象
        
    Returns:
        是否为图片文件
    """
    return file_path.is_file() and file_path.suffix.lower() in config.IMAGE_EXTENSIONS

def is_nfo_file(file_path: Path) -> bool:
    """
    判断文件是否为NFO文件
    
    Args:
        file_path: 文件路径
        
    Returns:
        是否为NFO文件
    """
    return file_path.is_file() and file_path.suffix.lower() == '.nfo'