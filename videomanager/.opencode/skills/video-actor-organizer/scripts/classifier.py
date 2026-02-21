#!/usr/bin/env python3
"""
video-actor-organizer: classifier.py
演员名分类器 - 支持中文映射记忆系统
"""

import re
from pathlib import Path
from pypinyin import lazy_pinyin


class ActorClassifier:
    def __init__(self, memory_path: Path | None = None):
        self.memory_path = memory_path or Path("memory/actor_mappings.toml")
        self.mappings = self._load_mappings()

    def _load_mappings(self) -> dict:
        """加载演员名映射表"""
        mappings = {}
        if self.memory_path.exists():
            try:
                import tomllib

                content = self.memory_path.read_text(encoding="utf-8")
                data = tomllib.loads(content)
                mappings = data.get("actor_mappings", {})
            except Exception:
                pass
        return mappings

    def has_kana(self, text: str) -> bool:
        """检查文本是否包含日文假名（平假名或片假名）"""
        # 平假名范围: \u3040-\u309F
        # 片假名范围: \u30A0-\u30FF
        kana_pattern = re.compile(r"[\u3040-\u309F\u30A0-\u30FF]")
        return bool(kana_pattern.search(text))

    def get_mapping(self, name: str) -> tuple[str, str | None]:
        """
        获取演员名的映射信息
        返回: (display_name, chinese_name)
        - display_name: 用于目录显示的名字 (中文名_原名 或 原名)
        - chinese_name: 中文映射名（如果有），否则 None
        """
        if not self.has_kana(name):
            return name, None

        chinese_name = self.mappings.get(name)
        if chinese_name:
            display_name = f"{chinese_name}_{name}"
            return display_name, chinese_name
        else:
            return name, None

    def needs_mapping(self, name: str) -> bool:
        """检查名字是否需要映射（包含假名且无映射）"""
        if not self.has_kana(name):
            return False
        return name not in self.mappings

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

    def is_cjk_char(self, char: str) -> bool:
        return bool(re.compile(r"[\u4E00-\u9FFF]").match(char))

    def get_chinese_char_initial(self, name: str) -> str:
        """获取中文名的首汉字（用于 initial 层）"""
        if not name:
            return ""
        for char in name:
            if self.is_cjk_char(char):
                return char
        return ""

    def is_latin_char(self, char: str) -> bool:
        return bool(re.compile(r"[A-Za-z]").match(char))

    def get_english_initial(self, name: str) -> str:
        first_char = name[0].upper()
        if first_char.isalpha():
            return first_char
        return "#"

    def classify(
        self, name: str, unknown_category: str = "99", japanese_category: str = "0"
    ) -> dict:
        """
        对演员名进行分类
        返回分类信息，包括是否需要映射
        """
        if not name or not name.strip():
            return {
                "category": unknown_category,
                "initial": "",
                "actor_name": "",
                "type": "unknown",
                "needs_mapping": False,
                "display_name": "",
                "chinese_name": None,
            }

        name = name.strip()

        if name == "未知演员":
            return {
                "category": unknown_category,
                "initial": "",
                "actor_name": name,
                "type": "unknown",
                "needs_mapping": False,
                "display_name": name,
                "chinese_name": None,
            }

        display_name, chinese_name = self.get_mapping(name)
        needs_mapping_flag = self.needs_mapping(name)

        if chinese_name:
            initial = self.get_chinese_initial(chinese_name)
            chinese_char = self.get_chinese_char_initial(chinese_name)
            if initial != "#" and initial.isalpha():
                return {
                    "category": initial.upper(),
                    "initial": chinese_char,
                    "actor_name": name,
                    "type": "chinese_mapped",
                    "needs_mapping": False,
                    "display_name": display_name,
                    "chinese_name": chinese_name,
                }

        first_char = name[0]

        if self.is_cjk_char(first_char):
            initial = self.get_chinese_initial(name)
            chinese_char = self.get_chinese_char_initial(name)
            if initial != "#" and initial.isalpha():
                return {
                    "category": initial.upper(),
                    "initial": chinese_char,
                    "actor_name": name,
                    "type": "chinese",
                    "needs_mapping": needs_mapping_flag,
                    "display_name": display_name,
                    "chinese_name": chinese_name,
                }
        elif self.is_latin_char(first_char):
            initial = self.get_english_initial(name)
            return {
                "category": initial.upper(),
                "initial": initial.lower(),
                "actor_name": name,
                "type": "english",
                "needs_mapping": False,
                "display_name": display_name,
                "chinese_name": chinese_name,
            }

        return {
            "category": japanese_category,
            "initial": "",
            "actor_name": name,
            "type": "japanese",
            "needs_mapping": needs_mapping_flag,
            "display_name": display_name,
            "chinese_name": chinese_name,
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
