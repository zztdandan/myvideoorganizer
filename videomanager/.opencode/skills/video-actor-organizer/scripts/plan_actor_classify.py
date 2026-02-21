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
    parser = argparse.ArgumentParser(
        description="扫描并生成演员分类计划（同时处理VR和普通视频）"
    )
    parser.add_argument("--root", required=True, help="目标根目录")
    parser.add_argument("--unknown-category", default="99", help="未知演员分类")
    parser.add_argument("--japanese-category", default="0", help="日文名演员分类")
    parser.add_argument("--title-max-length", type=int, default=10, help="标题最大长度")
    parser.add_argument("--output", required=True, help="计划文件输出目录")
    parser.add_argument(
        "--width-threshold", type=int, default=2000, help="VR视频宽度阈值（像素）"
    )
    parser.add_argument("--big-dir", default="BIG", help="VR视频存放目录名")
    return parser.parse_args()


def parse_nfo(nfo_path: Path) -> dict:
    """解析 NFO 文件，提取演员、标题和视频分辨率"""
    result = {"actors": [], "title": "", "is_fc2": False, "width": 0, "height": 0}

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

        width_match = re.search(r"<width>(\d+)</width>", content, re.IGNORECASE)
        height_match = re.search(r"<height>(\d+)</height>", content, re.IGNORECASE)

        if width_match:
            result["width"] = int(width_match.group(1))
        if height_match:
            result["height"] = int(height_match.group(1))

        if result["width"] == 0:
            fileinfo_match = re.search(
                r"<fileinfo>.*?</fileinfo>", content, re.DOTALL | re.IGNORECASE
            )
            if fileinfo_match:
                fileinfo = fileinfo_match.group(0)
                width_match = re.search(
                    r"<width>(\d+)</width>", fileinfo, re.IGNORECASE
                )
                height_match = re.search(
                    r"<height>(\d+)</height>", fileinfo, re.IGNORECASE
                )
                if width_match:
                    result["width"] = int(width_match.group(1))
                if height_match:
                    result["height"] = int(height_match.group(1))

    except Exception:
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
        r"(\d{6,7}-\d{2,3})",  # 123456-789
        r"(FC2-\d+)",  # FC2-123456
        r"(FC2PPV-\d+)",  # FC2PPV-123456
    ]

    for pattern in patterns:
        match = re.search(pattern, folder_name.upper())
        if match:
            return match.group(1)

    return folder_name[:20]  # 返回前20字符作为标识


def is_classified_folder(folder_name: str, big_dir: str = "BIG") -> bool:
    if len(folder_name) == 1 and folder_name.isalpha():
        return True
    if folder_name.isdigit():
        return True
    if folder_name.startswith("."):
        return True
    if folder_name == big_dir:
        return True
    return False


def is_vr_video(width: int, height: int, threshold: int = 2000) -> bool:
    if width <= 0 or height <= 0:
        return False
    if width <= threshold:
        return False
    aspect_ratio = width / height
    is_16_9 = abs(aspect_ratio - 16 / 9) < 0.05
    return not is_16_9


def scan_folders(
    root_path: Path,
    unknown_category: str,
    japanese_category: str,
    title_max_length: int,
    width_threshold: int,
    big_dir: str,
) -> tuple[list, list]:
    """
    扫描目录，生成演员分类计划（同时处理VR和普通视频）
    返回: (operations, unmapped_actors)
    - operations: 移动计划列表
    - unmapped_actors: 需要映射但未映射的演员名列表
    """
    operations = []
    unmapped_actors = []
    classifier = ActorClassifier()

    try:
        for folder in root_path.iterdir():
            if not folder.is_dir():
                continue

            if is_classified_folder(folder.name, big_dir):
                continue

            nfo_path = find_first_nfo(folder)

            actors = []
            title = ""
            is_fc2 = False
            width = 0
            height = 0

            if nfo_path:
                nfo_data = parse_nfo(nfo_path)
                actors = nfo_data["actors"]
                title = nfo_data["title"]
                is_fc2 = nfo_data["is_fc2"]
                width = nfo_data["width"]
                height = nfo_data["height"]

            if not actors and is_fc2:
                folder_name = folder.name.upper()
                if "FC2-PPV" in folder_name or "FC2PPV" in folder_name:
                    actors = ["FC2-PPV"]
                elif "FC2" in folder_name:
                    actors = ["FC2"]
                elif "PPV" in folder_name:
                    actors = ["PPV"]

            if not actors:
                actors = ["未知演员"]

            primary_actor = actors[0]
            classification = classifier.classify(
                primary_actor, unknown_category, japanese_category
            )

            # 检查是否需要映射但未映射
            if classification.get("needs_mapping"):
                if primary_actor not in unmapped_actors:
                    unmapped_actors.append(primary_actor)
                continue  # 跳过此文件夹，不生成计划

            if not title:
                title = extract_code_from_folder(folder.name)

            if len(title) > title_max_length:
                title = title[:title_max_length]

            category = classification["category"]
            initial = classification["initial"]
            # 使用 display_name 作为目录名（格式: 中文名_原名 或 原名）
            display_name = classification.get(
                "display_name", classification["actor_name"]
            )

            is_vr = is_vr_video(width, height, width_threshold)

            if is_vr:
                if (
                    classification["type"] in ("chinese", "chinese_mapped")
                    and initial
                    and classification["actor_name"] != "未知演员"
                ):
                    dest_folder = (
                        root_path / big_dir / category / initial / display_name / title
                    )
                else:
                    dest_folder = root_path / big_dir / category / display_name / title
            else:
                if (
                    classification["type"] in ("chinese", "chinese_mapped")
                    and initial
                    and classification["actor_name"] != "未知演员"
                ):
                    dest_folder = root_path / category / initial / display_name / title
                else:
                    dest_folder = root_path / category / display_name / title

            folder_size = get_folder_size(folder)

            operation = {
                "func": "actor_classify",
                "action": "MOVE",
                "source": str(folder),
                "destination": str(dest_folder),
                "size_mb": folder_size,
                "actor": display_name,
                "original_actor": classification["actor_name"],
                "category": category,
                "title": title,
                "is_vr": is_vr,
                "width": width,
                "height": height,
                "created_at": datetime.now().isoformat(),
            }
            operations.append(operation)

    except OSError as e:
        print(f"Error scanning directory: {e}")

    return operations, unmapped_actors


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
    print(f"VR width threshold: {args.width_threshold}")
    print(f"VR directory: {args.big_dir}")

    operations, unmapped_actors = scan_folders(
        root_path,
        args.unknown_category,
        args.japanese_category,
        args.title_max_length,
        args.width_threshold,
        args.big_dir,
    )

    if operations:
        plan_file = save_plan(operations, output_dir)
        total_size = sum(op["size_mb"] for op in operations)
        vr_count = sum(1 for op in operations if op.get("is_vr", False))

        categories = {}
        for op in operations:
            cat = op["category"]
            categories[cat] = categories.get(cat, 0) + 1

        print(f"\nFound {len(operations)} folders to classify ({total_size:.2f} MB)")
        print(f"VR videos: {vr_count}, Normal videos: {len(operations) - vr_count}")
        print(f"Categories: {categories}")
        print(f"Plan saved to: {plan_file}")
    else:
        print("\nNo folders found.")

    # 输出未映射的演员列表（用于 Agent 处理）
    if unmapped_actors:
        print(f"\n{'=' * 60}")
        print("UNMAPPED_ACTORS_START")
        for actor in unmapped_actors:
            print(f"  - {actor}")
        print("UNMAPPED_ACTORS_END")
        print(f"{'=' * 60}")

    print(
        f"\nSUMMARY: {len(operations)} folders, {sum(op['size_mb'] for op in operations):.2f} MB"
    )
    if unmapped_actors:
        print(f"UNMAPPED: {len(unmapped_actors)} actors need mapping")


if __name__ == "__main__":
    main()
