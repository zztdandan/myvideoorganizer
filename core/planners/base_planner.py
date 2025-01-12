"""
基础操作计划生成器
"""
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
from datetime import datetime
from core.logger import logger
from core.helpers import format_tree_view, ensure_dir

class BasePlanner:
    """基础操作计划生成器"""
    
    def __init__(self, config):
        """
        初始化计划生成器
        
        Args:
            config: 配置对象
        """
        self.config = config
        self.root_dir = Path(config.ROOT_DIR)
        # 确保操作记录目录存在
        self.operations_dir = Path(config.JSON_OUTPUT_DIR)
        ensure_dir(self.operations_dir)
        
    def save_operations(self, operations: List[Dict[str, str]], 
                       function_name: str) -> List[str]:
        """
        保存操作计划到JSON文件，如果操作数量超过配置的批次大小，则分批保存
        
        Args:
            operations: 操作列表
            function_name: 功能名称（用于文件命名）
            
        Returns:
            JSON文件路径列表
        """
        if not operations:
            return []
            
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        json_paths = []
        
        # 计算需要分成几个批次
        batch_size = self.config.JSON_BATCH_SIZE
        total_batches = (len(operations) + batch_size - 1) // batch_size
        
        # 如果只有一个批次，直接保存
        if total_batches == 1:
            json_path = self.operations_dir / f"{function_name}_{timestamp}.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(operations, f, indent=2, ensure_ascii=False)
            json_paths.append(str(json_path))
        else:
            # 分批保存
            for batch_num in range(total_batches):
                start_idx = batch_num * batch_size
                end_idx = min((batch_num + 1) * batch_size, len(operations))
                batch_operations = operations[start_idx:end_idx]
                
                json_path = self.operations_dir / f"{function_name}_{timestamp}_batch{batch_num + 1:03d}.json"
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(batch_operations, f, indent=2, ensure_ascii=False)
                json_paths.append(str(json_path))
                
        return json_paths
        
    def preview_operations(self, operations: List[Dict[str, str]]) -> bool:
        """
        预览操作计划并等待确认
        
        Args:
            operations: 操作列表
            
        Returns:
            用户是否确认执行
        """
        if not operations:
            logger.info("No operations to preview.")
            return False
                
        print("\nPlanned Operations:")
        for op in operations:
            print(f"\n{op['action']}:")
            print(f"From: {op['source']}")
            print(f"To: {op['destination']}")
            print(f"Size: {op['file_size']} MB")
                
        move_ops = [op for op in operations if op['action'] == 'MOVE']
        if move_ops:
            print("\nTree view of affected folders:")
            for op in move_ops:
                source = Path(op['source'])
                if source.exists():
                    tree_lines = format_tree_view(source)
                    print('\n'.join(tree_lines))
                        
        confirm = input("\nDo you want to proceed with these operations? (y/N): ")
        return confirm.lower() == 'y' 