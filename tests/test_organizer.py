# tests/test_organizer.py
"""
视频整理功能单元测试
"""
import pytest
from pathlib import Path
from core.planner import OperationPlanner
from core.executor import OperationExecutor
from config import Config

class TestVideoOrganizer:
    """视频整理功能测试类"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """测试初始化"""
        self.config = Config.load_config()
        self.planner = OperationPlanner(self.config)
        self.executor = OperationExecutor(self.config)
        
    def test_func1_folder_cleanup(self):
        """
        功能1测试：视频文件夹初步整理
        使用方法：将此方法复制后修改路径运行，观察输出结果是否符合预期
        """
        # 生成清理计划
        operations = self.planner.generate_clean_folders_plan()
        
        # 打印计划内容供检查
        print("\n=== 功能1：文件夹清理计划 ===")
        for op in operations:
            print(f"\n将移动: {op['source']}")
            print(f"到: {op['destination']}")
            
        # 返回操作列表供进一步检查
        return operations
        
    def test_func2_file_cleanup(self):
        """
        功能2测试：视频文件夹内部文件清理
        使用方法：将此方法复制后修改路径运行，观察输出结果是否符合预期
        """
        # 生成清理计划
        operations = self.planner.generate_clean_files_plan()
        
        # 打印计划内容供检查
        print("\n=== 功能2：文件清理计划 ===")
        for op in operations:
            source_path = Path(op['source'])
            print(f"\n将移动: {source_path.name}")
            print(f"从: {source_path.parent}")
            print(f"到: {op['destination']}")
            
        return operations
        
    def test_func3_video_rename(self):
        """
        功能3测试：视频文件重命名
        使用方法：将此方法复制后修改路径运行，观察输出结果是否符合预期
        """
        # 生成重命名计划
        operations = self.planner.generate_rename_plan()
        
        # 打印计划内容供检查
        print("\n=== 功能3：视频重命名计划 ===")
        for op in operations:
            source_path = Path(op['source'])
            dest_path = Path(op['destination'])
            print(f"\n将重命名: {source_path.name}")
            print(f"为: {dest_path.name}")
            print(f"在目录: {source_path.parent}")
            
        return operations
        
    def execute_test_operations(self, operations, preview_only=True):
        """
        执行测试操作
        
        Args:
            operations: 操作列表
            preview_only: 是否仅预览不执行
            
        Returns:
            如果执行，返回成功和失败的操作数量
        """
        if preview_only:
            print("\n=== 预览模式：以上操作不会真正执行 ===")
            return None
            
        print("\n=== 执行操作 ===")
        success, failure = self.executor.execute_operations(operations)
        print(f"成功: {success}, 失败: {failure}")
        return success, failure

def run_test(function_name: str, execute: bool = False):
    """
    运行指定的测试功能
    
    Args:
        function_name: 功能名称 ('func1', 'func2', 或 'func3')
        execute: 是否执行操作（默认False，仅预览）
    """
    tester = TestVideoOrganizer()
    # 运行测试并获取操作列表
    if function_name == 'func1':
        operations = tester.test_func1_folder_cleanup()
    elif function_name == 'func2':
        operations = tester.test_func2_file_cleanup()
    elif function_name == 'func3':
        operations = tester.test_func3_video_rename()
    else:
        print(f"未知功能: {function_name}")
        return
        
    # 执行或预览操作
    tester.execute_test_operations(operations, not execute)

if __name__ == '__main__':
    """
    使用示例：
    1. 预览功能1的操作计划：
       run_test('func1')
    2. 执行功能2的操作：
       run_test('func2', True)
    """
    # 在这里直接调用你想测试的功能
    # 例如：run_test('func1')
    run_test('func1')