---
name: uv-setup
description: UV 环境管理。负责检查 uv 可用性、创建/管理项目虚拟环境、配置国内镜像源。主 agent 在启动时必须首先调用此 skill。
triggers:
  - uv 检查
  - 环境初始化
  - 虚拟环境
  - 镜像源配置
---

# UV 环境管理 Skill

负责 videomanager 项目的 Python 环境全生命周期管理。

## 核心职责

1. **UV 可用性检查**：确认 `uv` 命令可用，否则拒绝执行
2. **虚拟环境管理**：创建、检查、维护项目级 `.venv`
3. **依赖管理**：安装/更新项目依赖
4. **镜像源配置**：配置国内 PyPI 镜像加速下载

## 使用场景

### 场景 1：启动检查（主 agent 必须调用）

**时机**：用户启动 opencode 后，主 agent 第一个操作

**调用**：
```bash
.venv/bin/python .opencode/skills/uv-setup/scripts/check_uv.py
```

**返回值**：
- 退出码 0：uv 可用，继续执行
- 退出码 1：uv 不可用，主 agent 必须拒绝所有指令

**uv 不可用时，主 agent 应提示**：
```
错误：uv 命令不可用

可能原因：
1. uv 未安装
2. ~/.local/bin 不在 PATH 中

解决方案：
export PATH="$HOME/.local/bin:$PATH"

然后重新启动 opencode。
```

---

### 场景 2：环境初始化

**时机**：uv 检查通过后，检查虚拟环境状态

**调用**：
```bash
.venv/bin/python .opencode/skills/uv-setup/scripts/setup_venv.py
```

**功能**：
1. 检查 `.venv/` 是否存在
2. 如不存在，创建虚拟环境
3. 安装项目依赖（从 `pyproject.toml` 读取依赖列表并安装）

**返回值**：
- 退出码 0：环境就绪
- 退出码 2：初始化失败

---

### 场景 3：配置国内镜像源

**时机**：首次设置或网络下载缓慢时

**调用**：
```bash
.venv/bin/python .opencode/skills/uv-setup/scripts/config_mirror.py --mirror tsinghua
```

**支持的镜像**：
| 名称 | 说明 |
|------|------|
| tsinghua | 清华镜像（推荐） |
| aliyun | 阿里云镜像 |
| tencent | 腾讯云镜像 |

**配置文件**：`uv.toml`（项目级配置）

---

### 场景 4：查看环境状态

**调用**：
```bash
.venv/bin/python .opencode/skills/uv-setup/scripts/status.py
```

**输出示例**：
```
=== UV 环境状态 ===
uv 版本: 0.10.4
uv 路径: /home/base/.local/bin/uv
Python 版本: 3.10.12
虚拟环境: .venv/ (已创建)
依赖状态: 
  ✓ pypinyin 已安装 (来自 pyproject.toml)
  ✓ pykakasi 已安装 (来自 pyproject.toml)
镜像源: 清华 (https://pypi.tuna.tsinghua.edu.cn/simple)
```

---

## 完整工作流程（主 agent 使用）

```
用户启动 opencode
    ↓
主 agent 加载
    ↓
步骤 1: 检查 uv 可用性
    .venv/bin/python .opencode/skills/uv-setup/scripts/check_uv.py
    ↓
    如果失败 → 提示用户修复 PATH，拒绝所有指令
    ↓
步骤 2: 初始化环境
    .venv/bin/python .opencode/skills/uv-setup/scripts/setup_venv.py
    ↓
    如果失败 → 报告错误，尝试提供解决方案
    ↓
步骤 3: 环境就绪，开始处理用户指令
```

---

## 文件说明

| 脚本 | 用途 |
|------|------|
| `check_uv.py` | 检查 uv 命令是否可用 |
| `setup_venv.py` | 创建虚拟环境、安装依赖 |
| `config_mirror.py` | 配置国内镜像源 |
| `status.py` | 查看完整环境状态 |

---

## 配置说明

### uv.toml（自动创建）

```toml
# 默认索引 - 清华镜像
[[index]]
name = "tsinghua"
url = "https://pypi.tuna.tsinghua.edu.cn/simple"
default = true
```

### 环境变量

| 变量 | 说明 |
|------|------|
| `UV_PROJECT_ENVIRONMENT` | 虚拟环境路径（默认：`.venv`） |
| `UV_DEFAULT_INDEX` | 默认 PyPI 镜像源 |
| `UV_PYTHON` | 指定 Python 版本 |

---

## 注意事项

1. **所有脚本使用项目虚拟环境 Python**：`.venv/bin/python`
2. **不依赖系统 Python**：虚拟环境完全隔离
3. **自动处理依赖**：skill 会自动从 `pyproject.toml` 读取并安装项目所有依赖
4. **幂等设计**：重复运行不会出错，会检查状态后跳过已完成步骤

---

## 故障排除

### uv 命令未找到

**现象**：`check_uv.py` 返回退出码 1

**解决**：
```bash
export PATH="$HOME/.local/bin:$PATH"
# 添加到 ~/.bashrc 使其永久生效
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
```

### 虚拟环境创建失败

**现象**：`setup_venv.py` 返回退出码 2

**可能原因**：
- Python 版本不兼容
- 磁盘空间不足
- 网络问题（下载依赖失败）

**解决**：
1. 检查 Python 版本：`python3 --version`（需要 >=3.10）
2. 检查磁盘空间：`df -h`
3. 配置国内镜像源后重试

### 依赖安装失败

**现象**：从 `pyproject.toml` 安装依赖失败

**解决**：
```bash
# 查看具体失败信息
.venv/bin/python .opencode/skills/uv-setup/scripts/setup_venv.py

# 或手动安装（仅用于调试）
.venv/bin/python -m pip install <package-name>
```
