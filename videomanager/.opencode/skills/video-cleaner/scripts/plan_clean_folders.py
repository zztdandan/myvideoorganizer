#!/usr/bin/env python3
"""
video-cleaner: plan_clean_folders.py
扫描目录，将不含有效视频文件的文件夹标记为待清理
"""

import argparse
import json
import os
from pathlib import Path
from datetime import datetime


def parse_args():
    parser = argparse.ArgumentParser(description="扫描非视频文件夹")
    parser.add_argument("--root", required=True, help="目标根目录")
    parser.add_argument("--extensions", required=True, help="视频扩展名，逗号分隔")
    parser.add_argument("--min-size", type=int, required=True, help="最小视频大小(MB)")
    parser.add_argument("--delete-dir", default=".delete", help="删除目录名")
    parser.add_argument("--output", required=True, help="计划文件输出目录")
    return parser.parse_args()


def get_video_extensions(extensions_str: str) -> set:
    """解析扩展名字符串为集合"""
    return set(ext.strip().lower() for ext in extensions_str.split(",") if ext.strip())


def is_video_file(filepath: Path, video_extensions: set) -> bool:
    """判断是否为视频文件"""
    return filepath.suffix.lower() in video_extensions


def is_valid_video(filepath: Path, min_size_bytes: int) -> bool:
    """判断是否为有效视频（大小符合要求）"""
    try:
        return filepath.stat().st_size >= min_size_bytes
    except OSError:
        return False


def folder_has_valid_video(folder: Path, video_extensions: set, min_size_bytes: int) -> bool:
    """检查文件夹是否包含有效视频"""
    for item in folder.iterdir():
        if item.is_file() and is_video_file(item, video_extensions):
            if is_valid_video(item, min_size_bytes):
                return True
        elif item.is_dir():
            # 递归检查子目录
            if folder_has_valid_video(item, video_extensions, min_size_bytes):
                return True
    return False


def get_folder_size(folder: Path) -> float:
    """计算文件夹总大小(MB)"""
    total_size = 0
    try:
        for item in folder.rglob("*"):
            if item.is_file():
                try:
                    total_size += item.stat().st_size
                except OSError:
                    pass
    except OSError:
        pass
    return round(total_size / (1024 * 1024), 2)


def scan_folders(root_path: Path, video_extensions: set, min_size_mb: int, delete_dir: str):
    """扫描目录，找出不含有效视频的文件夹"""
    min_size_bytes = min_size_mb * 1024 * 1024
    operations = []
    
    # 获取一级子目录
    try:
        subdirs = [d for d in root_path.iterdir() if d.is_dir() and d.name != delete_dir]
    except OSError as e:
        print(f"Error reading directory {root_path}: {e}")
        return operations
    
    for folder in subdirs:
        # 检查是否包含有效视频
        if not folder_has_valid_video(folder, video_extensions, min_size_bytes):
            folder_size = get_folder_size(folder)
            
            operation = {
                "func": "clean_folders",
                "action": "MOVE",
                "source": str(folder),
                "destination": str(root_path / delete_dir / folder.name),
                "size_mb": folder_size,
                "created_at": datetime.now().isoformat()
            }
            operations.append(operation)
    
    return operations


def save_plan(operations: list, output_dir: Path) -> Path:
    """保存计划到 JSON 文件"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    plan_file = output_dir / f"clean_folders_{timestamp}.json"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(plan_file, "w", encoding="utf-8") as f:
        json.dump(operations, f, ensure_ascii=False, indent=2)
    
    return plan_file


def main():
    args = parse_args()
    
    root_path = Path(args.root).resolve()
    if not root_path.exists():
        print(f"Error: Root directory does not exist: {root_path}")
        exit(1)
    
    video_extensions = get_video_extensions(args.extensions)
    output_dir = Path(args.output)
    
    print(f"Scanning: {root_path}")
    print(f"Video extensions: {video_extensions}")
    print(f"Min video size: {args.min_size} MB")
    print(f"Delete directory: {args.delete_dir}")
    
    operations = scan_folders(root_path, video_extensions, args.min_size, args.delete_dir)
    
    if operations:
        plan_file = save_plan(operations, output_dir)
        total_size = sum(op["size_mb"] for op in operations)
        print(f"\nFound {len(operations)} non-video folders ({total_size:.2f} MB)")
        print(f"Plan saved to: {plan_file}")
    else:
        print("\nNo non-video folders found.")
    
    # 输出用于 agent 解析的摘要
    print(f"\nSUMMARY: {len(operations)} folders, {sum(op['size_mb'] for op in operations):.2f} MB")


if __name__ == "__main__":
    main()
