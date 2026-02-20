---
description: 清理视频目录（非视频文件夹 + 无用文件）
model: anthropic/claude-sonnet-4-5
---

加载 `video-cleaner` skill，对 memory 中记录的 `last_clean_path` 执行清理。

如果 memory 中无记录，询问用户目标路径。

默认执行 func1（清理非视频文件夹）+ func2（清理无用文件）。
