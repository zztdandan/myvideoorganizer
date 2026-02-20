---
description: 整理电影目录（AI 命名 + 归档）
model: anthropic/claude-sonnet-4-5
---

加载 `movie-organizer` skill，对 memory 中记录的 `last_movie_path` 执行整理。

如果 memory 中无记录，询问用户目标路径。
