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
