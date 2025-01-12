"""
通用工具函数模块
"""
from pathlib import Path
from typing import List, Union, Optional, Tuple, Dict
import os
from datetime import datetime
import xml.etree.ElementTree as ET
from core.logger import logger

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

def is_video_folder(folder_path: Path, config) -> bool:
    """
    判断是否为视频文件夹（递归检查）
    
    Args:
        folder_path: 文件夹路径
        config: 配置对象
        
    Returns:
        是否为视频文件夹
    """
    if not folder_path.is_dir():
        return False
        
    # 检查当前文件夹中的文件
    for item in folder_path.iterdir():
        if is_video_file(item, config):
            return True
        if item.is_dir() and is_video_folder(item, config):
            return True
            
    return False

def parse_nfo_file(nfo_path: Path) -> Tuple[Optional[str], Optional[str], Optional[Dict]]:
    """
    解析NFO文件，获取演员名字和标题
    
    Args:
        nfo_path: NFO文件路径
        
    Returns:
        演员名字、标题和视频信息的元组
    """
    try:
        tree = ET.parse(nfo_path)
        root = tree.getroot()
        
        # 获取第一个演员名字
        actor_elem = root.find('.//actor/name')
        actor_name = actor_elem.text if actor_elem is not None else None
        
        # 获取标题
        title_elem = root.find('title')
        title = title_elem.text if title_elem is not None else None
        
        # 获取视频信息
        video_elem = root.find('.//video')
        if video_elem is not None:
            video_info = {
                'width': int(video_elem.find('width').text) if video_elem.find('width') is not None else 0,
                'height': int(video_elem.find('height').text) if video_elem.find('height') is not None else 0,
                'aspect': video_elem.find('aspect').text if video_elem.find('aspect') is not None else None
            }
        else:
            video_info = None
            
        return actor_name, title, video_info
        
    except Exception as e:
        logger.error(f"解析NFO文件出错 {nfo_path}: {str(e)}")
        return None, None, None

def get_first_nfo_file(folder_path: Path) -> Optional[Path]:
    """
    获取文件夹中的第一个NFO文件
    
    Args:
        folder_path: 文件夹路径
        
    Returns:
        NFO文件路径
    """
    for item in folder_path.iterdir():
        if is_nfo_file(item):
            return item
    return None

def sanitize_folder_name(name: str) -> str:
    """
    净化文件夹名称，移除不合法字符
    
    Args:
        name: 原始名称
        
    Returns:
        净化后的名称
    """
    # Windows下的非法字符: \ / : * ? " < > |
    invalid_chars = {'\\', '/', ':', '*', '?', '"', '<', '>', '|'}
    
    # 替换非法字符为空格
    result = ''.join(' ' if c in invalid_chars else c for c in name)
    
    # 移除前后空格
    result = result.strip()
    
    # 如果为空，返回默认名称
    return result if result else "unnamed"

def format_folder_name(title: str, config) -> str:
    """
    格式化文件夹名称
    
    Args:
        title: 原始标题
        config: 配置对象
        
    Returns:
        格式化后的文件夹名称
    """
    if not title:
        return "unnamed"
        
    # 按-分割
    parts = title.split('-')
    
    # 如果分割后的部分超过4个，只保留前4个
    if len(parts) > 4:
        parts = parts[:3] + [parts[-1]]
        
    # 对最后一部分进行长度限制
    if parts:
        parts[-1] = parts[-1][:config.TITLE_MAX_LENGTH]
        
    # 净化每个部分的名称
    parts = [sanitize_folder_name(part) for part in parts]
    
    return '-'.join(parts)