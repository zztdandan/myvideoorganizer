### 基本功能命令
```bash
# 预览模式（默认）
python main.py func1            # 预览整理文件夹操作
python main.py func2            # 预览整理视频文件操作
python main.py func3            # 预览重命名操作
python main.py func4            # 预览按演员整理文件夹
python main.py func5            # 预览超宽视频处理


# JSON模式（生成操作计划文件）
python main.py func1 --mode json    # 生成文件夹整理的JSON计划
python main.py func2 --mode json    # 生成文件整理的JSON计划
python main.py func3 --mode json    # 生成重命名的JSON计划
python main.py func4 --mode json    # 生成按演员整理的JSON计划
python main.py func5 --mode json    # 生成超宽视频处理的JSON计划


# 执行JSON文件中的操作
python main.py func1 --json operations.json    # 执行指定的JSON操作文件
python main.py func2 --json operations.json
python main.py func3 --json operations.json
python main.py func4 --json operations.json
python main.py func5 --json operations.json
```

### HTTP服务器命令
```bash
# 启动HTTP服务器（默认端口8080）
python main.py --http

# 指定端口启动HTTP服务器
python main.py --http --port 8888
```

### HTTP API 调用示例
```
# 预览模式
http://localhost:8080/organize?function=func1&mode=preview
http://localhost:8080/organize?function=func2&mode=preview
http://localhost:8080/organize?function=func3&mode=preview
http://localhost:8080/organize?function=func4&mode=preview
http://localhost:8080/organize?function=func5&mode=preview

# JSON模式
http://localhost:8080/organize?function=func1&mode=json
http://localhost:8080/organize?function=func2&mode=json
http://localhost:8080/organize?function=func3&mode=json
http://localhost:8080/organize?function=func4&mode=json
http://localhost:8080/organize?function=func5&mode=json

# 执行JSON文件
http://localhost:8080/organize?json_path=operations.json
```

### 帮助命令
```bash
# 显示帮助信息
python main.py -h
python main.py --help
```

参数说明：
- `--mode`: 执行模式，可选 `preview`（默认）或 `json`
- `--json`: 指定要执行的JSON文件路径
- `--http`: 启动HTTP服务器
- `--port`: 指定HTTP服务器端口（默认8080）