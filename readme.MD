# 视频文件夹整理工具

## 项目介绍
本项目是一个用于整理视频文件夹的 Python 工具，支持通过命令行或 HTTP 触发功能。工具可以根据配置文件对视频文件夹进行清理、重命名等操作，并支持预览和生成操作计划。本工具主要旨在弥补jellyfin的整理功能不足，且我下载的资源有大量杂七杂八的文件，需要手动清除，我暂不想做jellyfin的插件，所以做个python脚本简单处理下。

## 功能列表
1. **视频文件夹初步整理**：识别并清理非视频文件夹。
2. **视频文件夹内部文件清理**：清理视频文件夹中的无用文件。
3. **视频文件重命名**：对视频文件进行重命名。
4. **操作计划生成与执行**：支持生成操作计划并执行。

## 使用方法
1. **安装依赖**：
   ```bash
   pip install -r requirements.txt
   ```

2. **配置**：
   - 修改 `config.py` 文件，设置目标目录、文件扩展名、图片关键字等配置项。

3. **运行**：
   - 通过命令行运行：
     ```bash
     python main.py func1 --mode=preview
     ```
   - 所有命令可参照[commands.md](commands.md)进行触发
   - 通过 HTTP 触发（需实现 HTTP 接口）。

## 配置文件
配置文件 `config.py` 支持多套配置（如 `dev1`, `dev2`, `release`），配置项包括：
- 视频文件大小阈值
- 文件扩展名
- 图片文件关键字
- 操作模式（预览、生成 JSON、执行）

## 日志系统
日志系统使用 Python 的 `logging` 模块，支持不同日志级别（如 `DEBUG`, `INFO`, `WARNING`, `ERROR`），日志输出到文件和命令行。

## 操作计划 JSON 格式
操作计划 JSON 文件包含文件的全路径、操作类型（如 `move`, `rename`, `ignore`）等信息，格式如下：
```json
[
    {
        "path": "/path/to/file",
        "operation": "move",
        "destination": "/path/to/destination"
    }
]
```

## 贡献
欢迎提交 Issue 和 Pull Request 来改进本项目。