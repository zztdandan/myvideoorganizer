"""
演员名字分类器
"""
from typing import Optional
import re
from pypinyin import pinyin, Style
import pykakasi

class ActorClassifier:
    """演员名字分类器"""
    
    def __init__(self):
        """初始化分类器"""
        self.kks = pykakasi.kakasi()
        
    def _has_kana(self, text: str) -> bool:
        """
        判断文本是否包含假名（平假名或片假名）
        
        Args:
            text: 要判断的文本
            
        Returns:
            是否包含假名
        """
        # 日文假名范围
        kana_ranges = [
            (0x3040, 0x309F),  # Hiragana
            (0x30A0, 0x30FF),  # Katakana
        ]
        
        for char in text:
            code = ord(char)
            for start, end in kana_ranges:
                if start <= code <= end:
                    return True
        return False
        
    def _is_chinese(self, text: str) -> bool:
        """
        判断文本是否为中文
        
        Args:
            text: 要判断的文本
            
        Returns:
            是否为中文
        """
        if not text:
            return False
            
        # 只判断第一个字符
        first_char = text[0]
        py_result = pinyin(first_char, style=Style.NORMAL)
        
        # 如果能获取到拼音结果，且是标准拼音（纯小写字母）
        if py_result and py_result[0] and py_result[0][0].isalpha() and py_result[0][0].islower():
            return True
            
        return False
        
    def _is_japanese(self, text: str) -> bool:
        """
        判断文本是否为日文
        
        Args:
            text: 要判断的文本
            
        Returns:
            是否为日文
        """
        # 如果包含假名，则一定是日文
        if self._has_kana(text):
            return True
            
        # 如果不包含假名，尝试用 kakasi 转换
        # 如果能转换出假名，说明是日文汉字
        result = self.kks.convert(text)
        if result:
            # 检查是否有假名输出
            for item in result:
                if item['hira'] or item['kana']:
                    return True
                    
        return False
        
    def _get_first_letter_pinyin(self, text: str) -> str:
        """
        获取中文文本第一个字的拼音首字母
        
        Args:
            text: 中文文本
            
        Returns:
            拼音首字母（大写）
        """
        if not text:
            return ''
            
        # 获取第一个字的拼音
        py = pinyin(text[0], style=Style.NORMAL)
        if py and py[0]:
            return py[0][0][0].upper()
            
        return ''
        
    def _get_first_letter_romaji(self, text: str) -> str:
        """
        获取日文文本第一个字的罗马字首字母
        
        Args:
            text: 日文文本
            
        Returns:
            罗马字首字母（大写）
        """
        if not text:
            return ''
            
        # 转换为罗马字
        result = self.kks.convert(text)
        if result and result[0]['hepburn']:
            return result[0]['hepburn'][0].upper()
            
        return ''
        
    def get_category(self, actor_name: Optional[str], config) -> str:
        """
        获取演员名字的分类
        
        Args:
            actor_name: 演员名字
            config: 配置对象
            
        Returns:
            分类名（0-9/A-Z/99）
        """
        if not actor_name:
            return config.UNKNOWN_ACTOR_CATEGORY
            
        # 移除括号内的内容和特殊字符
        cleaned_name = re.sub(r'\([^)]*\)', '', actor_name)
        cleaned_name = re.sub(r'[^\w\s\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]', '', cleaned_name)
        cleaned_name = cleaned_name.strip()
        
        if not cleaned_name:
            return config.UNKNOWN_ACTOR_CATEGORY
            
        # 如果第一个字符是英文字母
        if cleaned_name[0].isascii() and cleaned_name[0].isalpha():
            return cleaned_name[0].upper()
            
        # 优先判断是否为中文
        if self._is_chinese(cleaned_name):
            pinyin_letter = self._get_first_letter_pinyin(cleaned_name)
            if pinyin_letter and pinyin_letter.isascii():
                return pinyin_letter
                
        # 如果不是中文，判断是否为日文
        if self._is_japanese(cleaned_name):
            # 获取罗马字首字母
            romaji = self._get_first_letter_romaji(cleaned_name)
            if romaji:
                return romaji if not romaji.isascii() else config.JAPANESE_ACTOR_CATEGORY
            return config.JAPANESE_ACTOR_CATEGORY
            
        return config.UNKNOWN_ACTOR_CATEGORY 