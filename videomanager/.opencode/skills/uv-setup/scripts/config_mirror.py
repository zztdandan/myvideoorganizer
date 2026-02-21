#!/usr/bin/env python3
"""
配置国内镜像源脚本

支持的镜像：
- tsinghua: 清华镜像（默认）
- aliyun: 阿里云镜像
- tencent: 腾讯云镜像

使用方法：
    .venv/bin/python .opencode/skills/uv-setup/scripts/config_mirror.py [tsinghua|aliyun|tencent]
"""

import argparse
import sys
from pathlib import Path


MIRRORS = {
    "tsinghua": {
        "name": "清华镜像",
        "url": "https://pypi.tuna.tsinghua.edu.cn/simple"
    },
    "aliyun": {
        "name": "阿里云镜像",
        "url": "https://mirrors.aliyun.com/pypi/simple/"
    },
    "tencent": {
        "name": "腾讯云镜像",
        "url": "https://mirrors.cloud.tencent.com/pypi/simple/"
    }
}


def generate_uv_toml(mirror_name):
    """生成 uv.toml 内容"""
    mirror = MIRRORS.get(mirror_name, MIRRORS["tsinghua"])
    
    return f"""# UV 项目级配置 - 国内镜像源
# 自动生成于 videomanager 项目

# Python 版本偏好
python-preference = "only-system"

# 默认索引 - {mirror['name']}
[[index]]
name = "{mirror_name}"
url = "{mirror['url']}"
default = true
"""


def config_mirror(mirror_name):
    """配置指定镜像源"""
    if mirror_name not in MIRRORS:
        print(f"✗ 不支持的镜像: {mirror_name}")
        print(f"支持的镜像: {', '.join(MIRRORS.keys())}")
        return False
    
    mirror = MIRRORS[mirror_name]
    print(f"→ 正在配置 {mirror['name']}...")
    print(f"  URL: {mirror['url']}")
    
    # 生成配置文件
    config_content = generate_uv_toml(mirror_name)
    config_path = Path("uv.toml")
    
    try:
        # 备份旧配置（如果存在）
        if config_path.exists():
            backup_path = Path("uv.toml.backup")
            backup_path.write_text(config_path.read_text(), encoding="utf-8")
            print(f"  已备份旧配置到: {backup_path}")
        
        # 写入新配置
        config_path.write_text(config_content, encoding="utf-8")
        print(f"  配置文件已保存: {config_path}")
        
        return True
    except Exception as e:
        print(f"✗ 配置文件写入失败: {e}")
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="配置 UV 国内镜像源",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
支持的镜像：
  tsinghua  - 清华镜像（推荐）
  aliyun    - 阿里云镜像
  tencent   - 腾讯云镜像

示例：
  .venv/bin/python .opencode/skills/uv-setup/scripts/config_mirror.py tsinghua
        """
    )
    parser.add_argument(
        "mirror",
        nargs="?",
        default="tsinghua",
        choices=list(MIRRORS.keys()),
        help="选择镜像源（默认: tsinghua）"
    )
    
    args = parser.parse_args()
    
    print("=" * 50)
    print("UV 镜像源配置")
    print("=" * 50)
    
    if config_mirror(args.mirror):
        print()
        print("✓ 镜像源配置成功")
        print()
        print("下次安装依赖时将使用新配置的镜像源")
        print("如需恢复默认 PyPI，删除 uv.toml 文件即可")
        sys.exit(0)
    else:
        print()
        print("✗ 镜像源配置失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
