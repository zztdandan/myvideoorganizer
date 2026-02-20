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
