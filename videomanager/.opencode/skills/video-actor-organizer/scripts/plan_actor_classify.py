#!/usr/bin/env python3
"""
video-actor-organizer: plan_actor_classify.py
扫描视频文件夹，按演员分类生成移动计划
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
    parser = argparse.ArgumentParser(description="扫描并生成演员分类计划")
    parser.add_argument("--root", required=True, help="目标根目录")
    parser.add_argument("--unknown-category", default="99", help="未知演员分类")
    parser.add_argument("--japanese-category", default="0", help="日文名演员分类")
    parser.add_argument("--title-max-length", type=int, default=10, help="标题最大长度")
    parser.add_argument("--output", required=True, help="计划文件输出目录")
    return parser.parse_args()


def parse_nfo(nfo_path: Path) -> dict:
    """解析 NFO 文件，提取演员和标题"""
    result = {"actors": [], "title": "", "is_fc2": False}
    
    try:
        content = nfo_path.read_text(encoding="utf-8", errors="ignore")
        
        # 检查是否是 FC2/PPV
        if "FC2" in content.upper() or "PPV" in content.upper():
            result["is_fc2"] = True
        
        # 提取演员名
        actor_patterns = [
            r"<actor>.*?<name>(.*?)</name>.*?</actor>",
            r"<actor>(.*?)</actor>",
            r"主演[:\s]*(.*?)[\n<]",
        ]
        
        for pattern in actor_patterns:
            matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                actor = re.sub(r"<.*?>", "", match).strip()
                if actor and actor not in result["actors"]:
                    result["actors"].append(actor)
        
        # 提取标题
        title_patterns = [
            r"<title>(.*?)</title>",
            r"<originaltitle>(.*?)</originaltitle>",
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                title = re.sub(r"<.*?>", "", match.group(1)).strip()
                if title:
                    result["title"] = title
                    break
    
    except Exception as e:
        pass
    
    return result


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


def find_first_nfo(folder: Path) -> Path | None:
    """查找文件夹中的第一个 NFO 文件"""
    try:
        for item in folder.iterdir():
            if item.is_file() and item.suffix.lower() == ".nfo":
                return item
    except OSError:
        pass
    return None


def extract_code_from_folder(folder_name: str) -> str:
    """从文件夹名提取视频编号（如 SSNI-123）"""
    # 匹配常见的视频编号格式
    patterns = [
        r"([A-Z]{2,6}-\d{2,4})",  # SSNI-123
        r"(\d{6,7}-\d{2,3})",       # 123456-789
        r"(FC2-\d+)",               # FC2-123456
        r"(FC2PPV-\d+)",            # FC2PPV-123456
    ]
    
    for pattern in patterns:
        match = re.search(pattern, folder_name.upper())
        if match:
            return match.group(1)
    
    return folder_name[:20]  # 返回前20字符作为标识


def scan_folders(root_path: Path, unknown_category: str, japanese_category: str,
                 title_max_length: int) -> list:
    """扫描目录，生成演员分类计划"""
    operations = []
    classifier = ActorClassifier()
    
    try:
        for folder in root_path.iterdir():
            if not folder.is_dir():
                continue
            
            # 查找 NFO 文件
            nfo_path = find_first_nfo(folder)
            
            actors = []
            title = ""
            is_fc2 = False
            
            if nfo_path:
                nfo_data = parse_nfo(nfo_path)
                actors = nfo_data["actors"]
                title = nfo_data["title"]
                is_fc2 = nfo_data["is_fc2"]
            
            # FC2/PPV 特殊处理
            if not actors and is_fc2:
                folder_name = folder.name.upper()
                if "FC2-PPV" in folder_name or "FC2PPV" in folder_name:
                    actors = ["FC2-PPV"]
                elif "FC2" in folder_name:
                    actors = ["FC2"]
                elif "PPV" in folder_name:
                    actors = ["PPV"]
            
            # 如果没有演员，使用文件夹名作为未知
            if not actors:
                actors = ["未知演员"]
            
            # 使用第一个演员进行分类
            primary_actor = actors[0]
            classification = classifier.classify(primary_actor, unknown_category, japanese_category)
            
            # 处理标题
            if not title:
                title = extract_code_from_folder(folder.name)
            
            # 截断标题
            if len(title) > title_max_length:
                title = title[:title_max_length]
            
            # 构建目标路径
            category = classification["category"]
            initial = classification["initial"]
            actor_name = classification["actor_name"]
            
            if classification["type"] == "chinese" and initial:
                dest_folder = root_path / category / initial / actor_name / title
            else:
                dest_folder = root_path / category / actor_name / title
            
            folder_size = get_folder_size(folder)
            
            operation = {
                "func": "actor_classify",
                "action": "MOVE",
                "source": str(folder),
                "destination": str(dest_folder),
                "size_mb": folder_size,
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
    plan_file = output_dir / f"actor_classify_{timestamp}.json"
    
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
    print(f"Unknown category: {args.unknown_category}")
    print(f"Japanese category: {args.japanese_category}")
    print(f"Title max length: {args.title_max_length}")
    
    operations = scan_folders(root_path, args.unknown_category,
                             args.japanese_category, args.title_max_length)
    
    if operations:
        plan_file = save_plan(operations, output_dir)
        total_size = sum(op["size_mb"] for op in operations)
        
        # 统计分类
        categories = {}
        for op in operations:
            cat = op["category"]
            categories[cat] = categories.get(cat, 0) + 1
        
        print(f"\nFound {len(operations)} folders to classify ({total_size:.2f} MB)")
        print(f"Categories: {categories}")
        print(f"Plan saved to: {plan_file}")
    else:
        print("\nNo folders found.")
    
    print(f"\nSUMMARY: {len(operations)} folders, {sum(op['size_mb'] for op in operations):.2f} MB")


if __name__ == "__main__":
    main()
