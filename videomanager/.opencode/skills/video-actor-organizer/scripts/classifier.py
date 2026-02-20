#!/usr/bin/env python3
"""
video-actor-organizer: classifier.py
演员名分类器
"""

import re
from pypinyin import lazy_pinyin
from pykakasi import kakasi


class ActorClassifier:
    """演员名分类器"""
    
    def __init__(self):
        self.kakasi = kakasi()
        self.kakasi.setMode("J", "H")  # Japanese to Hiragana
        self.conv = self.kakasi.getConverter()
    
    def is_japanese(self, name: str) -> bool:
        """判断是否为日文名"""
        # 检查是否包含日文假名
        hiragana_pattern = re.compile(r'[\u3040-\u309F]')
        katakana_pattern = re.compile(r'[\u30A0-\u30FF]')
        kanji_pattern = re.compile(r'[\u4E00-\u9FAF]')
        
        if hiragana_pattern.search(name) or katakana_pattern.search(name):
            return True
        
        # 如果全是汉字但不在常用中文姓氏中，可能是日文
        if kanji_pattern.search(name) and not self.is_common_chinese_surname(name):
            return True
        
        return False
    
    def is_common_chinese_surname(self, name: str) -> bool:
        """检查是否为常见中文姓氏开头"""
        common_surnames = {
            "李", "王", "张", "刘", "陈", "杨", "赵", "黄", "周", "吴",
            "徐", "孙", "胡", "朱", "高", "林", "何", "郭", "马", "罗",
            "梁", "宋", "郑", "谢", "韩", "唐", "冯", "于", "董", "萧",
            "程", "曹", "袁", "邓", "许", "傅", "沈", "曾", "彭", "吕",
            "苏", "卢", "蒋", "蔡", "贾", "丁", "魏", "薛", "叶", "阎"
        }
        if name:
            for surname in common_surnames:
                if name.startswith(surname):
                    return True
        return False
    
    def get_chinese_initial(self, name: str) -> str:
        """获取中文名的拼音首字母"""
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
    
    def get_japanese_romaji(self, name: str) -> str:
        """获取日文名的罗马音首字母"""
        if not name:
            return "#"
        
        try:
            # 转换为平假名
            hiragana = self.conv.do(name)
            # 再转换为罗马音
            self.kakasi.setMode("H", "a")
            self.kakasi.setMode("K", "a")
            conv_romaji = self.kakasi.getConverter()
            romaji = conv_romaji.do(hiragana)
            
            if romaji:
                first_char = romaji[0].upper()
                if first_char.isalpha():
                    return first_char
        except Exception:
            pass
        
        return "#"
    
    def classify(self, name: str, unknown_category: str = "99", japanese_category: str = "0") -> dict:
        """
        分类演员名
        
        Returns:
            dict: {
                "category": str,      # 分类字母 (A-Z) 或特殊分类
                "initial": str,       # 首字母
                "actor_name": str,    # 处理后的演员名
                "type": str           # "chinese", "japanese", "unknown"
            }
        """
        if not name or not name.strip():
            return {
                "category": unknown_category,
                "initial": "",
                "actor_name": "",
                "type": "unknown"
            }
        
        name = name.strip()
        
        # 检查是否为日文名
        if self.is_japanese(name):
            return {
                "category": japanese_category,
                "initial": "",
                "actor_name": name,
                "type": "japanese"
            }
        
        # 中文名或其他
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


def main():
    """测试函数"""
    classifier = ActorClassifier()
    
    test_names = [
        "杨幂",
        "Tom Cruise",
        "蒼井そら",
        "",
        "123",
    ]
    
    for name in test_names:
        result = classifier.classify(name)
        print(f"{name} -> {result}")


if __name__ == "__main__":
    main()
