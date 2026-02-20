# 视频整理器 Agent 化改造计划（细化版）

## 1. 目标定义
- **核心目标**：把原项目改造成纯 Opencode 工程，Python 仅作为技能脚本的执行载体。
- **交互方式**：仅保留 Opencode 前端与其 API 生态；删除 Flask 与原前端。
- **风格要求**：以“技能自治 + 轻脚本”为原则，不构建共享 core。

## 2. Agent 体系设计（主 Agent + Subagent）
### 2.1 主 Agent：`videomanager`
- **职责**：项目唯一入口，负责指挥技能、维护记忆、执行高层流程。
- **能力限制**：
  - **禁止**调用非本项目注册的 MCP/skills。
  - **Bash/tool 调用受限**（只允许白名单指令，如 `ls`, `cat`, `python`, `uv`, `venv` 等；不允许 `rm -rf` 等破坏性操作）。
- **上下文**：作为开发和调试人员，在videomanager目录启动 Opencode 时， 可切换使用 `videomanager` agent，当videomanager作为一个服务独立启动时，其启动命令将直接屏蔽agent切换，以 `videomanager`作为唯一的agent启动，将其作为一个后台服务提供服务内容
- **Memory 责任**：所有短期记忆（路径、上次任务、最近计划文件位置）由该 Agent 维护。

### 2.2 子 Agent（Subagents）
**原则**：只设计必须的子 Agent，且明确各自职责与权限。
很多需要调用大模型完成的功能，将直接派发给子subagent完成，以及很多长线但是

- **subagent：`movie-info`**
  - 处理电影整理中的信息抽取、命名建议、年份判断。以及对应nfo文件的相关操作

- **subagent：`scraper`（预留）**
  - 负责未来刮削任务

- **subagent: `115oper` (预留) **
  - 负责未来115相关的加链接，下载等操作

## 3. 配置体系（Skill 化配置）
### 3.1 Config Skill 作为统一配置管理者
- **Config Skill** 负责：
  1) 初始化默认 TOML 配置
  2) 读取 + 修改配置
  3) 为用户翻译配置含义（解释每个字段的作用）
  4) 输出给 agent 可读的“摘要版配置”

### 3.2 配置读取方式
- 配置由大模型读取理解，脚本仅接收参数。
- Config Skill 提供两种输出：
  - **原始 TOML**（机器可读）
  - **解释版 Markdown**（人类可读）

### 3.2.1 大模型读取与传参
- 配置**由大模型读取理解**，不是程序读取。
- 大模型理解配置后，将各个子功能skill所需的各类参数，作为参数传给对应 Python 脚本。这样的好处是，配置修改灵活，大模型理解，skill与配置不严格绑定，增加整体柔性

### 3.3 路径记忆（短期记忆）
- 路径信息不放入主配置。
- 单独使用简易 **md/txt** 记录“上一次操作目录”。
- 每个 Skill 引用对应的“记忆文件”。

### 3.4 大模型配置
- 原配置中 LLM 调用字段移除。
- 需要模型能力时，直接派发 **Subagent** 任务（Opencode 友好）。

## 4. Skill 设计原则（功能 Skill 统一规范）
- **关键功能 Skill**，每个 Skill 自治。
- 每个 Skill 内含：
  - **计划生成**（生成 JSON 文件）
  - **执行逻辑**（可读取指定 JSON 进行执行）
- 可支持两种模式：
  1) 仅计划 → 写入 JSON
  2) 计划 + 执行联动 → JSON 只用于事后核对
  3) **仅执行** → 指定已有 JSON 计划文件进行执行

### 4.1 Skill 文件结构规范（统一）
每个功能 Skill 包含：
- `SKILL.md`：技能说明（用途、输入输出、计划/执行模式、日志目录、示例）
- `skill.py`：入口（解析参数 → 计划/执行/合并）
- `planner.py`：生成计划逻辑
- `executor.py`：执行计划逻辑
- `logs/`：独立日志目录
- `plans/`：计划文件存储目录

### 4.2 计划 JSON 规范（统一约定，每个skill可增加它所需要的细节字段，只需要自己的executor可以识别即可）
- 文件命名：`{func}_{YYYYMMDD_HHMMSS}.json`
- 内容字段：
  - `action`: MOVE / RENAME / DELETE
  - `source`：若操作文件，则代表
  - `destination`
  - `size_mb`
  - `func`
  - `created_at`

## 5. 日志体系
- 每个 Skill **独立日志目录**。
- 不需要共享日志系统，也不需要集中 core 处理。
- 每个脚本自行输出日志。

## 6. 共享能力策略
- **不做共享能力**。
- 每个 Skill 内复制所需逻辑，独立运转。
- 任何 helper / classifier 等能力都只在 Skill 内存在。

## 7. Python 运行环境
- 全项目使用**本地 uv 环境**（推荐）或 venv。
- 所有 Skill 共享该环境的依赖包。
- **不得使用全局环境**。

## 8. 目录结构（遵循 Opencode 技能目录规范）
**注意**：技能必须放在 Opencode 默认搜索目录内，避免无法加载。

推荐目录：
- 项目级：`.opencode/skills/`
- 备选：`.agents/skills/`

统一采用：`.opencode/skills/`

```
/.opencode/skills/
├── config-skill/               # 配置管理 Skill（初始化+修改+解释）
│   ├── SKILL.md
│   ├── skill.py
│   ├── config.default.toml
│   └── docs/
│       └── config_fields.md    # 配置项解释
├── video-cleaner/
│   ├── SKILL.md
│   ├── skill.py
│   ├── planner.py
│   ├── executor.py
│   ├── logs/
│   └── plans/
├── video-renamer/
│   ├── SKILL.md
│   ├── skill.py
│   ├── planner.py
│   ├── executor.py
│   ├── logs/
│   └── plans/
├── video-actor-organizer/
│   ├── SKILL.md
│   ├── skill.py
│   ├── planner.py
│   ├── executor.py
│   ├── logs/
│   └── plans/
├── video-big-detector/
│   ├── SKILL.md
│   ├── skill.py
│   ├── planner.py
│   ├── executor.py
│   ├── logs/
│   └── plans/
└── movie-organizer/
    ├── SKILL.md
    ├── skill.py
    ├── planner.py
    ├── executor.py
    ├── logs/
    └── plans/

videomanager/
├── memory/
│   ├── last_clean_path.txt
│   ├── last_rename_path.txt
│   ├── last_actor_path.txt
│   ├── last_bigvideo_path.txt
│   └── last_movie_path.txt
├── env/
│   └── uv.md
└── notes/
    └── future_skills.md
```

## 9. 未来扩展余量（预留 Skill 空间）
- 刮削（scraping）
- 时间对比 / 去重
- 115 下载 / 重挂载
- 115 下载后替换逻辑
- 新的整理能力

*以上扩展将按同一“单 Skill 自治”原则加入 `skills/` 目录。*

## 10. 迁移执行顺序（简版）
1) 建立 Config Skill + TOML 配置模板 + memory 文件
2) 迁移 6 个功能为独立 Skill（计划+执行二合一）
3) 移除 Flask 与旧前端
4) 引入后续扩展 Skill
