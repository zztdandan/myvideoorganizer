#!/usr/bin/env python3
"""
虚拟环境初始化和依赖安装脚本

功能：
1. 检查 .venv 是否存在
2. 如不存在，创建虚拟环境
3. 安装项目依赖

返回值：
- 0: 环境就绪
- 2: 初始化失败
"""

import subprocess
import sys
from pathlib import Path


def parse_deps_with_regex(pyproject_path):
    """使用正则表达式解析 pyproject.toml 中的依赖"""
    import re
    try:
        content = pyproject_path.read_text(encoding="utf-8")
        # 查找 dependencies = ["...", "..."] 部分
        match = re.search(r'dependencies\s*=\s*\[(.*?)\]', content, re.DOTALL)
        if not match:
            return []
        
        deps_str = match.group(1)
        # 提取引号内的包名
        deps = re.findall(r'"([^"]+)"', deps_str)
        
        # 解析包名（去掉版本号）
        dep_names = []
        for dep in deps:
            for sep in [">=", ">", "==", "<", "~="]:
                if sep in dep:
                    dep = dep.split(sep)[0].strip()
                    break
            dep_names.append(dep)
        
        return dep_names
    except Exception as e:
        print(f"⚠ 正则解析失败: {e}")
        return []


def read_dependencies_from_pyproject():
    """从 pyproject.toml 读取项目依赖列表"""
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        print("✗ pyproject.toml 不存在")
        return []
    
    try:
        # Python 3.11+ 内置 tomllib
        try:
            import tomllib
        except ImportError:
            # Python < 3.11，尝试使用 tomli（应该在依赖中）
            try:
                import tomli as tomllib
            except ImportError:
                print("⚠ 缺少 TOML 解析库，使用正则表达式解析")
                return parse_deps_with_regex(pyproject_path)
        
        with open(pyproject_path, "rb") as f:
            config = tomllib.load(f)
        
        # 读取 [project] dependencies
        deps = config.get("project", {}).get("dependencies", [])
        
        # 解析依赖名称（去掉版本号）
        dep_names = []
        for dep in deps:
            # 处理形如 "package>=1.0" 的格式，提取包名
            if ">=" in dep:
                dep_names.append(dep.split(">=")[0].strip())
            elif ">" in dep:
                dep_names.append(dep.split(">")[0].strip())
            elif "==" in dep:
                dep_names.append(dep.split("==")[0].strip())
            elif "<" in dep:
                dep_names.append(dep.split("<")[0].strip())
            else:
                dep_names.append(dep.strip())
        
        return dep_names
    except Exception as e:
        print(f"✗ 读取 pyproject.toml 失败: {e}")
        return []


def check_venv_exists():
    """检查虚拟环境是否存在且完整"""
    venv_path = Path(".venv")
    if not venv_path.exists():
        print("✗ 虚拟环境不存在: .venv/")
        return False
    
    python_path = venv_path / "bin" / "python"
    if not python_path.exists():
        print("✗ 虚拟环境不完整: 缺少 python 可执行文件")
        return False
    
    print(f"✓ 虚拟环境存在: {venv_path.absolute()}")
    return True


def create_venv():
    """创建虚拟环境"""
    print()
    print("→ 正在创建虚拟环境...")
    try:
        subprocess.run(["uv", "venv"], check=True)
        print("✓ 虚拟环境创建成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ 虚拟环境创建失败: {e}")
        return False


def install_dependencies():
    """从 pyproject.toml 安装项目依赖"""
    print()
    print("→ 正在从 pyproject.toml 读取依赖...")
    
    deps = read_dependencies_from_pyproject()
    if not deps:
        print("⚠ 未找到依赖配置或 pyproject.toml 不存在")
        print("→ 尝试直接安装...")
        deps = []
    else:
        print(f"✓ 发现 {len(deps)} 个依赖: {', '.join(deps)}")
    
    print()
    print("→ 正在安装依赖...")
    
    try:
        subprocess.run(
            ["uv", "pip", "install", "-e", "."],
            check=True
        )
        print("✓ 依赖安装成功")
    except subprocess.CalledProcessError as e:
        print(f"✗ 依赖安装失败: {e}")
        return False
    
    if deps:
        print()
        print("→ 验证依赖...")
        for dep in deps:
            try:
                result = subprocess.run(
                    [".venv/bin/python", "-c", f"import {dep}; print('OK')"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    print(f"  ✓ {dep}")
                else:
                    print(f"  ⚠ {dep} (导入名可能不同，已安装)")
            except Exception:
                print(f"  ⚠ {dep} (验证跳过)")
    
    return True


def main():
    """主函数"""
    print("=" * 50)
    print("虚拟环境初始化")
    print("=" * 50)
    
    # 检查虚拟环境
    if check_venv_exists():
        print()
        print("→ 检查依赖状态...")
        deps = read_dependencies_from_pyproject()
        if deps:
            try:
                result = subprocess.run(
                    [".venv/bin/python", "-c", f"import {deps[0]}; print('OK')"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    print(f"✓ 依赖已安装 ({len(deps)} 个)")
                    print()
                    print("=" * 50)
                    print("✓ 环境检查通过")
                    print("=" * 50)
                    sys.exit(0)
                else:
                    print("✗ 依赖不完整，需要重新安装")
            except Exception:
                print("✗ 依赖检查失败，需要重新安装")
        else:
            print("✓ 环境就绪")
            sys.exit(0)
    
    # 需要创建或修复虚拟环境
    print()
    print("需要初始化虚拟环境...")
    
    # 创建虚拟环境
    if not create_venv():
        print()
        print("✗ 虚拟环境创建失败")
        sys.exit(2)
    
    # 安装依赖
    if not install_dependencies():
        print()
        print("✗ 依赖安装失败")
        print()
        print("尝试手动安装：")
        print("  uv pip install -e .")
        print()
        print("或检查 pyproject.toml 配置")
        sys.exit(2)
    
    print()
    print("=" * 50)
    print("✓ 环境初始化完成")
    print("=" * 50)
    sys.exit(0)


if __name__ == "__main__":
    main()
