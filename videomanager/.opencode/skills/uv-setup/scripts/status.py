#!/usr/bin/env python3
"""
查看 UV 环境状态

输出完整的环境信息，用于诊断问题
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, shell=False):
    """运行命令并返回输出"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            shell=shell,
            check=False
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except Exception:
        return None


def get_uv_info():
    """获取 uv 信息"""
    version = run_command(["uv", "--version"])
    path = run_command(["which", "uv"])
    return version, path


def get_python_info():
    """获取 Python 信息"""
    system_python = run_command(["python3", "--version"])
    
    # 检查虚拟环境 Python
    venv_python = Path(".venv/bin/python")
    if venv_python.exists():
        venv_version = run_command([str(venv_python), "--version"])
        venv_path = str(venv_python.absolute())
    else:
        venv_version = None
        venv_path = None
    
    return system_python, venv_version, venv_path


def read_deps_from_pyproject():
    """从 pyproject.toml 读取依赖列表"""
    import re
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        return []
    
    try:
        content = pyproject_path.read_text(encoding="utf-8")
        match = re.search(r'dependencies\s*=\s*\[(.*?)\]', content, re.DOTALL)
        if not match:
            return []
        
        deps_str = match.group(1)
        deps = re.findall(r'"([^"]+)"', deps_str)
        
        dep_names = []
        for dep in deps:
            for sep in [">=", ">", "==", "<", "~="]:
                if sep in dep:
                    dep = dep.split(sep)[0].strip()
                    break
            dep_names.append(dep)
        
        return dep_names
    except Exception:
        return []


def get_venv_status():
    """获取虚拟环境状态"""
    venv_path = Path(".venv")
    if not venv_path.exists():
        return "未创建", []
    
    checks = []
    
    python_exe = venv_path / "bin" / "python"
    checks.append(("Python 可执行文件", python_exe.exists()))
    
    pip_exe = venv_path / "bin" / "pip"
    checks.append(("pip", pip_exe.exists()))
    
    # 动态检查依赖
    deps = read_deps_from_pyproject()
    if deps:
        for dep in deps[:5]:  # 只显示前5个避免输出过长
            result = run_command([str(venv_path / "bin" / "python"), "-c", f"import {dep}"])
            checks.append((f"依赖: {dep}", result is not None))
        if len(deps) > 5:
            checks.append((f"... 及其他 {len(deps) - 5} 个依赖", True))
    
    return "已创建", checks


def get_mirror_config():
    """获取镜像源配置"""
    uv_toml = Path("uv.toml")
    if uv_toml.exists():
        content = uv_toml.read_text(encoding="utf-8")
        # 简单解析
        if "tsinghua" in content:
            return "清华镜像 (tsinghua)"
        elif "aliyun" in content:
            return "阿里云镜像 (aliyun)"
        elif "tencent" in content:
            return "腾讯云镜像 (tencent)"
        else:
            return "自定义配置"
    
    # 检查环境变量
    default_index = run_command(["echo", "$UV_DEFAULT_INDEX"], shell=True)
    if default_index:
        return f"环境变量: {default_index}"
    
    return "默认 PyPI"


def main():
    """主函数"""
    print("=" * 50)
    print("UV 环境状态")
    print("=" * 50)
    
    # UV 信息
    print()
    print("【UV 信息】")
    uv_version, uv_path = get_uv_info()
    if uv_version:
        print(f"  版本: {uv_version}")
        print(f"  路径: {uv_path or 'N/A'}")
    else:
        print("  ✗ uv 未找到")
    
    # Python 信息
    print()
    print("【Python 信息】")
    system_py, venv_py, venv_path = get_python_info()
    if system_py:
        print(f"  系统 Python: {system_py}")
    if venv_py:
        print(f"  虚拟环境 Python: {venv_py}")
        print(f"  虚拟环境路径: {venv_path}")
    elif not Path(".venv").exists():
        print("  虚拟环境: 未创建")
    
    # 虚拟环境状态
    print()
    print("【虚拟环境状态】")
    status, checks = get_venv_status()
    print(f"  状态: {status}")
    if checks:
        for name, ok in checks:
            symbol = "✓" if ok else "✗"
            print(f"  {symbol} {name}")
    
    # 镜像源配置
    print()
    print("【镜像源配置】")
    mirror = get_mirror_config()
    print(f"  {mirror}")
    
    # 项目信息
    print()
    print("【项目信息】")
    project_path = Path.cwd()
    print(f"  项目目录: {project_path}")
    
    pyproject = project_path / "pyproject.toml"
    print(f"  pyproject.toml: {'✓ 存在' if pyproject.exists() else '✗ 不存在'}")
    
    # 总结
    print()
    print("=" * 50)
    print("状态总结")
    print("=" * 50)
    
    issues = []
    
    if not uv_version:
        issues.append("uv 命令不可用")
    if status == "未创建":
        issues.append("虚拟环境未创建")
    else:
        for name, ok in checks:
            if not ok:
                issues.append(name)
    
    if not issues:
        print("✓ 所有检查通过，环境就绪")
        sys.exit(0)
    else:
        print("✗ 发现问题：")
        for issue in issues:
            print(f"  - {issue}")
        print()
        print("建议运行：")
        print("  .venv/bin/python .opencode/skills/uv-setup/scripts/setup_venv.py")
        sys.exit(1)


if __name__ == "__main__":
    main()
