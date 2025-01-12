"""
清理操作计划生成器
"""
from pathlib import Path
from typing import List, Dict, Set
from core.helpers import (
    get_file_size_mb, is_image_file, is_nfo_file, is_video_file, get_delete_path
)
from .base_planner import BasePlanner

class CleanPlanner(BasePlanner):
    """清理操作计划生成器"""
    
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
        
    def _scan_non_video_folders(self, start_path: Path) -> List[Dict[str, str]]:
        """
        扫描并识别非视频文件夹
        
        Args:
            start_path: 起始路径
            
        Returns:
            需要移动到删除目录的操作列表
        """
        operations = []
    
        if not start_path.is_dir():
            return operations
            
        if '.delete' in start_path.parts:
            return operations
            
        if not self._is_video_folder(start_path):
            # 计算文件夹总大小
            total_size = sum(get_file_size_mb(f) for f in start_path.rglob('*') if f.is_file())
            operations.append({
                "function": "func1",
                "action": "MOVE",
                "source": str(start_path),
                "destination": str(get_delete_path(self.root_dir, start_path)),
                "file_size": round(total_size, 2)  # 保留两位小数
            })
        else:
            for item in start_path.iterdir():
                if item.is_dir():
                    operations.extend(self._scan_non_video_folders(item))
                        
        return operations
        
    def _is_useful_image(self, image_path: Path, video_names: Set[str]) -> bool:
        """
        判断图片文件是否有用
        
        Args:
            image_path: 图片文件路径
            video_names: 视频文件名集合（用于前缀匹配）
            
        Returns:
            图片是否有用
        """
        name = image_path.stem.lower()
        
        # 检查是否为保留的关键字名称
        if name in self.config.VALID_IMAGE_KEYWORDS:
            return True
            
        # 检查是否与视频文件名匹配
        for video_name in video_names:
            if (len(video_name) >= self.config.NFO_MATCH_LENGTH and
                name.startswith(video_name[:self.config.NFO_MATCH_LENGTH])):
                return True
                
        return False
        
    def _is_useful_nfo(self, nfo_path: Path, video_names: Set[str]) -> bool:
        """
        判断NFO文件是否有用
        
        Args:
            nfo_path: NFO文件路径
            video_names: 视频文件名集合
            
        Returns:
            NFO文件是否有用
        """
        name = nfo_path.stem.lower()
        
        for video_name in video_names:
            if (len(video_name) >= self.config.NFO_MATCH_LENGTH and
                name.startswith(video_name[:self.config.NFO_MATCH_LENGTH])):
                return True
                
        return False
        
    def _scan_video_folder_files(self, folder_path: Path) -> List[Dict[str, str]]:
        """
        扫描视频文件夹内的文件，生成清理计划
        
        Args:
            folder_path: 文件夹路径
            
        Returns:
            需要移动到删除目录的操作列表
        """
        operations = []
        
        if not folder_path.is_dir() or '.delete' in folder_path.parts:
            return operations
            
        video_names = set()
        for item in folder_path.iterdir():
            if is_video_file(item, self.config):
                video_names.add(item.stem.lower())
                
        if not video_names and not self._is_video_folder(folder_path):
            for item in folder_path.iterdir():
                if item.is_dir():
                    operations.extend(self._scan_video_folder_files(item))
            return operations
                
        for item in folder_path.iterdir():
            if item.is_dir():
                operations.extend(self._scan_video_folder_files(item))
                continue
                    
            if is_video_file(item, self.config):
                continue
                    
            if is_image_file(item, self.config):
                if not self._is_useful_image(item, video_names):
                    operations.append({
                        "function": "func2",
                        "action": "MOVE",
                        "source": str(item),
                        "destination": str(get_delete_path(self.root_dir, item)),
                        "file_size": round(get_file_size_mb(item), 2)
                    })
                continue
                    
            if is_nfo_file(item):
                if not self._is_useful_nfo(item, video_names):
                    operations.append({
                        "function": "func2",
                        "action": "MOVE",
                        "source": str(item),
                        "destination": str(get_delete_path(self.root_dir, item)),
                        "file_size": round(get_file_size_mb(item), 2)
                    })
                continue
                    
            operations.append({
                "function": "func2",
                "action": "MOVE",
                "source": str(item),
                "destination": str(get_delete_path(self.root_dir, item)),
                "file_size": round(get_file_size_mb(item), 2)
            })
            
        return operations
        
    def generate_clean_folders_plan(self) -> List[Dict[str, str]]:
        """
        生成清理非视频文件夹的操作计划（功能1）
        
        Returns:
            操作计划列表
        """
        return self._scan_non_video_folders(self.root_dir)
        
    def generate_clean_files_plan(self) -> List[Dict[str, str]]:
        """
        生成清理视频文件夹内文件的操作计划（功能2）
        
        Returns:
            操作计划列表
        """
        return self._scan_video_folder_files(self.root_dir) 