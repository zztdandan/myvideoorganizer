"""
重命名操作计划生成器
"""
from pathlib import Path
from typing import List, Dict
from core.helpers import get_file_size_mb, is_video_file
from .base_planner import BasePlanner

class RenamePlanner(BasePlanner):
    """重命名操作计划生成器"""
    
    def _get_common_prefix(self, names: List[str]) -> str:
        """
        获取文件名的公共前缀
        
        Args:
            names: 文件名列表
            
        Returns:
            公共前缀
        """
        if not names:
            return ""
            
        # 找出最短的名字长度
        min_len = min(len(name) for name in names)
        
        # 逐字符比较
        for i in range(min_len):
            char = names[0][i]
            if not all(name[i] == char for name in names):
                return names[0][:i]
                
        return names[0][:min_len]
        
    def _scan_videos_for_rename(self, folder_path: Path) -> List[Dict[str, str]]:
        """
        扫描需要重命名的视频文件
        
        Args:
            folder_path: 文件夹路径
            
        Returns:
            重命名操作列表
        """
        operations = []
        
        if not folder_path.is_dir() or '.delete' in folder_path.parts:
            return operations
                
        videos = [
            item for item in folder_path.iterdir()
            if is_video_file(item, self.config)
        ]
        
        if len(videos) > 1:
            names = [v.stem for v in videos]
            common_prefix = self._get_common_prefix(names)
            pattern = self.config.RENAME_PATTERNS[self.config.DEFAULT_RENAME_PATTERN]
            
            for idx, video in enumerate(videos):
                if idx >= len(pattern):
                    break
                
                # 检查文件名是否已经包含cd后缀
                current_name = video.stem.lower()
                if '-cd' in current_name:
                    continue
                        
                new_name = f"{common_prefix}-cd{pattern[idx]}{video.suffix}"
                new_path = video.parent / new_name
                
                if str(new_path) != str(video):
                    operations.append({
                        "function": "func3",
                        "action": "RENAME",
                        "source": str(video),
                        "destination": str(new_path),
                        "file_size": round(get_file_size_mb(video), 2)
                    })
                        
        for item in folder_path.iterdir():
            if item.is_dir():
                operations.extend(self._scan_videos_for_rename(item))
                
        return operations
        
    def generate_rename_plan(self) -> List[Dict[str, str]]:
        """
        生成视频重命名操作计划（功能3）
        
        Returns:
            操作计划列表
        """
        return self._scan_videos_for_rename(self.root_dir) 