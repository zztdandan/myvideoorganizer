"""
视频处理操作计划生成器
"""
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import xml.etree.ElementTree as ET
from core.logger import logger
from core.helpers import get_file_size_mb, is_nfo_file, is_video_file
from core.classifier import ActorClassifier
from .base_planner import BasePlanner

class VideoPlanner(BasePlanner):
    """视频处理操作计划生成器"""
    
    def __init__(self, config):
        """
        初始化计划生成器
        
        Args:
            config: 配置对象
        """
        super().__init__(config)
        self.classifier = ActorClassifier()
        
    def _parse_nfo_file(self, nfo_path: Path) -> Tuple[Optional[str], Optional[str], Optional[Dict]]:
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
            
    def _get_first_nfo_file(self, folder_path: Path) -> Optional[Path]:
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
        
    def _sanitize_folder_name(self, name: str) -> str:
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
        
    def _format_folder_name(self, title: str) -> str:
        """
        格式化文件夹名称
        
        Args:
            title: 原始标题
            
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
            parts[-1] = parts[-1][:self.config.TITLE_MAX_LENGTH]
            
        # 净化每个部分的名称
        parts = [self._sanitize_folder_name(part) for part in parts]
        
        return '-'.join(parts)
        
    def _is_video_folder(self, folder_path: Path) -> bool:
        """
        判断是否为视频文件夹（递归检查）
        
        Args:
            folder_path: 文件夹路径
            
        Returns:
            是否为视频文件夹
        """
        if not folder_path.is_dir():
            return False
            
        # 检查当前文件夹中的文件
        for item in folder_path.iterdir():
            if is_video_file(item, self.config):
                return True
            if item.is_dir() and self._is_video_folder(item):
                return True
                
        return False
        
    def _scan_big_video_folders(self, start_path: Path) -> List[Dict[str, str]]:
        """
        扫描超宽视频文件夹并生成移动计划
        
        Args:
            start_path: 起始路径
            
        Returns:
            操作计划列表
        """
        operations = []
        
        if not start_path.is_dir() or '.delete' in start_path.parts:
            return operations
            
        # 如果当前文件夹是视频文件夹
        if self._is_video_folder(start_path):
            # 获取第一个NFO文件
            nfo_file = self._get_first_nfo_file(start_path)
            if nfo_file:
                # 解析NFO文件
                actor_name, title, video_info = self._parse_nfo_file(nfo_file)
                
                # 检查视频信息
                if (video_info and 
                    video_info['width'] > self.config.BIG_VIDEO_WIDTH_THRESHOLD and 
                    video_info['aspect'] != '16:9'):
                    
                    # 获取演员分类
                    category = self.classifier.get_category(actor_name, self.config)
                    
                    if actor_name:
                        # 净化演员名称
                        actor_name = self._sanitize_folder_name(actor_name)
                        if actor_name and len(actor_name) > 0:
                            actor_first = actor_name[0]
                        else:
                            actor_first = "other"
                            
                        # 构造新的路径：BIG/分类/演员首字/演员名/标题
                        new_path = (self.config.get_big_video_dir() / category / 
                                  actor_first / actor_name / 
                                  self._format_folder_name(title))
                    else:
                        # 未知演员使用99分类
                        new_path = (self.config.get_big_video_dir() / 
                                  self.config.UNKNOWN_ACTOR_CATEGORY / 
                                  self._format_folder_name(title))
                        
                    operations.append({
                        "function": "func5",
                        "action": "MOVE",
                        "source": str(start_path),
                        "destination": str(new_path),
                        "file_size": round(sum(get_file_size_mb(f) for f in start_path.rglob('*') if f.is_file()), 2)
                    })
        
        # 递归处理子文件夹
        for item in start_path.iterdir():
            if item.is_dir():
                operations.extend(self._scan_big_video_folders(item))
                
        return operations
        
    def generate_big_video_plan(self) -> List[Dict[str, str]]:
        """
        生成识别超宽视频的操作计划（功能5）
        
        Returns:
            操作计划列表
        """
        return self._scan_big_video_folders(self.root_dir) 