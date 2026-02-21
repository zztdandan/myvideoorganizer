#!/usr/bin/env python3
"""
video-renamer: plan_rename.py
扫描含多个视频的文件夹，按规则重命名
"""

import argparse
import json
from pathlib import Path
from datetime import datetime
import re


def parse_args():
    parser = argparse.ArgumentParser(description="扫描并生成重命名计划")
    parser.add_argument("--root", required=True, help="目标根目录")
    parser.add_argument(
        "--pattern", default="number2", help="序号模式: number|letter|number2"
    )
    parser.add_argument("--output", required=True, help="计划文件输出目录")
    parser.add_argument("--min-size", type=int, default=300, help="最小视频大小(MB)")
    parser.add_argument(
        "--extensions",
        default=".mp4,.mkv,.avi,.wmv,.mov,.flv,.rmvb,.rm,.3gp,.m4v,.m2ts,.ts,.mpg",
        help="视频扩展名列表",
    )
    return parser.parse_args()


def find_common_prefix(names: list) -> str:
    """找出文件名列表的公共前缀"""
    if not names:
        return ""

    prefix = names[0]
    for name in names[1:]:
        i = 0
        while i < len(prefix) and i < len(name) and prefix[i] == name[i]:
            i += 1
        prefix = prefix[:i]
        if not prefix:
            break

    # 清理后缀（如 -A, _1, 等）
    prefix = re.sub(r"[-_][a-zA-Z0-9]+$", "", prefix)
    prefix = re.sub(r"[._\-]+$", "", prefix)

    return prefix


def generate_suffix(index: int, pattern: str) -> str:
    """根据模式生成序号后缀"""
    if pattern == "number":
        return f"-cd{index}"
    elif pattern == "letter":
        return f"-cd{chr(64 + index)}"  # 1->A, 2->B
    elif pattern == "number2":
        return f"-cd{index:02d}"
    else:
        return f"-cd{index:02d}"


def scan_folders(
    root_path: Path, pattern: str, min_size_mb: int, extensions: set
) -> list:
    """扫描目录，找出需要重命名的文件夹（只处理包含多个大视频的文件夹）"""
    operations = []
    min_size_bytes = min_size_mb * 1024 * 1024

    try:
        for folder in root_path.iterdir():
            if not folder.is_dir():
                continue

            # 获取所有大视频文件（>= min_size_mb）
            big_video_files = []
            try:
                for item in folder.iterdir():
                    if item.is_file() and item.suffix.lower() in extensions:
                        # 检查文件大小
                        try:
                            file_size = item.stat().st_size
                            if file_size >= min_size_bytes:
                                big_video_files.append(item)
                        except OSError:
                            continue
            except OSError:
                continue

            # 如果只有一个大视频文件，跳过（不需要重命名）
            if len(big_video_files) <= 1:
                continue

            # 如果文件名已包含 -cd，跳过
            if all("-cd" in f.stem for f in big_video_files):
                continue

            # 找出公共前缀
            names = [f.stem for f in big_video_files]
            common_prefix = find_common_prefix(names)

            if not common_prefix:
                common_prefix = folder.name

            # 按文件名排序
            big_video_files.sort(key=lambda f: f.name)

            # 生成重命名操作
            for i, video_file in enumerate(big_video_files, 1):
                new_name = (
                    f"{common_prefix}{generate_suffix(i, pattern)}{video_file.suffix}"
                )

                operation = {
                    "func": "rename",
                    "action": "RENAME",
                    "source": str(video_file),
                    "destination": str(video_file.parent / new_name),
                    "size_mb": round(video_file.stat().st_size / (1024 * 1024), 2)
                    if video_file.exists()
                    else 0,
                    "created_at": datetime.now().isoformat(),
                }
                operations.append(operation)

    except OSError as e:
        print(f"Error scanning directory: {e}")

    return operations


def save_plan(operations: list, output_dir: Path) -> Path:
    """保存计划到 JSON 文件"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    plan_file = output_dir / f"rename_{timestamp}.json"

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
    extensions = set(args.extensions.split(","))

    print(f"Scanning: {root_path}")
    print(f"Pattern: {args.pattern}")
    print(f"Min size: {args.min_size} MB")

    operations = scan_folders(root_path, args.pattern, args.min_size, extensions)

    if operations:
        plan_file = save_plan(operations, output_dir)
        total_size = sum(op["size_mb"] for op in operations)
        print(f"\nFound {len(operations)} files to rename ({total_size:.2f} MB)")
        print(f"Plan saved to: {plan_file}")
    else:
        print("\nNo files need renaming.")

    print(
        f"\nSUMMARY: {len(operations)} files, {sum(op['size_mb'] for op in operations):.2f} MB"
    )


if __name__ == "__main__":
    main()
