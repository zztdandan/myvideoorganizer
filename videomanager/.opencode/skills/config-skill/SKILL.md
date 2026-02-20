---
name: config-skill
description: 视频整理器配置管理。初始化、读取、修改、解释 TOML 配置。当用户提到"配置"、"设置"、"config"、"初始化配置"时触发。
---

# 配置管理 Skill

负责 `config.toml` 的全生命周期管理。

## 配置文件位置

`videomanager/config.toml`

## 功能

### 1. 初始化配置

用户首次使用或说"初始化配置"时：

```bash
cp .opencode/skills/config-skill/assets/config.default.toml config.toml
```

### 2. 读取配置

直接 read `config.toml`，理解后：
- 向用户解释关键配置项
- 或将参数传给其他 skill 的脚本

### 3. 修改配置

用户说"把最小视频大小改成 500MB"：

```bash
# 直接编辑 config.toml，修改对应行
# 例如：min_size_mb = 300 → min_size_mb = 500
```

### 4. 解释配置

加载 `references/config-fields.md`，向用户展示各字段含义。

## 配置项说明

详见 `references/config-fields.md`。

## 注意事项

- 配置**由 agent 读取理解**，不是程序直接读取。
- Agent 理解配置后，将值作为命令行参数传给 Python 脚本。
- 这样做的好处：配置修改灵活，skill 与配置不严格绑定。
