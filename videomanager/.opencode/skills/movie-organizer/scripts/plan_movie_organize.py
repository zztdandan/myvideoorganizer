#!/usr/bin/env python3
"""
movie-organizer: plan_movie_organize.py
扫描电影文件夹并生成整理计划
"""

import argparse
import json
import re
from pathlib import Path
from datetime import datetime
import sys

sys.path.insert(0, str(Path(__file__).parent))
from helpers import (
    extract_technical_info, build_movie_filename,
    is_subtitle_file, extract_subtitle_language,
    is_image_file, is_video_file
)


def parse_args():
    parser = argparse.ArgumentParser(description="扫描电影目录并生成整理计划")
    parser.add_argument("--root", required=True, help="电影根目录")
    parser.add_argument("--ai-analysis", required=True, help="AI分析结果（JSON字符串）")
    parser.add_argument("--force-reorganize", type=bool, default=False, help="强制重新整理")
    parser.add_argument("--output", required=True, help="计划文件输出目录")
    return parser.parse_args()


def parse_ai_analysis(analysis_json: str) -> dict:
    """解析AI分析结果"""
    import json
    try:
        return json.loads(analysis_json)
    except json.JSONDecodeError:
        return {
            "chinese_name": None,
            "english_name": "Unknown",
            "year": 0,
            "confidence": 0
        }


def is_already_organized(folder_name: str) -> bool:
    """检查文件夹是否已经整理过（包含 .fixed 后缀）"""
    return ".fixed" in folder_name.lower()


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


def build_new_folder_name(chinese_name: str | None, english_name: str, year: int) -> str:
    """构建新的文件夹名"""
    parts = []
    
    if chinese_name:
        parts.append(chinese_name)
    
    parts.append(english_name)
    parts.append(f"({year})")
    parts.append(".fixed")
    
    return ".".join(parts)


def scan_movie_folder(folder: Path, ai_data: dict, root_path: Path) -> list:
    """扫描单个电影文件夹，生成整理操作"""
    operations = []
    
    chinese_name = ai_data.get("chinese_name")
    english_name = ai_data.get("english_name", "Unknown")
    year = ai_data.get("year", 0)
    
    if not english_name or english_name == "Unknown":
        return operations
    
    # 构建新文件夹名
    new_folder_name = build_new_folder_name(chinese_name, english_name, year)
    new_folder_path = root_path / new_folder_name
    
    # 如果目标已存在，跳过
    if new_folder_path.exists() and new_folder_path != folder:
        return operations
    
    # 文件夹重命名操作
    if folder.name != new_folder_name:
        folder_size = get_folder_size(folder)
        operations.append({
            "func": "movie_organize",
            "action": "MOVE",
            "source": str(folder),
            "destination": str(new_folder_path),
            "size_mb": folder_size,
            "item_type": "folder",
            "created_at": datetime.now().isoformat()
        })
        current_folder = new_folder_path
    else:
        current_folder = folder
    
    # 扫描文件夹内的文件
    try:
        for item in folder.iterdir():
            if not item.is_file():
                continue
            
            filename = item.name
            new_filename = None
            
            if is_video_file(filename):
                # 视频文件重命名
                tech_info = extract_technical_info(filename)
                new_filename = build_movie_filename(english_name, year, tech_info, item.suffix)
            
            elif is_subtitle_file(filename):
                # 字幕文件保留语言标识
                lang = extract_subtitle_language(filename)
                if lang:
                    new_filename = f"{english_name}.{year}.{lang}{item.suffix}"
                else:
                    new_filename = f"{english_name}.{year}{item.suffix}"
            
            elif is_image_file(filename):
                # 图片文件保留关键词
                name_lower = filename.lower()
                if "poster" in name_lower:
                    new_filename = f"poster{item.suffix}"
                elif "fanart" in name_lower or "backdrop" in name_lower:
                    new_filename = f"fanart{item.suffix}"
                elif "banner" in name_lower:
                    new_filename = f"banner{item.suffix}"
                elif "clearart" in name_lower:
                    new_filename = f"clearart{item.suffix}"
                elif "logo" in name_lower:
                    new_filename = f"logo{item.suffix}"
                elif "thumb" in name_lower:
                    new_filename = f"thumb{item.suffix}"
                else:
                    # 其他图片保留原名
                    continue
            
            elif item.suffix.lower() == ".nfo":
                # NFO 文件统一命名为 movie.nfo
                new_filename = "movie.nfo"
            
            if new_filename and new_filename != filename:
                file_size = round(item.stat().st_size / (1024 * 1024), 2) if item.exists() else 0
                operations.append({
                    "func": "movie_organize",
                    "action": "RENAME",
                    "source": str(item),
                    "destination": str(current_folder / new_filename),
                    "size_mb": file_size,
                    "item_type": "file",
                    "created_at": datetime.now().isoformat()
                })
    
    except OSError as e:
        print(f"Error scanning folder {folder}: {e}")
    
    return operations


def scan_movies(root_path: Path, ai_analysis: dict, force_reorganize: bool) -> list:
    """扫描电影目录"""
    operations = []
    
    try:
        for folder in root_path.iterdir():
            if not folder.is_dir():
                continue
            
            # 检查是否已整理
            if not force_reorganize and is_already_organized(folder.name):
                continue
            
            # 对于演示，使用相同的AI数据
            # 实际使用中，每个文件夹应该有自己的AI分析结果
            folder_operations = scan_movie_folder(folder, ai_analysis, root_path)
            operations.extend(folder_operations)
    
    except OSError as e:
        print(f"Error scanning directory: {e}")
    
    return operations


def save_plan(operations: list, output_dir: Path) -> Path:
    """保存计划到 JSON 文件"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    plan_file = output_dir / f"movie_organize_{timestamp}.json"
    
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
    
    ai_analysis = parse_ai_analysis(args.ai_analysis)
    output_dir = Path(args.output)
    
    print(f"Scanning: {root_path}")
    print(f"AI Analysis: {ai_analysis}")
    print(f"Force reorganize: {args.force_reorganize}")
    
    operations = scan_movies(root_path, ai_analysis, args.force_reorganize)
    
    if operations:
        plan_file = save_plan(operations, output_dir)
        total_size = sum(op["size_mb"] for op in operations)
        
        folder_ops = sum(1 for op in operations if op.get("item_type") == "folder")
        file_ops = sum(1 for op in operations if op.get("item_type") == "file")
        
        print(f"\nFound {len(operations)} operations ({total_size:.2f} MB)")
        print(f"  - Folder operations: {folder_ops}")
        print(f"  - File operations: {file_ops}")
        print(f"Plan saved to: {plan_file}")
    else:
        print("\nNo operations needed.")
    
    print(f"\nSUMMARY: {len(operations)} operations, {sum(op['size_mb'] for op in operations):.2f} MB")


if __name__ == "__main__":
    main()
