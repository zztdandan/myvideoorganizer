#!/usr/bin/env python3
"""
UV 可用性检查脚本
检查 uv 命令是否在 PATH 中可用

返回值：
- 0: uv 可用
- 1: uv 不可用
"""

import subprocess
import sys
import os


def check_uv_available():
    """检查 uv 是否可用"""
    try:
        result = subprocess.run(
            ["uv", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        version = result.stdout.strip()
        print(f"✓ uv 可用: {version}")
        return True, version
    except FileNotFoundError:
        print("✗ 错误: uv 命令未找到")
        print()
        print("可能原因：")
        print("  1. uv 未安装")
        print("  2. ~/.local/bin 不在 PATH 中")
        print()
        print("解决方案：")
        print("  1. 安装 uv: curl -LsSf https://astral.sh/uv/install.sh | sh")
        print("  2. 添加 PATH: export PATH=\"$HOME/.local/bin:$PATH\"")
        print("  3. 永久生效: echo 'export PATH=\"$HOME/.local/bin:$PATH\"' >> ~/.bashrc")
        return False, None
    except subprocess.CalledProcessError as e:
        print(f"✗ uv 检查失败: {e}")
        return False, None


def main():
    """主函数"""
    print("=" * 50)
    print("UV 可用性检查")
    print("=" * 50)
    
    available, version = check_uv_available()
    
    if available:
        print()
        print("✓ 检查通过，可以继续")
        sys.exit(0)
    else:
        print()
        print("✗ 检查失败，无法继续")
        print()
        print("重要提示：")
        print("  uv 是 videomanager 项目的必需工具")
        print("  请按照上述解决方案配置环境后，重新启动 opencode")
        sys.exit(1)


if __name__ == "__main__":
    main()
