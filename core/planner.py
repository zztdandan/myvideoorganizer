"""
操作计划生成器
"""
from pathlib import Path
from typing import List, Dict, Any
from core.logger import logger
from core.helpers import ensure_dir
from .planners import (
    BasePlanner, CleanPlanner, RenamePlanner, ActorPlanner, VideoPlanner
)

class OperationPlanner(BasePlanner):
    """操作计划生成器"""
    
    def __init__(self, config):
        """
        初始化计划生成器
        
        Args:
            config: 配置对象
        """
        super().__init__(config)
        self.clean_planner = CleanPlanner(config)
        self.rename_planner = RenamePlanner(config)
        self.actor_planner = ActorPlanner(config)
        self.video_planner = VideoPlanner(config)
        
    def generate_clean_folders_plan(self) -> List[Dict[str, str]]:
        """
        生成清理非视频文件夹的操作计划（功能1）
        
        Returns:
            操作计划列表
        """
        return self.clean_planner.generate_clean_folders_plan()
        
    def generate_clean_files_plan(self) -> List[Dict[str, str]]:
        """
        生成清理视频文件夹内文件的操作计划（功能2）
        
        Returns:
            操作计划列表
        """
        return self.clean_planner.generate_clean_files_plan()
        
    def generate_rename_plan(self) -> List[Dict[str, str]]:
        """
        生成视频重命名操作计划（功能3）
        
        Returns:
            操作计划列表
        """
        return self.rename_planner.generate_rename_plan()
        
    def generate_actor_classify_plan(self) -> List[Dict[str, str]]:
        """
        生成按演员分类的操作计划（功能4）
        
        Returns:
            操作计划列表
        """
        return self.actor_planner.generate_actor_classify_plan()
        
    def generate_big_video_plan(self) -> List[Dict[str, str]]:
        """
        生成识别超宽视频的操作计划（功能5）
        
        Returns:
            操作计划列表
        """
        return self.video_planner.generate_big_video_plan()