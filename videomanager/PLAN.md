# 视频整理器 Agent 化改造计划（最终详细版）

## 1. 项目定位与目标

### 1.1 核心定位
这是一个**纯 Opencode Agent 驱动的工程**。用户在 `videomanager/` 目录下启动 opencode，通过自定义 agent + skills 完成所有视频整理任务。

- **Python 定位**：仅作为被 agent 调用的工具脚本，不承担编排调度职责
- **Agent 定位**：理解配置 → 理解用户意图 → 选择合适 skill → 按 skill 指导调用 Python 脚本 → 返回结果
- **Skill 定位**：操作手册/指南，告诉 agent"怎么做"而非"做什么"

### 1.2 删除内容
- ❌ Flask Web 服务（app.py）
- ❌ HTML 前端（templates/ + static/）
- ❌ CLI 入口（main.py）
- ❌ 共享 core 库（helpers.py, executor.py 等）
- ❌ 类属性配置（config.py）

### 1.3 新增内容
- ✅ Agent 定义（.opencode/agent/*.md）
- ✅ Skill 定义（.opencode/skills/*/SKILL.md）
- ✅ Command 快捷指令（.opencode/command/*.md）
- ✅ TOML 配置（config.toml）
- ✅ 短期记忆文件（memory/*.md）
- ✅ 独立 Python 脚本（每个 skill 自包含所需逻辑）

---

## 2. 目录结构总览

```
videomanager/                           # 项目根目录（用户在此启动 opencode）
├── .opencode/                          # Opencode 配置目录
│   ├── agent/                          # Agent 定义（注意是单数）
│   │   ├── videomanager.md            # 主 agent
│   │   ├── movie-info.md              # 子 agent：电影信息分析
│   │   ├── scraper.md                 # 子 agent：刮削（预留）
│   │   └── 115oper.md                 # 子 agent：115操作（预留）
│   ├── command/                        # 快捷命令（注意是单数）
│   │   ├── clean.md                   # /clean 命令
│   │   ├── organize.md                # /organize 命令
│   │   └── status.md                  # /status 命令
│   ├── skills/                         # 技能目录
│   │   ├── config-skill/
│   │   │   ├── SKILL.md
│   │   │   ├── references/
│   │   │   │   └── config-fields.md
│   │   │   └── assets/
│   │   │       └── config.default.toml
│   │   ├── video-cleaner/
│   │   │   ├── SKILL.md
│   │   │   ├── scripts/
│   │   │   │   ├── plan_clean_folders.py
│   │   │   │   ├── plan_clean_files.py
│   │   │   │   └── execute_plan.py
│   │   │   ├── logs/
│   │   │   └── plans/
│   │   ├── video-renamer/
│   │   │   ├── SKILL.md
│   │   │   ├── scripts/
│   │   │   │   ├── plan_rename.py
│   │   │   │   └── execute_plan.py
│   │   │   ├── logs/
│   │   │   └── plans/
│   │   ├── video-actor-organizer/
│   │   │   ├── SKILL.md
│   │   │   ├── scripts/
│   │   │   │   ├── plan_actor_classify.py
│   │   │   │   ├── execute_plan.py
│   │   │   │   └── classifier.py
│   │   │   ├── logs/
│   │   │   └── plans/
│   │   ├── video-big-detector/
│   │   │   ├── SKILL.md
│   │   │   ├── scripts/
│   │   │   │   ├── plan_big_video.py
│   │   │   │   ├── execute_plan.py
│   │   │   │   └── classifier.py
│   │   │   ├── logs/
│   │   │   └── plans/
│   │   └── movie-organizer/
│   │       ├── SKILL.md
│   │       ├── scripts/
│   │       │   ├── plan_movie_organize.py
│   │       │   ├── execute_plan.py
│   │       │   └── helpers.py
│   │       ├── logs/
│   │       └── plans/
│   └── opencode.jsonc                  # 项目级 Opencode 配置
├── config.toml                         # 业务配置（TOML 格式）
├── memory/                             # 短期记忆
│   ├── paths.md                        # 各功能上次操作路径
│   └── recent.md                       # 最近操作记录
├── pyproject.toml                      # uv 依赖管理
├── .python-version                     # Python 版本锁定
├── .venv/                              # 本地虚拟环境（uv 管理）
├── .gitignore
├── README.md                           # 项目说明
└── PLAN.md                             # 本文件
```

**关键说明**：
- `.opencode/` 位于 `videomanager/` 内部（不是外层 myvideoorganizer/）
- agent、command 目录名为单数（Opencode 规范）
- 所有 Python 脚本自包含于各 skill 的 `scripts/` 目录

---

## 3. Agent 体系设计

### 3.1 主 Agent：`videomanager`

**文件路径**：`.opencode/agent/videomanager.md`

**完整内容**：
```markdown
---
mode: primary
description: 视频整理管理器。负责文件整理、清理、重命名、演员分类、超宽检测、电影归档等任务，以及之后的其他视频相关整理任务。当用户提到视频整理、清理、重命名、分类、电影整理等需求时使用。
model: anthropic/claude-sonnet-4-5
color: "#FF6B35"
tools:
  "*": false
  "bash": true
  "read": true
  "write": true
  "glob": true
  "grep": true
  "skill": true
---

# 视频整理管理器

你是视频整理系统的主 Agent，负责协调所有视频整理任务。

## 启动流程

1. **加载配置**：首次启动时，加载 `config-skill` 读取 `config.toml`。若配置文件不存在，引导用户初始化。
2. **读取记忆**：检查 `memory/paths.md` 获取上次操作路径，`memory/recent.md` 获取最近操作记录。
3. **理解意图**：根据用户指令，判断需要执行哪个功能（清理/重命名/分类/检测/整理）。
4. **加载 Skill**：调用对应的功能 skill，按 skill 指示执行。

## 工具使用限制

- **Bash 白名单**：只允许 `ls`, `cat`, `python`, `uv`, `mkdir`, `cp`, `mv`, `find`, `grep`
- **禁止**：`rm`, `rm -rf`, `chmod`, `chown`, `sudo`, `curl`, `wget` 等破坏性或网络操作
- **Python 调用**：统一使用 `uv run python <script>` 或激活虚拟环境后调用

## Memory 管理

- **路径记忆**（`memory/paths.md`）：
  - 记录格式：`last_clean_path: /path/to/dir`
  - 每次操作完成后更新对应路径
  - 下次用户说"继续清理"时，优先使用记忆中的路径

- **操作记录**（`memory/recent.md`）：
  - 记录格式：markdown 列表
  - 示例：`- 2026-02-20 15:30 | 清理 | /mnt/nas/jav | 移动 35 个文件夹`

## 子 Agent 调用

- **@movie-info**：电影信息分析。传入文件夹名、视频文件名、NFO 摘要，返回 JSON 结构。
- **@scraper**（预留）：刮削任务。
- **@115oper**（预留）：115 网盘操作。

## 注意事项

- 配置参数不是硬编码的，而是从 `config.toml` 读取后理解，作为参数传给脚本。
- 每个 skill 都有独立的 `logs/` 和 `plans/` 目录，不要混淆。
- 执行前向用户确认计划摘要，除非用户明确说"直接执行"。
```

---

### 3.2 子 Agent：`movie-info`

**文件路径**：`.opencode/agent/movie-info.md`

**完整内容**：
```markdown
---
mode: subagent
description: 电影信息分析。提取电影中英文名、年份、命名建议。处理 NFO 文件内容解析。通过 @movie-info 调用。
model: anthropic/claude-sonnet-4-5
color: "#3498DB"
tools:
  "*": false
  "read": true
---

# 电影信息分析子 Agent

你是电影信息提取专家，负责分析电影文件夹并提取结构化信息。

## 输入

主 agent 会传给你：
- `folder_name`：文件夹名称（可能包含网站信息、发布组等无关内容）
- `video_files`：视频文件名列表（数组）
- `nfo_summary`：NFO 文件摘要（若有）

## 任务

分析以上信息，提取电影的：
- 中文名（若无则返回 null）
- 英文名（用点分隔单词，如 The.Hobbit.An.Unexpected.Journey）
- 年份（数字）
- 置信度（0-1 之间的浮点数）

## 输出格式

返回 **纯 JSON 对象**（不是数组，不包含 markdown 代码块标记）：

```json
{
  "chinese_name": "霍比特人：意外之旅",
  "english_name": "The.Hobbit.An.Unexpected.Journey",
  "year": 2012,
  "confidence": 0.95
}
```

## 注意事项

- 这是**单个电影**，不是多个电影。
- 文件夹名可能包含网站信息（如 `[www.example.com]`）、发布组（如 `[YTS.MX]`）等，忽略这些。
- 如果 NFO 摘要包含明确的英文名和年份，优先采用。
- 如果没有中文名，`chinese_name` 返回 `null`。
- 只返回 JSON，不要包含任何解释文字。

## 完成后

返回 JSON 后，你的任务完成，上下文清空。主 agent 会拿着这个结果继续后续操作。
```

---

### 3.3 子 Agent：`scraper`（预留）

**文件路径**：`.opencode/agent/scraper.md`

```markdown
---
mode: subagent
description: 刮削代理。从指定网站获取视频元数据（演员、标题、封面等）。通过 @scraper 调用。
model: anthropic/claude-sonnet-4-5
color: "#9B59B6"
tools:
  "*": false
  "bash": true
  "read": true
---

# 刮削子 Agent（预留）

负责从网站刮削视频元数据。

## 输入

- `video_code`：视频编号（如 SSNI-123）
- `source`：刮削源（如 javbus, javdb）

## 输出

返回 JSON：
```json
{
  "title": "视频标题",
  "actors": ["演员1", "演员2"],
  "cover_url": "https://...",
  "year": 2023,
  "tags": ["标签1", "标签2"]
}
```

## 实现状态

预留，暂未实现。
```

---

### 3.4 子 Agent：`115oper`（预留）

**文件路径**：`.opencode/agent/115oper.md`

```markdown
---
mode: subagent
description: 115 网盘操作代理。添加离线任务、下载文件、替换本地文件。通过 @115oper 调用。
model: anthropic/claude-sonnet-4-5
color: "#E74C3C"
tools:
  "*": false
  "bash": true
---

# 115 网盘操作子 Agent（预留）

负责 115 网盘相关操作。

## 功能

- 添加离线下载任务
- 检查下载进度
- 下载完成后自动替换本地文件

## 实现状态

预留，暂未实现。
```

---

## 4. Command 快捷指令

### 4.1 `/clean` 命令

**文件路径**：`.opencode/command/clean.md`

```markdown
---
description: 清理视频目录（非视频文件夹 + 无用文件）
model: anthropic/claude-sonnet-4-5
---

加载 `video-cleaner` skill，对 memory 中记录的 `last_clean_path` 执行清理。

如果 memory 中无记录，询问用户目标路径。

默认执行 func1（清理非视频文件夹）+ func2（清理无用文件）。
```

---

### 4.2 `/organize` 命令

**文件路径**：`.opencode/command/organize.md`

```markdown
---
description: 整理电影目录（AI 命名 + 归档）
model: anthropic/claude-sonnet-4-5
---

加载 `movie-organizer` skill，对 memory 中记录的 `last_movie_path` 执行整理。

如果 memory 中无记录，询问用户目标路径。
```

---

### 4.3 `/status` 命令

**文件路径**：`.opencode/command/status.md`

```markdown
---
description: 查看当前配置和上次操作记录
---

读取并展示：
1. `config.toml` 关键配置项
2. `memory/paths.md` 各功能上次操作路径
3. `memory/recent.md` 最近 5 条操作记录
```

---

## 5. Skill 体系详解

### 5.1 config-skill（配置管理）

**目录结构**：
```
config-skill/
├── SKILL.md
├── references/
│   └── config-fields.md
└── assets/
    └── config.default.toml
```

**SKILL.md 内容**：

````markdown
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
````

**config.default.toml 内容**：

```toml
[video]
# 视频文件扩展名（数组）
extensions = [".mp4", ".mkv", ".avi", ".wmv", ".mov", ".flv", ".rmvb", ".rm", ".3gp", ".m4v", ".m2ts", ".ts", ".mpg"]
# 最小视频大小（MB），小于此值不视为有效视频
min_size_mb = 300

[image]
# 图片文件扩展名
extensions = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff"]
# 有效图片关键词（保留这些图片）
valid_keywords = ["poster", "movie", "folder", "cover", "fanart", "banner", "clearart", "thumb", "landscape", "logo", "clearlogo", "disc", "discart", "backdrop", "keyart"]

[nfo]
# NFO 文件名匹配长度（前 N 个字符）
match_length = 5

[rename]
# 重命名序号模式：number(1,2,3) | letter(A,B,C) | number2(01,02,03)
pattern = "number2"

[cleanup]
# 删除文件存放目录名
delete_dir_name = ".delete"

[bigvideo]
# 超宽视频存放目录名
dir_name = "BIG"
# 超宽视频宽度阈值（像素）
width_threshold = 2000

[actor]
# 未知演员分类
unknown_category = "99"
# 日文名演员分类
japanese_category = "0"
# 标题最大长度（用于文件夹命名）
title_max_length = 10

[movie]
# 是否强制重新整理已整理的文件夹
force_reorganize = false

[plan]
# 每个计划 JSON 文件的最大操作数
batch_size = 200
```

**references/config-fields.md 内容**：

```markdown
# 配置字段说明

## [video] 视频相关

- `extensions`：视频文件扩展名列表。skill 会根据此列表判断文件是否为视频。
- `min_size_mb`：最小视频大小（MB）。小于此值的文件不被视为有效视频，影响"清理非视频文件夹"功能。

## [image] 图片相关

- `extensions`：图片文件扩展名列表。
- `valid_keywords`：有效图片关键词。包含这些关键词的图片（如 poster.jpg）会被保留，其他图片会被清理。

## [nfo] NFO 文件相关

- `match_length`：NFO 文件名匹配长度。清理时，若 NFO 文件名前 N 个字符与某个视频文件名匹配，则保留。

## [rename] 重命名相关

- `pattern`：重命名序号模式。
  - `number`：1, 2, 3, ...
  - `letter`：A, B, C, ...
  - `number2`：01, 02, 03, ...

## [cleanup] 清理相关

- `delete_dir_name`：删除文件存放目录名（默认 `.delete`）。被清理的文件/文件夹会移动到此目录。

## [bigvideo] 超宽视频相关

- `dir_name`：超宽视频存放目录名（默认 `BIG`）。
- `width_threshold`：超宽视频宽度阈值（像素）。视频宽度超过此值且非 16:9 的会被移动到 BIG 目录。

## [actor] 演员分类相关

- `unknown_category`：未知演员分类（默认 `99`）。
- `japanese_category`：日文名演员分类（默认 `0`）。
- `title_max_length`：标题最大长度，超过会被截断（用于文件夹命名）。

## [movie] 电影整理相关

- `force_reorganize`：是否强制重新整理已整理的文件夹（默认 `false`）。已整理的文件夹会带 `.fixed` 后缀。

## [plan] 计划相关

- `batch_size`：每个计划 JSON 文件的最大操作数。超过此数量会分批生成多个 JSON 文件。
```

---

### 5.2 video-cleaner（清理功能）

**目录结构**：
```
video-cleaner/
├── SKILL.md
├── scripts/
│   ├── plan_clean_folders.py
│   ├── plan_clean_files.py
│   └── execute_plan.py
├── logs/
└── plans/
```

**SKILL.md 内容**：

````markdown
---
name: video-cleaner
description: 视频目录清理。扫描并清理非视频文件夹（func1）和无用文件（func2）。当用户提到"清理"、"clean"、"删除无用文件"、"整理目录"时触发。
---

# 视频目录清理 Skill

负责清理视频目录中的无用内容。

## 功能说明

### func1：清理非视频文件夹

扫描指定目录，将**不含任何有效视频文件**的文件夹移至 `.delete` 目录。

有效视频定义：
- 扩展名在配置的 `video.extensions` 列表中
- 文件大小 >= 配置的 `video.min_size_mb`

### func2：清理无用文件

在视频文件夹内，将与视频无关的文件移至 `.delete` 目录。

保留规则：
- 视频文件：全部保留
- 图片文件：
  - 文件名包含配置的 `image.valid_keywords`（如 poster, cover）→ 保留
  - 文件名前 N 个字符与某个视频文件名匹配 → 保留
  - 其他 → 删除
- NFO 文件：
  - 文件名前 N 个字符与某个视频文件名匹配 → 保留
  - 其他 → 删除
- 其他文件：全部删除

## 操作模式

支持三种模式，由用户指令决定：

### 模式 1：仅计划

生成 JSON 计划文件，不执行。

**调用方式**：

```bash
# func1：清理非视频文件夹
uv run python .opencode/skills/video-cleaner/scripts/plan_clean_folders.py \
  --root "/path/to/videos" \
  --extensions ".mp4,.mkv,.avi,.wmv,.mov,.flv,.rmvb,.rm,.3gp,.m4v,.m2ts,.ts,.mpg" \
  --min-size 300 \
  --delete-dir ".delete" \
  --output ".opencode/skills/video-cleaner/plans/"

# func2：清理无用文件
uv run python .opencode/skills/video-cleaner/scripts/plan_clean_files.py \
  --root "/path/to/videos" \
  --video-extensions ".mp4,.mkv,.avi" \
  --image-extensions ".jpg,.png,.gif,.bmp,.webp" \
  --valid-keywords "poster,cover,fanart,banner,thumb,logo" \
  --nfo-match-length 5 \
  --delete-dir ".delete" \
  --output ".opencode/skills/video-cleaner/plans/"
```

**输出**：
- 文件路径：`.opencode/skills/video-cleaner/plans/clean_folders_20260220_150000.json`
- 格式：见下方 JSON 规范

### 模式 2：仅执行

读取已有 JSON 计划文件，执行操作。

**调用方式**：

```bash
uv run python .opencode/skills/video-cleaner/scripts/execute_plan.py \
  --plan ".opencode/skills/video-cleaner/plans/clean_folders_20260220_150000.json"
```

### 模式 3：联动执行

先计划，agent 向用户展示摘要，用户确认后执行。JSON 保留作为事后核查记录。

## 参数来源

Agent 从 `config.toml` 读取配置，理解后作为命令行参数传入：

| 参数 | 配置来源 |
| --- | --- |
| `--extensions` / `--video-extensions` | `[video] extensions` |
| `--min-size` | `[video] min_size_mb` |
| `--image-extensions` | `[image] extensions` |
| `--valid-keywords` | `[image] valid_keywords` |
| `--nfo-match-length` | `[nfo] match_length` |
| `--delete-dir` | `[cleanup] delete_dir_name` |

`--root` 参数：
1. 优先从 `memory/paths.md` 中读取 `last_clean_path`
2. 若无记忆，询问用户

## 计划 JSON 格式

```json
[
  {
    "func": "clean_folders",
    "action": "MOVE",
    "source": "/path/to/videos/non-video-folder",
    "destination": "/path/to/videos/.delete/non-video-folder",
    "size_mb": 12.5,
    "created_at": "2026-02-20T15:00:00"
  },
  {
    "func": "clean_files",
    "action": "MOVE",
    "source": "/path/to/videos/some-movie/useless.txt",
    "destination": "/path/to/videos/.delete/some-movie/useless.txt",
    "size_mb": 0.01,
    "created_at": "2026-02-20T15:00:05"
  }
]
```

## 日志

脚本运行日志输出到 `.opencode/skills/video-cleaner/logs/` 目录。

文件命名：`{func}_{timestamp}.log`

## 脚本职责

### `plan_clean_folders.py`

- 遍历目录树
- 判断文件夹是否包含有效视频
- 生成 MOVE 操作列表
- 写入 JSON 文件

### `plan_clean_files.py`

- 遍历视频文件夹
- 判断每个文件是否有用
- 生成 MOVE 操作列表
- 写入 JSON 文件

### `execute_plan.py`

- 读取 JSON 文件
- 逐条执行 MOVE 操作
- 记录成功/失败日志

## 注意事项

- 脚本**自包含所有所需逻辑**，不依赖外部 helper 模块。
- 文件遍历、视频判断、图片/NFO 判断、文件大小计算等全部在脚本内实现。
- 使用 Python 标准库 + `pathlib`。
````

---

### 5.3 video-renamer（重命名功能）

**目录结构**：
```
video-renamer/
├── SKILL.md
├── scripts/
│   ├── plan_rename.py
│   └── execute_plan.py
├── logs/
└── plans/
```

**SKILL.md 内容要点**：

````markdown
---
name: video-renamer
description: 视频文件重命名。为含多个视频的文件夹按公共前缀 + 序号规则重命名。当用户提到"重命名"、"rename"、"添加 cd 序号"时触发。
---

# 视频重命名 Skill

## 功能

扫描含多个视频的文件夹，按以下规则重命名：

- 公共前缀：取所有视频文件名的公共前缀
- 序号：按配置的 `rename.pattern` 添加 `-cd{序号}`
- 示例：`Movie-A.mp4`, `Movie-B.mp4` → `Movie-cd01.mp4`, `Movie-cd02.mp4`

## 序号规则

从配置 `[rename] pattern` 读取：
- `number`：1, 2, 3, ...
- `letter`：A, B, C, ...
- `number2`：01, 02, 03, ...

## 操作模式

同 video-cleaner，支持三种模式。

## 调用方式

```bash
# 仅计划
uv run python .opencode/skills/video-renamer/scripts/plan_rename.py \
  --root "/path/to/videos" \
  --pattern "number2" \
  --output ".opencode/skills/video-renamer/plans/"

# 仅执行
uv run python .opencode/skills/video-renamer/scripts/execute_plan.py \
  --plan ".opencode/skills/video-renamer/plans/rename_20260220_150000.json"
```

## JSON 格式

```json
[
  {
    "func": "rename",
    "action": "RENAME",
    "source": "/path/to/videos/folder/Movie-A.mp4",
    "destination": "/path/to/videos/folder/Movie-cd01.mp4",
    "size_mb": 1024.5,
    "created_at": "2026-02-20T15:00:00"
  }
]
```

## 注意事项

- 如果文件名已包含 `-cd` 后缀，跳过。
- 脚本自包含公共前缀计算逻辑。
````

---

### 5.4 video-actor-organizer（演员分类）

**目录结构**：
```
video-actor-organizer/
├── SKILL.md
├── scripts/
│   ├── plan_actor_classify.py
│   ├── execute_plan.py
│   └── classifier.py
├── logs/
└── plans/
```

**SKILL.md 内容要点**：

````markdown
---
name: video-actor-organizer
description: 演员分类整理。解析 NFO 文件提取演员名，按拼音首字母/假名分类。当用户提到"演员分类"、"按演员整理"、"actor classify"时触发。
---

# 演员分类整理 Skill

## 功能

1. 扫描视频文件夹，获取第一个 NFO 文件
2. 解析 NFO 提取演员名和标题
3. 按演员名分类：
   - 拼音首字母（A-Z）
   - 假名首字母（A-Z）
   - 日文名 → 分类 `0`
   - 未知演员 → 分类 `99`
4. 生成目标路径：`{root}/{category}/{首字}/{演员名}/{标题}/`

## 特殊处理

FC2/PPV 视频如果没有演员信息，自动添加 `FC2-PPV`, `FC2`, `PPV` 作为演员标签。

## 操作模式

三种模式同上。

## 调用方式

```bash
# 仅计划
uv run python .opencode/skills/video-actor-organizer/scripts/plan_actor_classify.py \
  --root "/path/to/videos" \
  --unknown-category "99" \
  --japanese-category "0" \
  --title-max-length 10 \
  --output ".opencode/skills/video-actor-organizer/plans/"

# 仅执行
uv run python .opencode/skills/video-actor-organizer/scripts/execute_plan.py \
  --plan ".opencode/skills/video-actor-organizer/plans/actor_20260220_150000.json"
```

## classifier.py

自包含演员名分类逻辑：
- 依赖：`pypinyin`, `pykakasi`
- 功能：判断演员名属于哪个分类（A-Z / 0 / 99）

## JSON 格式

```json
[
  {
    "func": "actor_classify",
    "action": "MOVE",
    "source": "/path/to/videos/SSNI-123",
    "destination": "/path/to/videos/A/a/aoi/某个标题",
    "size_mb": 2048.0,
    "created_at": "2026-02-20T15:00:00"
  }
]
```
````

---

### 5.5 video-big-detector（超宽视频检测）

**SKILL.md 内容要点**：

````markdown
---
name: video-big-detector
description: 超宽视频检测。扫描 NFO 中视频宽度 > 阈值且非 16:9 的文件夹，移动到 BIG 目录。当用户提到"超宽视频"、"big video"、"宽屏检测"时触发。
---

# 超宽视频检测 Skill

## 功能

1. 扫描视频文件夹，解析 NFO 中的视频宽度和宽高比
2. 如果宽度 > 阈值（默认 2000）且宽高比 != 16:9，标记为超宽视频
3. 移动到 `{root}/BIG/{category}/{首字}/{演员名}/{标题}/`

## 操作模式

三种模式同上。

## 调用方式

```bash
# 仅计划
uv run python .opencode/skills/video-big-detector/scripts/plan_big_video.py \
  --root "/path/to/videos" \
  --width-threshold 2000 \
  --big-dir "BIG" \
  --output ".opencode/skills/video-big-detector/plans/"
```

## 依赖

复用 `classifier.py`（从 video-actor-organizer 复制一份，自包含）。
````

---

### 5.6 movie-organizer（电影整理）

**SKILL.md 内容要点**：

````markdown
---
name: movie-organizer
description: 电影整理归档。AI 分析电影信息，重命名文件夹和文件，归档到标准结构。当用户提到"电影整理"、"movie organize"、"整理电影目录"时触发。
---

# 电影整理 Skill

## 功能

1. 扫描电影目录，识别电影文件夹
2. **调用 @movie-info 子 agent** 分析电影信息（中英文名、年份）
3. 重命名文件夹：`{中文名}.{英文名} ({年份}).fixed`
4. 重命名视频文件：`{英文名}.{年份}.{技术信息}.{扩展名}`（如 `The.Hobbit.2012.1080p.BluRay.x264.mp4`）
5. 重命名字幕文件：保留语言标识（如 `.chs.srt`）
6. 重命名图片文件：保留关键词（如 `poster.jpg`）
7. 重命名 NFO 文件：`movie.nfo`

## AI 分析环节

**重要**：此 skill 不直接调用 Python AI 库，而是由主 agent 调用 @movie-info 子 agent。

### 流程

1. `plan_movie_organize.py` 脚本接收 `--ai-analysis` 参数（JSON 字符串）
2. 主 agent 在调用脚本前，先调用 @movie-info：
   - 收集文件夹名、视频文件名、NFO 摘要
   - 发送给 @movie-info
   - 获得 JSON 结果：`{ chinese_name, english_name, year, confidence }`
3. 主 agent 将 JSON 结果作为 `--ai-analysis` 参数传给脚本

### 调用示例

```bash
# 主 agent 先调用 @movie-info
# 假设返回：
# {
#   "chinese_name": "霍比特人",
#   "english_name": "The.Hobbit.An.Unexpected.Journey",
#   "year": 2012,
#   "confidence": 0.95
# }

# 然后调用脚本
uv run python .opencode/skills/movie-organizer/scripts/plan_movie_organize.py \
  --root "/path/to/movies" \
  --ai-analysis '{"chinese_name":"霍比特人","english_name":"The.Hobbit.An.Unexpected.Journey","year":2012,"confidence":0.95}' \
  --force-reorganize false \
  --output ".opencode/skills/movie-organizer/plans/"
```

## helpers.py

自包含电影相关辅助函数：
- `extract_technical_info(filename)`：从文件名提取技术信息（1080p, BluRay, x264 等）
- `build_movie_filename(...)`：构建标准电影文件名

## JSON 格式

```json
[
  {
    "func": "movie_organize",
    "action": "MOVE",
    "source": "/path/to/movies/[YTS]The Hobbit (2012)",
    "destination": "/path/to/movies/霍比特人.The.Hobbit.An.Unexpected.Journey (2012).fixed",
    "size_mb": 5120.0,
    "created_at": "2026-02-20T15:00:00"
  },
  {
    "func": "movie_organize",
    "action": "RENAME",
    "source": "/path/to/movies/霍比特人.The.Hobbit.An.Unexpected.Journey (2012).fixed/movie.mkv",
    "destination": "/path/to/movies/霍比特人.The.Hobbit.An.Unexpected.Journey (2012).fixed/The.Hobbit.An.Unexpected.Journey.2012.1080p.BluRay.x264.mkv",
    "size_mb": 4096.0,
    "created_at": "2026-02-20T15:00:05"
  }
]
```
````

---

## 6. Opencode 项目配置

**文件路径**：`.opencode/opencode.jsonc`

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  // 禁用全局工具，只启用项目内定义的
  "tools": {
    "*": false
  },
  // 项目级 MCP（暂无）
  "mcp": {},
  // 项目级插件（暂无）
  "plugin": []
}
```

---

## 7. Python 环境配置

**pyproject.toml**：

```toml
[project]
name = "videomanager"
version = "1.0.0"
description = "视频整理器 - Opencode Agent 驱动版"
requires-python = ">=3.10"
dependencies = [
    "pypinyin>=0.51.0",
    "pykakasi>=2.2.1",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

**.python-version**：

```
3.11
```

---

## 8. Memory 文件格式

### 8.1 memory/paths.md

```markdown
# 路径记忆

last_clean_path: /mnt/nas/jav
last_rename_path: /mnt/nas/jav
last_actor_path: /mnt/nas/jav
last_bigvideo_path: /mnt/nas/jav
last_movie_path: /mnt/nas/movies
```

### 8.2 memory/recent.md

```markdown
# 最近操作记录

- 2026-02-20 15:30 | 清理非视频文件夹 | /mnt/nas/jav | 移动 35 个文件夹，共 1.2GB
- 2026-02-20 14:15 | 清理无用文件 | /mnt/nas/jav | 移动 128 个文件，共 45MB
- 2026-02-19 22:00 | 演员分类 | /mnt/nas/jav | 移动 56 个文件夹
- 2026-02-19 20:30 | 电影整理 | /mnt/nas/movies | 整理 12 部电影
```

---

## 9. 数据流示例

### 示例：清理视频目录

```
用户：清理一下 /mnt/nas/jav 目录

主 agent videomanager：
  1. 加载 config-skill → read config.toml → 理解配置
  2. 加载 video-cleaner skill → 阅读 SKILL.md
  3. 组装参数：
     - --root: /mnt/nas/jav（用户指定）
     - --extensions: 从 config.toml [video] extensions 读取，逗号拼接
     - --min-size: 从 config.toml [video] min_size_mb 读取
     - --delete-dir: 从 config.toml [cleanup] delete_dir_name 读取
  4. 执行：
     bash: uv run python .opencode/skills/video-cleaner/scripts/plan_clean_folders.py \
           --root /mnt/nas/jav --extensions ".mp4,.mkv,..." --min-size 300 --delete-dir ".delete" \
           --output .opencode/skills/video-cleaner/plans/
  5. 读取生成的 JSON，向用户展示摘要：
     "发现 35 个非视频文件夹，共 1.2GB，将移动到 .delete 目录。是否执行？"

用户：执行

主 agent：
  6. 执行：
     bash: uv run python .opencode/skills/video-cleaner/scripts/execute_plan.py \
           --plan .opencode/skills/video-cleaner/plans/clean_folders_20260220_150000.json
  7. 完成后更新记忆：
     write memory/paths.md: last_clean_path: /mnt/nas/jav
     append memory/recent.md: - 2026-02-20 15:30 | 清理非视频文件夹 | /mnt/nas/jav | ...
```

---

### 示例：电影整理（含 AI 分析）

```
用户：整理一下 /mnt/nas/movies

主 agent videomanager：
  1. 加载 config-skill → read config.toml
  2. 加载 movie-organizer skill
  3. 扫描 /mnt/nas/movies，发现文件夹：[YTS]The Hobbit (2012)
  4. 收集信息：
     - folder_name: "[YTS]The Hobbit (2012)"
     - video_files: ["The.Hobbit.2012.1080p.BluRay.mkv"]
     - nfo_summary: "标题: The Hobbit; 年份: 2012"
  5. 调用 @movie-info 子 agent：
     @movie-info: 分析 {...}
     返回：
     {
       "chinese_name": "霍比特人",
       "english_name": "The.Hobbit.An.Unexpected.Journey",
       "year": 2012,
       "confidence": 0.95
     }
  6. 将结果传给脚本：
     bash: uv run python .opencode/skills/movie-organizer/scripts/plan_movie_organize.py \
           --root /mnt/nas/movies \
           --ai-analysis '{"chinese_name":"霍比特人",...}' \
           --force-reorganize false \
           --output .opencode/skills/movie-organizer/plans/
  7. 向用户展示计划摘要，确认后执行
```

---

## 10. 未来扩展

### 10.1 预留 Skill

| Skill 名称 | 说明 | 对应 Subagent |
| --- | --- | --- |
| `scraper` | 网站刮削元数据（演员、封面、标题） | @scraper |
| `time-comparator` | 文件时间对比 / 去重 | 无 |
| `115-downloader` | 115 网盘离线下载 | @115oper |
| `115-replacer` | 下载完成后替换本地文件 | @115oper |
| `metadata-updater` | NFO / 海报批量更新 | @scraper |

### 10.2 扩展方式

1. 在 `.opencode/skills/` 下新建 skill 目录
2. 编写 `SKILL.md` + `scripts/`
3. 如需 AI 能力，定义新的 subagent
4. 无需修改主 agent，自动发现新 skill

---

## 11. 实施顺序

### Phase 1：环境搭建
1. 初始化 uv 环境：`uv init`，编辑 `pyproject.toml`
2. 安装依赖：`uv sync`
3. 创建目录结构：`.opencode/agent/`, `.opencode/command/`, `.opencode/skills/`, `memory/`
4. 创建 `.opencode/opencode.jsonc`

### Phase 2：核心 Agent 与配置
1. 编写 `videomanager.md`（主 agent）
2. 编写 `movie-info.md`（子 agent）
3. 实现 `config-skill`（SKILL.md + config.default.toml + config-fields.md）
4. 测试配置加载

### Phase 3：功能 Skill（逐个实现）
1. `video-cleaner`（优先级最高，最常用）
2. `video-renamer`
3. `video-actor-organizer`
4. `video-big-detector`
5. `movie-organizer`（最复杂，最后实现）

### Phase 4：Command 与测试
1. 编写 `/clean`, `/organize`, `/status` 命令
2. 集成测试各功能
3. 完善日志、错误处理
4. 编写 README.md

---

## 12. 关键设计原则回顾

1. **Agent 思维**：配置由 agent 读取理解，不是程序硬编码。
2. **Skill 自治**：每个 skill 自包含所有逻辑，无共享依赖。
3. **三种模式**：仅计划、仅执行、联动执行，灵活应对不同场景。
4. **记忆机制**：路径记忆 + 操作记录，提升用户体验。
5. **子 Agent**：AI 能力通过子 agent 实现，而非 Python 库调用。
6. **工具限制**：主 agent Bash 白名单，防止破坏性操作。
7. **本地环境**：uv 管理的本地虚拟环境，不污染全局。

---

## 附录：关键文件路径速查

| 类型 | 路径 |
| --- | --- |
| 主 Agent | `.opencode/agent/videomanager.md` |
| 子 Agent | `.opencode/agent/movie-info.md` |
| Config Skill | `.opencode/skills/config-skill/SKILL.md` |
| 配置文件 | `config.toml` |
| 配置说明 | `.opencode/skills/config-skill/references/config-fields.md` |
| 路径记忆 | `memory/paths.md` |
| 操作记录 | `memory/recent.md` |
| 项目配置 | `.opencode/opencode.jsonc` |
| Python 依赖 | `pyproject.toml` |
| 清理 Skill | `.opencode/skills/video-cleaner/SKILL.md` |
| 电影 Skill | `.opencode/skills/movie-organizer/SKILL.md` |

---

**计划版本**：v2.0（2026-02-20）
**下一步**：与用户确认此计划，确认无误后开始 Phase 1 实施。
