#!/usr/bin/env python3
"""
movie-organizer: helpers.py
电影整理辅助函数
"""

import re
from pathlib import Path


def extract_technical_info(filename: str) -> str:
    """从文件名提取技术信息（1080p, BluRay, x264等）"""
    patterns = [
        r"(1080p|720p|480p|2160p|4K|8K)",
        r"(BluRay|BDRip|BRRip|WEB-DL|WEBRip|HDRip|DVDRip|HDTV)",
        r"(x264|x265|HEVC|H\.264|H\.265|AVC|VC-1)",
        r"(AAC|AC3|DTS|TrueHD|FLAC|MP3)",
        r"(REPACK|PROPER|EXTENDED|UNRATED|DC| Directors Cut)",
    ]
    
    info_parts = []
    filename_upper = filename.upper()
    
    for pattern in patterns:
        matches = re.findall(pattern, filename, re.IGNORECASE)
        info_parts.extend(matches)
    
    # 去重并保持原有顺序
    seen = set()
    unique_parts = []
    for part in info_parts:
        part_upper = part.upper()
        if part_upper not in seen:
            seen.add(part_upper)
            unique_parts.append(part)
    
    return ".".join(unique_parts) if unique_parts else ""


def build_movie_filename(english_name: str, year: int, technical_info: str, extension: str) -> str:
    """构建标准电影文件名"""
    parts = [english_name, str(year)]
    
    if technical_info:
        parts.append(technical_info)
    
    return ".".join(parts) + extension


def is_subtitle_file(filename: str) -> bool:
    """判断是否为字幕文件"""
    subtitle_extensions = {".srt", ".ass", ".ssa", ".sub", ".idx", ".vtt"}
    return Path(filename).suffix.lower() in subtitle_extensions


def extract_subtitle_language(filename: str) -> str:
    """从字幕文件名提取语言标识"""
    patterns = [
        r"\.([a-zA-Z]{2,3})\.srt$",      # .chs.srt, .eng.srt
        r"\.([a-zA-Z]+)\.srt$",          # .chinese.srt, .english.srt
        r"_([a-zA-Z]{2,3})\.srt$",        # _chs.srt
    ]
    
    for pattern in patterns:
        match = re.search(pattern, filename, re.IGNORECASE)
        if match:
            lang = match.group(1).lower()
            # 标准化语言代码
            lang_map = {
                "chs": "chs", "cht": "cht", "chi": "chs",
                "eng": "eng", "en": "eng",
                "jpn": "jpn", "jp": "jpn",
                "kor": "kor", "kr": "kor",
            }
            return lang_map.get(lang, lang)
    
    return ""


def is_image_file(filename: str) -> bool:
    """判断是否为图片文件"""
    image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff"}
    return Path(filename).suffix.lower() in image_extensions


def is_video_file(filename: str) -> bool:
    """判断是否为视频文件"""
    video_extensions = {".mp4", ".mkv", ".avi", ".wmv", ".mov", ".flv", ".m4v", ".m2ts", ".ts", ".mpg", ".rmvb", ".rm", ".3gp"}
    return Path(filename).suffix.lower() in video_extensions
