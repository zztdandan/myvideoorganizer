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
.venv/bin/python .opencode/skills/movie-organizer/scripts/plan_movie_organize.py \
  --root "/path/to/movies" \
  --ai-analysis '{"chinese_name":"霍比特人","english_name":"The.Hobbit.An.Unexpected.Journey","year":2012,"confidence":0.95}' \
  --force-reorganize false \
  --output "plans/"
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
