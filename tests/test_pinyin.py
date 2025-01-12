"""
测试 pypinyin 包的行为
"""
from pypinyin import pinyin, Style

def test_pinyin_basic():
    """测试基本的拼音转换"""
    print("\n=== 基本拼音转换测试 ===")
    
    # 测试纯中文
    text = "张三"
    result = pinyin(text, style=Style.NORMAL)
    print(f"输入：{text}")
    print(f"输出：{result}")  # 期望: [['zhang'], ['san']]
    
    # 测试中文带空格
    text = "张 三"
    result = pinyin(text, style=Style.NORMAL)
    print(f"\n输入：{text}")
    print(f"输出：{result}")  # 期望: [['zhang'], ['san']]
    
    # 测试中文带英文
    text = "张Tom"
    result = pinyin(text, style=Style.NORMAL)
    print(f"\n输入：{text}")
    print(f"输出：{result}")  # 期望: [['zhang'], ['Tom']]
    
def test_pinyin_japanese():
    """测试带日文字符的转换"""
    print("\n=== 日文混合测试 ===")
    
    # 测试日文假名
    text = "橘メアリー"
    result = pinyin(text, style=Style.NORMAL)
    print(f"输入：{text}")
    print(f"输出：{result}")
    
    # 测试日文汉字
    text = "山田太郎"
    result = pinyin(text, style=Style.NORMAL)
    print(f"\n输入：{text}")
    print(f"输出：{result}")
    
def test_pinyin_styles():
    """测试不同的拼音风格"""
    print("\n=== 拼音风格测试 ===")
    
    text = "张三"
    # 普通风格
    result = pinyin(text, style=Style.NORMAL)
    print(f"NORMAL: {result}")  # 期望: [['zhang'], ['san']]
    
    # 声调风格
    result = pinyin(text, style=Style.TONE)
    print(f"TONE: {result}")  # 期望: [['zhāng'], ['sān']]
    
    # 首字母风格
    result = pinyin(text, style=Style.FIRST_LETTER)
    print(f"FIRST_LETTER: {result}")  # 期望: [['z'], ['s']]
    
def test_pinyin_edge_cases():
    """测试边缘情况"""
    print("\n=== 边缘情况测试 ===")
    
    # 测试空字符串
    text = ""
    result = pinyin(text, style=Style.NORMAL)
    print(f"空字符串：{result}")
    
    # 测试特殊字符
    text = "张#三"
    result = pinyin(text, style=Style.NORMAL)
    print(f"\n特殊字符：{result}")
    
    # 测试数字
    text = "张3三"
    result = pinyin(text, style=Style.NORMAL)
    print(f"\n数字：{result}")
    
def test_pinyin_first_char():
    """测试只获取第一个字符的拼音"""
    print("\n=== 首字符拼音测试 ===")
    
    # 测试日文混合（汉字开头）
    text = "橘メアリー"
    result = pinyin(text[0], style=Style.NORMAL)
    print(f"输入首字符：{text[0]}")
    print(f"输出：{result}")  # 期望: [['ju']]
    
    # 测试日文混合（假名开头）
    text = "メアリー橘"
    result = pinyin(text[0], style=Style.NORMAL)
    print(f"\n输入首字符：{text[0]}")
    print(f"输出：{result}")  # 期望: [['メ']]
    
    # 测试中文
    text = "张三"
    result = pinyin(text[0], style=Style.NORMAL)
    print(f"\n输入首字符：{text[0]}")
    print(f"输出：{result}")  # 期望: [['zhang']]

if __name__ == "__main__":
    test_pinyin_basic()
    test_pinyin_japanese()
    test_pinyin_styles()
    test_pinyin_edge_cases()
    test_pinyin_first_char() 