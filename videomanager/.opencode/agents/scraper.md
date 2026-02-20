---
mode: subagent
description: 刮削代理。从指定网站获取视频元数据（演员、标题、封面等）。通过 @scraper 调用。
model: openrouter/moonshotai/kimi-k2.5
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
