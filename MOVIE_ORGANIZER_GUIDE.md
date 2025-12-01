# 电影文件夹智能整理功能使用指南

## 功能概述

电影文件夹智能整理功能（func6）使用AI技术自动分析和整理电影文件夹，将其统一为规范的命名格式。

## 命名规则

### 文件夹命名格式
```
中文名.英文名 (年份).fixed
```
例如：`霍比特人.The.Hobbit.An.Unexpected.Journey (2012).fixed`

**注意**：`.fixed` 后缀用于标识已整理的文件夹，系统会自动跳过这些文件夹，避免重复处理。

### 文件命名格式
视频文件保留技术信息，采用点分隔格式：
```
英文名.年份.分辨率.来源.编码.音频.mkv
```
例如：`The.Hobbit.An.Unexpected.Journey.2012.2160p.BluRay.REMUX.HEVC.DTS-HD.MA.TrueHD.7.1.Atmos.mkv`

字幕、图片、NFO等辅助文件使用统一的基础名称。

## 配置步骤

### 1. 配置OpenRouter API密钥

在 `config.py` 的 `DevConfig` 类中设置：

```python
class DevConfig(BaseConfig):
    OPENROUTER_API_KEY = "your-api-key-here"
    OPENROUTER_MODEL = "google/gemini-flash-1.5"  # 可选其他模型
```

### 2. 设置根目录

确保 `ROOT_DIR` 配置正确：

```python
class DevConfig(BaseConfig):
    ROOT_DIR = "Z:/JELLYFIN/MOVIE"  # 您的电影目录
```

## 使用方法

### Web界面使用

1. 启动Web服务：
```bash
python app.py
```

2. 在浏览器中访问 `http://localhost:5050`

3. 在功能列表中选择 "电影文件夹智能整理"

4. 点击"生成计划"查看整理方案

5. 确认无误后点击"执行操作"

### 命令行使用

#### 预览模式（推荐）
```bash
python main.py func6 --mode preview
```
这将显示所有计划的操作，并等待您确认后执行。

#### JSON模式
生成操作计划到JSON文件，稍后执行：
```bash
# 生成计划
python main.py func6 --mode json

# 执行计划
python main.py func6 --json operations/func6_20250101_120000.json
```

## 功能特点

### 1. 智能识别
- 综合分析文件夹名称、视频文件名、NFO内容
- 使用AI提取准确的中英文名和年份
- 支持多种命名风格的电影文件夹

### 2. 系列电影扁平化
自动将嵌套在子目录中的电影移动到根目录：
```
Before:
Mission_-_Impossible_Collection/
  ├─ 碟中谍(1996)/
  ├─ 碟中谍2(2002)/
  └─ 碟中谍3(2006)/

After:
碟中谍.Mission.Impossible (1996)/
碟中谍2.Mission.Impossible.II (2000)/
碟中谍3.Mission.Impossible.III (2006)/
```

### 3. 技术信息保留
视频文件保留原有的技术参数：
- 分辨率（4K, 2160p, 1080p等）
- 视频编码（H.265, HEVC等）
- 音频编码（TrueHD, DTS-HD MA等）
- 来源信息（BluRay, WEB-DL等）
- 特殊标识（IMAX, HDR, DV等）

### 4. 文件类型处理
- **视频文件**：重命名为标准格式
- **字幕文件**：使用主视频的基础名+语言标识
- **图片文件**：保留关键词（poster, fanart等）
- **NFO文件**：统一命名为 `movie.nfo`

### 5. 容错机制
- AI识别失败时自动使用文件夹名解析
- 支持重试机制（最多3次）
- 详细的日志记录

## 注意事项

### 1. API配置
- 确保配置了有效的OpenRouter API密钥
- 首次使用建议先测试几个文件夹
- API调用会产生费用，注意使用量

### 2. 备份建议
- 首次使用前建议备份重要数据
- 使用预览模式确认操作无误
- 可先在小范围测试

### 3. 文件夹识别标准
识别为电影文件夹的条件：
- 包含至少一个大于300MB的视频文件
- 不在 `.delete` 目录中

### 4. 命名冲突
如果目标文件夹已存在，系统会记录错误，不会覆盖现有文件夹。

## 日志查看

所有操作都会记录在日志文件中：
```
logs/organizer_YYYYMMDD.log
```

查看日志了解：
- AI分析结果
- 操作执行状态
- 错误信息和警告

## 常见问题

### Q: AI识别不准确怎么办？
A: 系统会在AI失败时使用原文件夹名，您可以在预览阶段检查并手动调整JSON文件。

### Q: 支持哪些语言的电影？
A: 支持中英文电影，其他语言电影会尝试提取英文名或使用原名称。

### Q: 能否自定义命名格式？
A: 当前版本使用固定格式，如需自定义可修改 `core/planners/movie_planner.py` 中的命名逻辑。

### Q: 系列电影如何处理？
A: 系统会自动将系列电影集合中的子文件夹扁平化到根目录，每个电影独立成为一个文件夹。

## 示例

### 输入示例
```
Z:\JELLYFIN\MOVIE\
├─ Deadpool and Wolverine 2024 2160p WEB-DL/
│  ├─ Deadpool.and.Wolverine.2024.2160p.WEB-DL.mkv
│  ├─ poster.jpg
│  └─ movie.nfo
├─ [Hao4K]你想活出怎样的人生/
│  └─ The.Boy.and.the.Heron.2023.2160p.mkv
└─ 加勒比海盗/
   ├─ 加勒比海盗(2003)/
   └─ 加勒比海盗2-聚魂棺(2006)/
```

### 输出示例
```
Z:\JELLYFIN\MOVIE\
├─ 死侍与金刚狼.Deadpool.and.Wolverine (2024).fixed/
│  ├─ Deadpool.and.Wolverine.2024.2160p.WEB-DL.H.265.mkv
│  ├─ poster.jpg
│  └─ movie.nfo
├─ 你想活出怎样的人生.The.Boy.and.the.Heron (2023).fixed/
│  └─ The.Boy.and.the.Heron.2023.2160p.H.265.mkv
├─ 加勒比海盗.Pirates.of.the.Caribbean (2003).fixed/
│  └─ ...
└─ 加勒比海盗2.Pirates.of.the.Caribbean.Dead.Mans.Chest (2006).fixed/
   └─ ...
```

## 技术支持

如遇到问题，请查看：
1. 日志文件中的详细错误信息
2. 配置是否正确（API密钥、目录路径等）
3. 文件夹是否符合识别标准

更多技术细节请参考源代码注释。

