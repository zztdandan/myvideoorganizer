#!/usr/bin/env python3
"""
video-cleaner: plan_clean_files.py
重构版：智能清理视频文件夹中的文件
"""

import argparse
import json
import os
import re
from pathlib import Path
from datetime import datetime


def parse_args():
    default_video_extensions = (
        ".mp4,.mkv,.avi,.wmv,.mov,.flv,.rmvb,.rm,.3gp,.m4v,.m2ts,.ts,.mpg"
    )
    default_image_extensions = ".jpg,.jpeg,.png,.gif,.bmp,.webp,.tiff"
    default_valid_keywords = "poster,movie,folder,cover,fanart,banner,clearart,thumb,landscape,logo,clearlogo,disc,discart,backdrop,keyart"

    parser = argparse.ArgumentParser(description="清理视频文件夹中的无用文件")
    parser.add_argument("--root", required=True, help="目标根目录")
    parser.add_argument(
        "--video-extensions",
        default=default_video_extensions,
        help=f"视频扩展名，逗号分隔 (默认: {default_video_extensions})",
    )
    parser.add_argument(
        "--image-extensions",
        default=default_image_extensions,
        help=f"图片扩展名，逗号分隔 (默认: {default_image_extensions})",
    )
    parser.add_argument(
        "--valid-keywords",
        default=default_valid_keywords,
        help=f"有效图片关键词，逗号分隔 (默认: {default_valid_keywords})",
    )
    parser.add_argument(
        "--nfo-match-length", type=int, default=5, help="NFO文件名匹配长度 (默认: 5)"
    )
    parser.add_argument(
        "--delete-dir", default=".delete", help="删除目录名 (默认: .delete)"
    )
    parser.add_argument(
        "--min-size", type=float, default=300, help="最小视频大小 MB (默认: 300)"
    )
    parser.add_argument("--output", required=True, help="计划文件输出目录")
    return parser.parse_args()


def parse_comma_list(value: str) -> set:
    return set(item.strip().lower() for item in value.split(",") if item.strip())


def get_file_size_mb(filepath: Path) -> float:
    try:
        return filepath.stat().st_size / (1024 * 1024)
    except OSError:
        return 0


def classify_videos(folder: Path, video_extensions: set, min_size_mb: float) -> tuple:
    """
    分类文件夹中的视频文件
    返回: (大视频文件列表, 小视频文件列表)
    每个元素是 (文件路径, stem, 是否序列化, 序列号或None, 基础名)
    """
    large_videos = []
    small_videos = []
    serial_pattern = re.compile(r'[-_](cd|part|pt|disc|disk)(\d+)$', re.IGNORECASE)

    try:
        for item in folder.iterdir():
            if not item.is_file():
                continue
            if item.suffix.lower() not in video_extensions:
                continue

            size_mb = get_file_size_mb(item)
            stem = item.stem
            match = serial_pattern.search(stem)
            if match:
                base_name = stem[:match.start()]
                serial_num = int(match.group(2))
                is_serial = True
            else:
                base_name = stem
                serial_num = None
                is_serial = False

            if size_mb >= min_size_mb:
                large_videos.append((item, stem, is_serial, serial_num, base_name))
            else:
                small_videos.append((item, stem, is_serial, serial_num, base_name))
    except OSError:
        pass

    return large_videos, small_videos


def get_keyword_from_filename(filename: str, valid_keywords: set) -> str:
    name_lower = filename.lower()
    for keyword in valid_keywords:
        if keyword in name_lower:
            return keyword
    return None


def is_pure_keyword_file(filename: str, valid_keywords: set) -> bool:
    stem = Path(filename).stem.lower()
    return stem in valid_keywords


def has_large_video_prefix(filename: str, large_video_stems: set) -> bool:
    name_lower = filename.lower()
    for stem in large_video_stems:
        stem_lower = stem.lower()
        if name_lower.startswith(stem_lower + '-') or name_lower.startswith(stem_lower + '_'):
            return True
    return False


def has_small_video_prefix(filename: str, small_video_stems: set) -> bool:
    name_lower = filename.lower()
    for stem in small_video_stems:
        stem_lower = stem.lower()
        if name_lower.startswith(stem_lower + '-') or name_lower.startswith(stem_lower + '_'):
            return True
    return False


def is_large_video_nfo(filename: str, large_videos: list) -> bool:
    """
    检查NFO文件是否属于大视频
    支持：
    1. 文件名与大视频完全一致
    2. 文件名与大视频cd1一致
    3. 文件名是基础名，对应序列化视频（A.nfo对应A-cd1.mp4, A-cd2.mp4）
    """
    nfo_stem = Path(filename).stem.lower()

    for _, stem, is_serial, serial_num, base_name in large_videos:
        if nfo_stem == stem.lower():
            return True

    has_cd1 = any(serial_num == 1 for _, _, _, serial_num, _ in large_videos)
    if has_cd1:
        for _, _, is_serial, _, base_name in large_videos:
            if is_serial and nfo_stem == base_name.lower():
                return True

    return False


def is_small_video_nfo(filename: str, small_videos: list) -> bool:
    nfo_stem = Path(filename).stem.lower()
    for _, stem, is_serial, serial_num, base_name in small_videos:
        if nfo_stem == stem.lower():
            return True
    return False


def classify_file(
    filepath: Path,
    video_extensions: set,
    image_extensions: set,
    valid_keywords: set,
    large_videos: list,
    small_videos: list,
) -> str:
    """
    分类单个文件，返回操作类型
    KEEP: 保留
    DELETE: 清理
    """
    ext = filepath.suffix.lower()
    filename = filepath.name

    if ext in video_extensions:
        size_mb = get_file_size_mb(filepath)
        if size_mb >= 300:
            return 'KEEP'
        else:
            return 'DELETE'

    if ext in image_extensions:
        if is_pure_keyword_file(filename, valid_keywords):
            return 'KEEP'

        large_stems = {v[1] for v in large_videos}
        if has_large_video_prefix(filename, large_stems):
            if get_keyword_from_filename(filename, valid_keywords):
                return 'KEEP'

        small_stems = {v[1] for v in small_videos}
        if has_small_video_prefix(filename, small_stems):
            if get_keyword_from_filename(filename, valid_keywords):
                return 'DELETE'

        return 'DELETE'

    if ext == ".nfo":
        if is_large_video_nfo(filename, large_videos):
            return 'KEEP'
        if is_small_video_nfo(filename, small_videos):
            return 'DELETE'
        return 'DELETE'

    return 'DELETE'


def scan_folder_for_files(
    folder: Path,
    root_path: Path,
    video_extensions: set,
    image_extensions: set,
    valid_keywords: set,
    delete_dir: str,
    min_size_mb: float = 300,
) -> list:
    operations = []
    large_videos, small_videos = classify_videos(folder, video_extensions, min_size_mb)

    if not large_videos:
        return operations

    try:
        for item in folder.iterdir():
            if not item.is_file():
                continue

            action = classify_file(
                item,
                video_extensions,
                image_extensions,
                valid_keywords,
                large_videos,
                small_videos,
            )

            if action == 'KEEP':
                continue

            file_size = get_file_size_mb(item)
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
                "created_at": datetime.now().isoformat(),
            }
            operations.append(operation)
    except OSError as e:
        print(f"Error scanning folder {folder}: {e}")

    return operations


def scan_all_folders(
    root_path: Path,
    video_extensions: set,
    image_extensions: set,
    valid_keywords: set,
    delete_dir: str,
    min_size_mb: float = 300,
) -> list:
    all_operations = []

    try:
        for folder in root_path.rglob("*"):
            if not folder.is_dir():
                continue
            if folder.name == delete_dir or delete_dir in folder.parts:
                continue

            operations = scan_folder_for_files(
                folder,
                root_path,
                video_extensions,
                image_extensions,
                valid_keywords,
                delete_dir,
                min_size_mb,
            )
            all_operations.extend(operations)
    except OSError as e:
        print(f"Error walking directory {root_path}: {e}")

    return all_operations


def save_plan(operations: list, output_dir: Path) -> Path:
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
    print(f"Min video size: {args.min_size} MB")

    operations = scan_all_folders(
        root_path,
        video_extensions,
        image_extensions,
        valid_keywords,
        args.delete_dir,
        args.min_size,
    )

    if operations:
        plan_file = save_plan(operations, output_dir)
        total_size = sum(op["size_mb"] for op in operations)
        print(f"\nFound {len(operations)} files to clean ({total_size:.2f} MB)")
        print(f"Plan saved to: {plan_file}")
    else:
        print("\nNo files to clean.")

    print(
        f"\nSUMMARY: {len(operations)} files, {sum(op['size_mb'] for op in operations):.2f} MB"
    )


if __name__ == "__main__":
    main()
