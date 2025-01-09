"""
日志模块: 统一的日志记录接口
"""
import logging
import sys
from pathlib import Path
from datetime import datetime

def setup_logger(name: str = __name__) -> logging.Logger:
    """
    设置日志器
    
    Args:
        name: 日志器名称
        
    Returns:
        配置好的日志器实例
    """
    # 创建日志器
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # 如果已经有处理器，说明已经初始化过，直接返回
    if logger.handlers:
        return logger
        
    # 创建日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # 文件处理器
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    file_handler = logging.FileHandler(
        log_dir / f"organizer_{datetime.now():%Y%m%d}.log",
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # 添加处理器
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

# 创建默认日志器
logger = setup_logger("video_organizer")