#!/usr/bin/env python3
"""
video-big-detector: classifier.py
演员名分类器（从 video-actor-organizer 复制，自包含）
"""

import re
from pypinyin import lazy_pinyin
from pykakasi import kakasi


class ActorClassifier:
    """演员名分类器"""
    
    def __init__(self):
        self.kakasi = kakasi()
        self.kakasi.setMode("J", "H")
        self.conv = self.kakasi.getConverter()
    
    def is_japanese(self, name: str) -> bool:
        hiragana_pattern = re.compile(r'[\u3040-\u309F]')
        katakana_pattern = re.compile(r'[\u30A0-\u30FF]')
        
        if hiragana_pattern.search(name) or katakana_pattern.search(name):
            return True
        
        return False
    
    def get_chinese_initial(self, name: str) -> str:
        if not name:
            return "#"
        
        try:
            pinyin_list = lazy_pinyin(name)
            if pinyin_list:
                first_char = pinyin_list[0][0].upper()
                if first_char.isalpha():
                    return first_char
        except Exception:
            pass
        
        return "#"
    
    def classify(self, name: str, unknown_category: str = "99", japanese_category: str = "0") -> dict:
        if not name or not name.strip():
            return {
                "category": unknown_category,
                "initial": "",
                "actor_name": "",
                "type": "unknown"
            }
        
        name = name.strip()
        
        if self.is_japanese(name):
            return {
                "category": japanese_category,
                "initial": "",
                "actor_name": name,
                "type": "japanese"
            }
        
        initial = self.get_chinese_initial(name)
        
        if initial == "#" or not initial.isalpha():
            return {
                "category": unknown_category,
                "initial": "",
                "actor_name": name,
                "type": "unknown"
            }
        
        return {
            "category": initial.upper(),
            "initial": initial.lower(),
            "actor_name": name,
            "type": "chinese"
        }
