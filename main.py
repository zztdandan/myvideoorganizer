"""
主程序入口：提供命令行接口和HTTP服务接口
"""
import argparse
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs
import threading

from config import Config
from core.logger import logger
from core.planner import OperationPlanner
from core.executor import OperationExecutor

class VideoOrganizerCLI:
    """视频整理器命令行接口"""
    
    def __init__(self):
        """初始化CLI"""
        self.config = Config.load_config()
        self.planner = OperationPlanner(self.config)
        self.executor = OperationExecutor(self.config)
        
    def _handle_preview_mode(self, operations: List[Dict[str, str]]) -> bool:
        """
        处理预览模式
        
        Args:
            operations: 操作列表
            
        Returns:
            是否执行成功
        """
        if not operations:
            logger.info("No operations planned.")
            return True
            
        if self.planner.preview_operations(operations):
            success, failure = self.executor.execute_operations(operations)
            return failure == 0
        return True
        
    def _handle_json_mode(self, operations: List[Dict[str, str]], 
                         function_name: str) -> bool:
        """
        处理JSON模式
        
        Args:
            operations: 操作列表
            function_name: 功能名称
            
        Returns:
            是否执行成功
        """
        if not operations:
            logger.info("No operations planned.")
            return True
            
        json_path = self.planner.save_operations(operations, function_name)
        if json_path:
            logger.info(f"Operations saved to: {json_path}")
            return True
        return False
        
    def execute_json(self, json_path: str) -> bool:
        """
        执行JSON文件中的操作
        
        Args:
            json_path: JSON文件路径
            
        Returns:
            是否执行成功
        """
        success, failure = self.executor.execute_from_file(json_path)
        return failure == 0
        
    def run_function(self, function: str, mode: str, json_path: Optional[str] = None) -> bool:
        """
        运行指定功能
        
        Args:
            function: 功能名称
            mode: 执行模式 (preview/json)
            json_path: JSON文件路径（用于执行模式）
            
        Returns:
            是否执行成功
        """
        if json_path:
            return self.execute_json(json_path)
            
        operations = []
        if function == 'func1':
            operations = self.planner.generate_clean_folders_plan()
        elif function == 'func2':
            operations = self.planner.generate_clean_files_plan()
        elif function == 'func3':
            operations = self.planner.generate_rename_plan()
        else:
            logger.error(f"Unknown function: {function}")
            return False
            
        if mode == 'preview':
            return self._handle_preview_mode(operations)
        elif mode == 'json':
            return self._handle_json_mode(operations, function)
        else:
            logger.error(f"Unknown mode: {mode}")
            return False

class VideoOrganizerHandler(BaseHTTPRequestHandler):
    """HTTP请求处理器"""
    
    def __init__(self, *args, **kwargs):
        self.cli = VideoOrganizerCLI()
        super().__init__(*args, **kwargs)
        
    def _send_response(self, status_code: int, message: str):
        """发送HTTP响应"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        response = json.dumps({"message": message})
        self.wfile.write(response.encode())
        
    def do_GET(self):
        """处理GET请求"""
        if self.path.startswith('/organize'):
            try:
                # 解析查询参数
                query = parse_qs(self.path.split('?')[1]) if '?' in self.path else {}
                function = query.get('function', [''])[0]
                mode = query.get('mode', [''])[0]
                json_path = query.get('json_path', [''])[0]
                
                if not function and not json_path:
                    self._send_response(400, "Missing function or json_path parameter")
                    return
                    
                # 执行操作
                success = self.cli.run_function(function, mode, json_path)
                
                if success:
                    self._send_response(200, "Operation completed successfully")
                else:
                    self._send_response(500, "Operation failed")
                    
            except Exception as e:
                self._send_response(500, f"Error: {str(e)}")
        else:
            self._send_response(404, "Not found")

def run_http_server(port: int = 8080):
    """运行HTTP服务器"""
    server = HTTPServer(('localhost', port), VideoOrganizerHandler)
    logger.info(f"Starting HTTP server on port {port}")
    server.serve_forever()

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Video folder organizer')
    
    parser.add_argument('function', nargs='?', choices=['func1', 'func2', 'func3'],
                      help='Function to execute')
    parser.add_argument('--mode', choices=['preview', 'json'],
                      default='preview', help='Execution mode')
    parser.add_argument('--json', help='JSON file path for execution')
    parser.add_argument('--http', action='store_true',
                      help='Start HTTP server')
    parser.add_argument('--port', type=int, default=8080,
                      help='HTTP server port')
    
    args = parser.parse_args()
    
    # 启动HTTP服务器
    if args.http:
        run_http_server(args.port)
        return
    
#     # 预览模式执行功能1
# GET http://localhost:8080/organize?function=func1&mode=preview

# # JSON模式执行功能2
# GET http://localhost:8080/organize?function=func2&mode=json

# # 执行JSON文件
# GET http://localhost:8080/organize?json_path=/path/to/operations.json
    # 命令行模式
    cli = VideoOrganizerCLI()
    
    success = cli.run_function(args.function, args.mode, args.json)
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()