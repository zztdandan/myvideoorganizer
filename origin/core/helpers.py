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

def extract_technical_info(filename: str) -> Dict[str, str]:
    """
    从视频文件名中提取技术信息
    
    Args:
        filename: 视频文件名（不含扩展名）
        
    Returns:
        包含技术信息的字典
        
    @process:
        1. 识别分辨率信息（720p, 1080p, 2160p等）
        2. 识别视频编码（H264, H265, HEVC等）
        3. 识别音频编码（DTS, AC3, AAC等）
        4. 识别其他信息（BluRay, WEB-DL, REMUX等）
    """
    import re
    
    tech_info = {
        'resolution': '',
        'video_codec': '',
        'audio_codec': '',
        'source': '',
        'other': []
    }
    
    filename_upper = filename.upper()
    
    # 提取分辨率
    resolution_patterns = [
        r'\b(2160P|4K|UHD)\b',
        r'\b(1080P|FHD)\b',
        r'\b(720P|HD)\b',
        r'\b(480P|SD)\b'
    ]
    for pattern in resolution_patterns:
        match = re.search(pattern, filename_upper)
        if match:
            tech_info['resolution'] = match.group(1)
            break
    
    # 提取视频编码
    video_codec_patterns = [
        r'\b(H\.?265|HEVC|X265)\b',
        r'\b(H\.?264|AVC|X264)\b',
        r'\b(VP9)\b',
        r'\b(AV1)\b'
    ]
    for pattern in video_codec_patterns:
        match = re.search(pattern, filename_upper)
        if match:
            tech_info['video_codec'] = match.group(1)
            break
    
    # 提取音频编码
    audio_patterns = [
        r'\b(TRUEHD[.\s]*7[.\s]*1[.\s]*ATMOS|TRUEHD)\b',
        r'\b(DTS-HD[.\s]*MA[.\s]*7[.\s]*1|DTS-HD[.\s]*MA)\b',
        r'\b(DTS[.\s]*7[.\s]*1|DTS)\b',
        r'\b(DD[P+]?5[.\s]*1|DDP5[.\s]*1|AC3)\b',
        r'\b(AAC[.\s]*5[.\s]*1|AAC)\b',
        r'\b(ATMOS)\b',
        r'\b(FLAC)\b'
    ]
    for pattern in audio_patterns:
        match = re.search(pattern, filename_upper)
        if match:
            tech_info['audio_codec'] = match.group(1).replace(' ', '.')
            break
    
    # 提取来源信息
    source_patterns = [
        r'\b(BLURAY[.\s]*REMUX|REMUX)\b',
        r'\b(BLURAY|BLU-RAY|BDRIP|BDREMUX)\b',
        r'\b(WEB-DL|WEBDL|WEB[.\s]*DL)\b',
        r'\b(WEBRIP|WEB[.\s]*RIP)\b',
        r'\b(HDTV)\b',
        r'\b(DVDRIP)\b'
    ]
    for pattern in source_patterns:
        match = re.search(pattern, filename_upper)
        if match:
            tech_info['source'] = match.group(1).replace(' ', '-')
            break
    
    # 提取其他特殊信息
    other_patterns = [
        r'\b(EXTENDED)\b',
        r'\b(IMAX)\b',
        r'\b(REMASTERED)\b',
        r'\b(HYBRID)\b',
        r'\b(DV|DOLBY[.\s]*VISION)\b',
        r'\b(HDR10\+?|HDR)\b',
        r'\b(3D)\b'
    ]
    for pattern in other_patterns:
        match = re.search(pattern, filename_upper)
        if match:
            tech_info['other'].append(match.group(1).replace(' ', '.'))
    
    return tech_info

def build_movie_filename(english_name: str, year: str, tech_info: Dict[str, str], extension: str) -> str:
    """
    根据标准信息和技术信息构建新文件名
    
    Args:
        english_name: 英文电影名（已用点分隔）
        year: 年份
        tech_info: 技术信息字典
        extension: 文件扩展名（包含点）
        
    Returns:
        完整的文件名
        
    @process:
        1. 以英文名开始
        2. 添加年份
        3. 按顺序添加技术信息：分辨率、来源、视频编码、音频编码、其他
        4. 添加扩展名
    """
    parts = [english_name, year]
    
    # 添加技术信息（按优先级顺序）
    if tech_info.get('resolution'):
        parts.append(tech_info['resolution'])
        
    if tech_info.get('source'):
        parts.append(tech_info['source'])
        
    if tech_info.get('video_codec'):
        parts.append(tech_info['video_codec'])
        
    if tech_info.get('audio_codec'):
        parts.append(tech_info['audio_codec'])
        
    # 添加其他信息
    if tech_info.get('other'):
        parts.extend(tech_info['other'])
    
    # 连接所有部分并添加扩展名
    return '.'.join(parts) + extension

def parse_movie_folder_name(folder_name: str) -> Dict[str, str]:
    """
    解析文件夹名称提取可能的电影信息
    
    Args:
        folder_name: 文件夹名称
        
    Returns:
        包含提取信息的字典
        
    @process:
        1. 移除常见的网站标记、发布组等无关信息
        2. 尝试提取年份（括号内的4位数字）
        3. 尝试分离中文和英文名称
        4. 清理特殊字符和多余空格
    """
    import re
    
    info = {
        'chinese_name': '',
        'english_name': '',
        'year': '',
        'original': folder_name
    }
    
    # 移除常见的无关前缀和括号内容
    # 例如：【更多高清电影访问 www.xxx.com】、[xxx发布组]等
    cleaned_name = folder_name
    
    # 移除【】括号及其内容
    cleaned_name = re.sub(r'【[^】]*】', '', cleaned_name)
    # 移除[]括号中的网站、发布组信息（但保留可能的电影信息）
    cleaned_name = re.sub(r'\[[^\]]*(?:www|com|net|org|发布|更多|高清|电影|访问)[^\]]*\]', '', cleaned_name, flags=re.IGNORECASE)
    # 移除[]括号中的音轨、字幕等描述信息
    cleaned_name = re.sub(r'\[[^\]]*(?:音轨|字幕|国语|粤语|英语|简|繁|中字)[^\]]*\]', '', cleaned_name, flags=re.IGNORECASE)
    
    # 提取年份（括号内的4位数字或直接在路径中的4位数字）
    year_match = re.search(r'\((\d{4})\)', cleaned_name)
    if year_match:
        info['year'] = year_match.group(1)
        # 移除年份部分
        cleaned_name = cleaned_name.replace(year_match.group(0), '').strip()
    
    # 尝试在文件名中查找年份（点分隔的）
    if not info['year']:
        year_match = re.search(r'[.\s](\d{4})[.\s]', cleaned_name)
        if year_match:
            info['year'] = year_match.group(1)
            # 从这个位置截断，后面通常是技术信息
            cleaned_name = cleaned_name[:year_match.start()].strip()
    
    # 尝试分离中文和英文
    # 如果包含中文字符
    if re.search(r'[\u4e00-\u9fff]', cleaned_name):
        # 查找中英文的分界点（通常是点、空格等）
        # 尝试找到类似 "中文名.English.Name" 或 "中文名[xxx].English.Name" 的模式
        
        # 先提取所有连续的中文部分
        chinese_parts = re.findall(r'[\u4e00-\u9fff]+', cleaned_name)
        info['chinese_name'] = ''.join(chinese_parts)
        
        # 尝试提取英文部分（通常在中文后面，可能用点分隔）
        # 移除中文和方括号内容
        temp = re.sub(r'[\u4e00-\u9fff]+', ' ', cleaned_name)
        temp = re.sub(r'\[[^\]]*\]', ' ', temp)
        
        # 查找连续的英文单词（可能用点或空格分隔）
        english_match = re.search(r'([A-Z][A-Za-z0-9.]*(?:[.\s]+[A-Z][A-Za-z0-9.]*)*)', temp)
        if english_match:
            english_name = english_match.group(1).strip()
            # 清理：移除开头/结尾的点，标准化分隔符
            english_name = english_name.strip('.')
            info['english_name'] = english_name
        else:
            # 如果没找到，清理后使用剩余部分
            temp = re.sub(r'[^\w\s.]', ' ', temp)
            temp = ' '.join(temp.split())
            info['english_name'] = temp.strip()
    else:
        # 没有中文，全部作为英文名
        # 清理特殊字符
        temp = re.sub(r'[^\w\s.]', ' ', cleaned_name)
        temp = ' '.join(temp.split())
        info['english_name'] = temp.strip()
    
    return info

def get_subtitle_extensions() -> set:
    """
    获取字幕文件扩展名集合
    
    Returns:
        字幕扩展名集合
    """
    return {'.srt', '.ass', '.ssa', '.sub', '.idx', '.vtt', '.smi'}

def is_subtitle_file(file_path: Path) -> bool:
    """
    判断文件是否为字幕文件
    
    Args:
        file_path: 文件路径
        
    Returns:
        是否为字幕文件
    """

    return file_path.is_file() and file_path.suffix.lower() in get_subtitle_extensions()

def is_movie_folder_organized(folder_name: str, video_files: List[Path]) -> bool:
    """
    判断电影文件夹是否已经整理为标准格式
    
    Args:
        folder_name: 文件夹名称
        video_files: 视频文件列表
        
    Returns:
        是否已经整理好
        
    @process:
        1. 检查文件夹名是否以.fixed结尾
        2. 这是最简单可靠的判断方式
    """
    # 简单检查：文件夹名是否以.fixed结尾
    return folder_name.endswith('.fixed')