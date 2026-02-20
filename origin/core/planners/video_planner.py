"""
视频处理操作计划生成器
"""
import xml.etree.ElementTree as ET

from pathlib import Path
from typing import List, Dict
from core.logger import logger
from core.helpers import (
    get_file_size_mb, is_video_folder, parse_nfo_file,
    get_first_nfo_file, format_folder_name, sanitize_folder_name
)
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
        if is_video_folder(start_path, self.config):
            # 获取第一个NFO文件
            nfo_file = get_first_nfo_file(start_path)
            if nfo_file:
                # 解析NFO文件
                actor_name, title, video_info = parse_nfo_file(nfo_file)
                
                # 检查视频信息
                if (video_info and 
                    video_info['width'] > self.config.BIG_VIDEO_WIDTH_THRESHOLD and 
                    video_info['aspect'] != '16:9'):
                    
                    # 获取演员分类
                    category = self.classifier.get_category(actor_name, self.config)
                    
                    if actor_name:
                        # 净化演员名称
                        actor_name = sanitize_folder_name(actor_name)
                        if actor_name and len(actor_name) > 0:
                            actor_first = actor_name[0]
                        else:
                            actor_first = "other"
                            
                        # 构造新的路径：BIG/分类/演员首字/演员名/标题
                        new_path = (self.config.get_big_video_dir() / category / 
                                  actor_first / actor_name / 
                                  format_folder_name(title, self.config))
                    else:
                        # 未知演员使用99分类
                        new_path = (self.config.get_big_video_dir() / 
                                  self.config.UNKNOWN_ACTOR_CATEGORY / 
                                  format_folder_name(title, self.config))
                        
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