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
