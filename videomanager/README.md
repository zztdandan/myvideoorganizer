# 视频整理器 - Opencode Agent 驱动版

基于 Opencode Agent 架构的视频文件整理工具。

## 项目定位

这是一个**纯 Opencode Agent 驱动的工程**。用户在 `videomanager/` 目录下启动 opencode，通过自定义 agent + skills 完成所有视频整理任务。

- **Python 定位**：仅作为被 agent 调用的工具脚本，不承担编排调度职责
- **Agent 定位**：理解配置 → 理解用户意图 → 选择合适 skill → 按 skill 指导调用 Python 脚本 → 返回结果
- **Skill 定位**：操作手册/指南，告诉 agent"怎么做"而非"做什么"

## 功能列表

| 功能 | 说明 | 对应 Skill |
|------|------|-----------|
| 清理非视频文件夹 | 移动不含有效视频的文件夹到 `.delete` | video-cleaner |
| 清理无用文件 | 清理视频文件夹中的非必要文件 | video-cleaner |
| 视频重命名 | 为含多个视频的文件夹添加 cd 序号 | video-renamer |
| 演员分类 | 按演员名拼音首字母分类整理（同时自动识别VR视频） | video-actor-organizer |
| 电影整理 | AI 分析并重命名电影文件夹 | movie-organizer |

## 快速开始

### 1. 初始化配置

```bash
# 复制默认配置
cp .opencode/skills/config-skill/assets/config.default.toml config.toml

# 编辑配置
# vim config.toml
```

### 2. 启动 Opencode

```bash
cd /path/to/videomanager
opencode
```

### 3. 使用命令

```
# 清理视频目录
/clean

# 整理电影目录
/organize

# 查看状态
/status
```

## 目录结构

```
videomanager/
├── .opencode/
│   ├── agents/                   # Agent 定义（复数形式，符合官方规范）
│   │   ├── videomanager.md       # 主 agent
│   │   ├── movie-info.md         # 子 agent：电影信息分析
│   │   ├── scraper.md            # 子 agent：刮削（预留）
│   │   └── 115oper.md            # 子 agent：115操作（预留）
│   ├── commands/                 # 命令定义（复数形式，符合官方规范）
│   │   ├── clean.md              # /clean 命令
│   │   ├── organize.md           # /organize 命令
│   │   └── status.md             # /status 命令
│   ├── skills/
│   │   ├── config-skill/         # 配置管理
│   │   ├── video-cleaner/        # 视频清理
│   │   ├── video-renamer/        # 视频重命名
│   │   ├── video-actor-organizer/# 演员分类（含VR视频自动识别）
│   │   └── movie-organizer/      # 电影整理
│   └── opencode.jsonc            # 项目配置
├── config.toml                   # 业务配置
├── memory/                       # 短期记忆
│   ├── paths.md                  # 路径记忆
│   └── recent.md                 # 操作记录
├── pyproject.toml                # Python 依赖
└── README.md                     # 本文件
```

## 配置说明

配置文件 `config.toml` 包含以下主要配置项：

### [video] 视频相关

- `extensions`：视频文件扩展名列表
- `min_size_mb`：最小视频大小（MB）

### [image] 图片相关

- `extensions`：图片文件扩展名列表
- `valid_keywords`：有效图片关键词

### [cleanup] 清理相关

- `delete_dir_name`：删除文件存放目录名（默认 `.delete`）

### [actor] 演员分类相关

- `unknown_category`：未知演员分类（默认 `99`）
- `japanese_category`：日文名演员分类（默认 `0`）
- `title_max_length`：标题最大长度

### [movie] 电影整理相关

- `force_reorganize`：是否强制重新整理已整理的文件夹

详细配置说明见 `.opencode/skills/config-skill/references/config-fields.md`

## 数据流示例

### 清理视频目录

```
用户：清理一下 /mnt/nas/jav 目录

主 agent videomanager：
  1. 加载 config-skill → read config.toml → 理解配置
  2. 加载 video-cleaner skill → 阅读 SKILL.md
  3. 组装参数并执行 plan_clean_folders.py
  4. 向用户展示摘要："发现 35 个非视频文件夹，共 1.2GB，将移动到 .delete 目录。是否执行？"

用户：执行

主 agent：
  5. 执行 execute_plan.py
  6. 更新记忆：write memory/paths.md, append memory/recent.md
```

## 技术栈

- Python 3.11+
- uv：Python 包管理
- pypinyin：中文拼音转换
- pykakasi：日文假名转换

## 许可证

MIT License
