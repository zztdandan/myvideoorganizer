#!/usr/bin/env python3
"""
video-cleaner: plan_clean_files.py
扫描视频文件夹，清理无用文件
"""

import argparse
import json
import os
from pathlib import Path
from datetime import datetime


def parse_args():
    parser = argparse.ArgumentParser(description="清理视频文件夹中的无用文件")
    parser.add_argument("--root", required=True, help="目标根目录")
    parser.add_argument("--video-extensions", required=True, help="视频扩展名，逗号分隔")
    parser.add_argument("--image-extensions", required=True, help="图片扩展名，逗号分隔")
    parser.add_argument("--valid-keywords", required=True, help="有效图片关键词，逗号分隔")
    parser.add_argument("--nfo-match-length", type=int, default=5, help="NFO文件名匹配长度")
    parser.add_argument("--delete-dir", default=".delete", help="删除目录名")
    parser.add_argument("--output", required=True, help="计划文件输出目录")
    return parser.parse_args()


def parse_comma_list(value: str) -> set:
    """解析逗号分隔的字符串为集合"""
    return set(item.strip().lower() for item in value.split(",") if item.strip())


def get_video_stems(folder: Path, video_extensions: set) -> set:
    """获取文件夹中所有视频文件的 stem（无扩展名）"""
    stems = set()
    try:
        for item in folder.iterdir():
            if item.is_file() and item.suffix.lower() in video_extensions:
                stems.add(item.stem)
    except OSError:
        pass
    return stems


def should_keep_image(filename: str, valid_keywords: set) -> bool:
    """判断图片是否应该保留"""
    name_lower = filename.lower()
    # 检查是否包含有效关键词
    for keyword in valid_keywords:
        if keyword in name_lower:
            return True
    return False


def should_keep_nfo(filename: str, video_stems: set, match_length: int) -> bool:
    """判断 NFO 文件是否应该保留"""
    name_lower = filename.lower()
    # 检查文件名前 N 个字符是否与某个视频文件名匹配
    prefix = name_lower[:match_length] if len(name_lower) >= match_length else name_lower
    prefix = Path(prefix).stem  # 去掉 .nfo
    
    for stem in video_stems:
        if stem.lower().startswith(prefix) or prefix.startswith(stem.lower()[:match_length]):
            return True
    return False


def should_keep_file(filepath: Path, video_extensions: set, image_extensions: set,
                     valid_keywords: set, video_stems: set, nfo_match_length: int) -> bool:
    """判断文件是否应该保留"""
    ext = filepath.suffix.lower()
    name = filepath.name
    
    # 视频文件：全部保留
    if ext in video_extensions:
        return True
    
    # 图片文件
    if ext in image_extensions:
        # 检查是否包含有效关键词或与视频名匹配
        if should_keep_image(name, valid_keywords):
            return True
        # 检查文件名前 N 个字符是否与视频匹配
        prefix = name[:nfo_match_length] if len(name) >= nfo_match_length else name
        prefix = Path(prefix).stem
        for stem in video_stems:
            if stem.lower().startswith(prefix.lower()):
                return True
        return False
    
    # NFO 文件
    if ext == ".nfo":
        return should_keep_nfo(name, video_stems, nfo_match_length)
    
    # 其他文件：删除
    return False


def scan_folder_for_files(folder: Path, root_path: Path, video_extensions: set,
                          image_extensions: set, valid_keywords: set,
                          nfo_match_length: int, delete_dir: str) -> list:
    """扫描单个文件夹中的无用文件"""
    operations = []
    
    # 获取视频文件 stems
    video_stems = get_video_stems(folder, video_extensions)
    
    # 如果没有视频文件，跳过
    if not video_stems:
        return operations
    
    try:
        for item in folder.iterdir():
            if not item.is_file():
                continue
            
            # 检查是否应该保留
            if should_keep_file(item, video_extensions, image_extensions,
                               valid_keywords, video_stems, nfo_match_length):
                continue
            
            # 应该删除
            try:
                file_size = item.stat().st_size / (1024 * 1024)  # MB
            except OSError:
                file_size = 0
            
            # 计算相对路径用于删除目录
            try:
                rel_path = item.relative_to(root_path)
                delete_path = root_path / delete_dir / rel_path
            except ValueError:
                delete_path = folder / delete_dir / item.name
            
            operation = {
                "func": "clean_files",
                "action": "MOVE",
                "source": str(item),
                "destination": str(delete_path),
                "size_mb": round(file_size, 2),
                "created_at": datetime.now().isoformat()
            }
            operations.append(operation)
    except OSError as e:
        print(f"Error scanning folder {folder}: {e}")
    
    return operations


def scan_all_folders(root_path: Path, video_extensions: set, image_extensions: set,
                     valid_keywords: set, nfo_match_length: int, delete_dir: str) -> list:
    """扫描所有包含视频的文件夹"""
    all_operations = []
    
    # 遍历所有子目录
    try:
        for folder in root_path.rglob("*"):
            if not folder.is_dir():
                continue
            if folder.name == delete_dir or delete_dir in folder.parts:
                continue
            
            operations = scan_folder_for_files(
                folder, root_path, video_extensions, image_extensions,
                valid_keywords, nfo_match_length, delete_dir
            )
            all_operations.extend(operations)
    except OSError as e:
        print(f"Error walking directory {root_path}: {e}")
    
    return all_operations


def save_plan(operations: list, output_dir: Path) -> Path:
    """保存计划到 JSON 文件"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    plan_file = output_dir / f"clean_files_{timestamp}.json"
    
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
    
    video_extensions = parse_comma_list(args.video_extensions)
    image_extensions = parse_comma_list(args.image_extensions)
    valid_keywords = parse_comma_list(args.valid_keywords)
    output_dir = Path(args.output)
    
    print(f"Scanning: {root_path}")
    print(f"Valid keywords: {valid_keywords}")
    print(f"NFO match length: {args.nfo_match_length}")
    
    operations = scan_all_folders(
        root_path, video_extensions, image_extensions,
        valid_keywords, args.nfo_match_length, args.delete_dir
    )
    
    if operations:
        plan_file = save_plan(operations, output_dir)
        total_size = sum(op["size_mb"] for op in operations)
        print(f"\nFound {len(operations)} files to clean ({total_size:.2f} MB)")
        print(f"Plan saved to: {plan_file}")
    else:
        print("\nNo files to clean.")
    
    # 输出摘要
    print(f"\nSUMMARY: {len(operations)} files, {sum(op['size_mb'] for op in operations):.2f} MB")


if __name__ == "__main__":
    main()
