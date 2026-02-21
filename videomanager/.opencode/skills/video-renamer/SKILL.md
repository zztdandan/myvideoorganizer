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
.venv/bin/python .opencode/skills/video-renamer/scripts/plan_rename.py \
  --root "/path/to/videos" \
  --pattern "number2" \
  --output "plans/"

# 仅执行
.venv/bin/python .opencode/skills/video-renamer/scripts/execute_plan.py \
  --plan "plans/rename_20260220_150000.json"
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
- 生成的计划路径，不能放在skill的目录中，要放在agent运行的目录中，保持skill目录清洁
