#!/usr/bin/env python3
"""
video-big-detector: plan_big_video.py
扫描超宽视频文件夹并生成移动计划
"""

import argparse
import json
import re
from pathlib import Path
from datetime import datetime
import sys

sys.path.insert(0, str(Path(__file__).parent))
from classifier import ActorClassifier


def parse_args():
    parser = argparse.ArgumentParser(description="扫描超宽视频并生成移动计划")
    parser.add_argument("--root", required=True, help="目标根目录")
    parser.add_argument("--width-threshold", type=int, default=2000, help="宽度阈值（像素）")
    parser.add_argument("--big-dir", default="BIG", help="超宽视频目录名")
    parser.add_argument("--unknown-category", default="99", help="未知演员分类")
    parser.add_argument("--japanese-category", default="0", help="日文名演员分类")
    parser.add_argument("--title-max-length", type=int, default=10, help="标题最大长度")
    parser.add_argument("--output", required=True, help="计划文件输出目录")
    return parser.parse_args()


def parse_nfo(nfo_path: Path) -> dict:
    """解析 NFO 文件，提取视频宽度、演员和标题"""
    result = {"width": 0, "height": 0, "actors": [], "title": ""}
    
    try:
        content = nfo_path.read_text(encoding="utf-8", errors="ignore")
        
        # 提取分辨率
        width_match = re.search(r"<width>(\d+)</width>", content, re.IGNORECASE)
        height_match = re.search(r"<height>(\d+)</height>", content, re.IGNORECASE)
        
        if width_match:
            result["width"] = int(width_match.group(1))
        if height_match:
            result["height"] = int(height_match.group(1))
        
        # 如果 NFO 中没有宽高，尝试从 fileinfo 中提取
        if result["width"] == 0:
            fileinfo_match = re.search(r"<fileinfo>.*?</fileinfo>", content, re.DOTALL | re.IGNORECASE)
            if fileinfo_match:
                fileinfo = fileinfo_match.group(0)
                width_match = re.search(r"<width>(\d+)</width>", fileinfo, re.IGNORECASE)
                height_match = re.search(r"<height>(\d+)</height>", fileinfo, re.IGNORECASE)
                if width_match:
                    result["width"] = int(width_match.group(1))
                if height_match:
                    result["height"] = int(height_match.group(1))
        
        # 提取演员
        actor_pattern = r"<actor>.*?<name>(.*?)</name>.*?</actor>"
        matches = re.findall(actor_pattern, content, re.DOTALL | re.IGNORECASE)
        for match in matches:
            actor = re.sub(r"<.*?>", "", match).strip()
            if actor and actor not in result["actors"]:
                result["actors"].append(actor)
        
        # 提取标题
        title_match = re.search(r"<title>(.*?)</title>", content, re.DOTALL | re.IGNORECASE)
        if title_match:
            result["title"] = re.sub(r"<.*?>", "", title_match.group(1)).strip()
    
    except Exception:
        pass
    
    return result


def is_big_video(width: int, height: int) -> bool:
    """判断是否为超宽视频（宽度>阈值且非16:9）"""
    if width <= 0 or height <= 0:
        return False
    
    # 检查宽高比是否为16:9（允许5%误差）
    aspect_ratio = width / height
    is_16_9 = abs(aspect_ratio - 16/9) < 0.05
    
    return not is_16_9


def find_first_nfo(folder: Path) -> Path | None:
    """查找文件夹中的第一个 NFO 文件"""
    try:
        for item in folder.iterdir():
            if item.is_file() and item.suffix.lower() == ".nfo":
                return item
    except OSError:
        pass
    return None


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


def scan_folders(root_path: Path, width_threshold: int, big_dir: str,
                 unknown_category: str, japanese_category: str, title_max_length: int) -> list:
    """扫描目录，找出超宽视频文件夹"""
    operations = []
    classifier = ActorClassifier()
    
    try:
        for folder in root_path.iterdir():
            if not folder.is_dir():
                continue
            
            if folder.name == big_dir:
                continue
            
            # 查找 NFO 文件
            nfo_path = find_first_nfo(folder)
            
            if not nfo_path:
                continue
            
            nfo_data = parse_nfo(nfo_path)
            
            # 检查是否为超宽视频
            if nfo_data["width"] <= width_threshold:
                continue
            
            if not is_big_video(nfo_data["width"], nfo_data["height"]):
                continue
            
            # 获取演员和分类
            actors = nfo_data["actors"]
            if not actors:
                actors = ["未知演员"]
            
            primary_actor = actors[0]
            classification = classifier.classify(primary_actor, unknown_category, japanese_category)
            
            # 处理标题
            title = nfo_data["title"]
            if not title:
                title = folder.name[:title_max_length]
            
            if len(title) > title_max_length:
                title = title[:title_max_length]
            
            # 构建目标路径
            category = classification["category"]
            initial = classification["initial"]
            actor_name = classification["actor_name"]
            
            if classification["type"] == "chinese" and initial:
                dest_folder = root_path / big_dir / category / initial / actor_name / title
            else:
                dest_folder = root_path / big_dir / category / actor_name / title
            
            folder_size = get_folder_size(folder)
            
            operation = {
                "func": "big_video",
                "action": "MOVE",
                "source": str(folder),
                "destination": str(dest_folder),
                "size_mb": folder_size,
                "width": nfo_data["width"],
                "height": nfo_data["height"],
                "actor": actor_name,
                "category": category,
                "title": title,
                "created_at": datetime.now().isoformat()
            }
            operations.append(operation)
    
    except OSError as e:
        print(f"Error scanning directory: {e}")
    
    return operations


def save_plan(operations: list, output_dir: Path) -> Path:
    """保存计划到 JSON 文件"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    plan_file = output_dir / f"big_video_{timestamp}.json"
    
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
    
    output_dir = Path(args.output)
    
    print(f"Scanning: {root_path}")
    print(f"Width threshold: {args.width_threshold}")
    print(f"Big directory: {args.big_dir}")
    
    operations = scan_folders(root_path, args.width_threshold, args.big_dir,
                             args.unknown_category, args.japanese_category,
                             args.title_max_length)
    
    if operations:
        plan_file = save_plan(operations, output_dir)
        total_size = sum(op["size_mb"] for op in operations)
        
        print(f"\nFound {len(operations)} big video folders ({total_size:.2f} MB)")
        print(f"Plan saved to: {plan_file}")
    else:
        print("\nNo big video folders found.")
    
    print(f"\nSUMMARY: {len(operations)} folders, {sum(op['size_mb'] for op in operations):.2f} MB")


if __name__ == "__main__":
    main()
