"""
操作执行器
"""
from pathlib import Path
from typing import List, Dict, Any, Tuple
import json
import shutil
from core.logger import logger
from core.helpers import ensure_dir

class OperationExecutor:
    """操作执行器"""
    
    def __init__(self, config):
        """
        初始化执行器
        
        Args:
            config: 配置对象
        """
        self.config = config
        
    def execute_operation(self, operation: Dict[str, str]) -> bool:
        """
        执行单个操作
        
        Args:
            operation: 操作信息字典
            
        Returns:
            操作是否成功
        """
        action = operation['action']
        source = Path(operation['source'])
        destination = Path(operation['destination'])
        
        try:
            if action == 'MOVE':
                if not source.exists():
                    logger.warning(f"Source does not exist: {source}")
                    return False
                    
                # 确保目标目录存在
                ensure_dir(destination.parent)
                
                # 移动文件或目录
                shutil.move(str(source), str(destination))
                logger.info(f"Moved: {source} -> {destination}")
                
            elif action == 'RENAME':
                if not source.exists():
                    logger.warning(f"Source does not exist: {source}")
                    return False
                    
                # 确保目标目录存在
                ensure_dir(destination.parent)
                
                # 重命名文件
                source.rename(destination)
                logger.info(f"Renamed: {source} -> {destination}")
                
            else:
                logger.warning(f"Unknown action: {action}")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Operation failed: {str(e)}")
            return False
            
    def execute_from_file(self, json_path: str) -> Tuple[int, int]:
        """
        从JSON文件执行操作
        
        Args:
            json_path: JSON文件路径
            
        Returns:
            成功和失败的操作数量元组
        """
        success_count = 0
        failure_count = 0
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                operations = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load JSON file: {str(e)}")
            return 0, 0
            
        for operation in operations:
            if self.execute_operation(operation):
                success_count += 1
            else:
                failure_count += 1
                
        logger.info(f"Execution completed: {success_count} succeeded, "
                   f"{failure_count} failed")
        
        return success_count, failure_count
        
    def execute_operations(self, operations: List[Dict[str, str]]) -> Tuple[int, int]:
        """
        执行操作列表
        
        Args:
            operations: 操作列表
            
        Returns:
            成功和失败的操作数量元组
        """
        success_count = 0
        failure_count = 0
        
        for operation in operations:
            if self.execute_operation(operation):
                success_count += 1
            else:
                failure_count += 1
                
        logger.info(f"Execution completed: {success_count} succeeded, "
                   f"{failure_count} failed")
        
        return success_count, failure_count