#!/usr/bin/env python3
"""
video-cleaner: execute_plan.py
执行清理计划（移动文件/文件夹到删除目录）
"""

import argparse
import json
import shutil
from pathlib import Path
from datetime import datetime


def parse_args():
    parser = argparse.ArgumentParser(description="执行清理计划")
    parser.add_argument("--plan", required=True, help="计划 JSON 文件路径")
    parser.add_argument("--dry-run", action="store_true", help="模拟执行，不实际移动")
    return parser.parse_args()


def execute_operation(operation: dict, dry_run: bool = False) -> dict:
    """执行单个操作"""
    source = Path(operation["source"])
    destination = Path(operation["destination"])
    
    result = {
        "success": False,
        "message": "",
        "source": str(source),
        "destination": str(destination)
    }
    
    if not source.exists():
        result["message"] = f"Source does not exist: {source}"
        return result
    
    if dry_run:
        result["success"] = True
        result["message"] = f"[DRY RUN] Would move: {source} -> {destination}"
        return result
    
    try:
        # 确保目标目录存在
        destination.parent.mkdir(parents=True, exist_ok=True)
        
        # 移动文件/文件夹
        shutil.move(str(source), str(destination))
        
        result["success"] = True
        result["message"] = f"Moved: {source.name}"
    except Exception as e:
        result["message"] = f"Error: {e}"
    
    return result


def log_execution(log_file: Path, results: list, plan_file: Path):
    """记录执行日志"""
    with open(log_file, "w", encoding="utf-8") as f:
        f.write(f"# Execution Log\n")
        f.write(f"Plan: {plan_file}\n")
        f.write(f"Time: {datetime.now().isoformat()}\n")
        f.write(f"\n## Results\n\n")
        
        success_count = sum(1 for r in results if r["success"])
        fail_count = len(results) - success_count
        
        f.write(f"Total: {len(results)}, Success: {success_count}, Failed: {fail_count}\n\n")
        
        for i, result in enumerate(results, 1):
            status = "✓" if result["success"] else "✗"
            f.write(f"{i}. {status} {result['message']}\n")


def main():
    args = parse_args()
    
    plan_file = Path(args.plan).resolve()
    if not plan_file.exists():
        print(f"Error: Plan file does not exist: {plan_file}")
        exit(1)
    
    # 读取计划
    try:
        with open(plan_file, "r", encoding="utf-8") as f:
            operations = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON file: {e}")
        exit(1)
    except Exception as e:
        print(f"Error reading plan file: {e}")
        exit(1)
    
    print(f"Executing plan: {plan_file}")
    print(f"Total operations: {len(operations)}")
    
    if args.dry_run:
        print("\n*** DRY RUN MODE - No actual changes will be made ***\n")
    
    # 执行所有操作
    results = []
    for i, operation in enumerate(operations, 1):
        print(f"[{i}/{len(operations)}] ", end="")
        result = execute_operation(operation, args.dry_run)
        results.append(result)
        print(result["message"])
    
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"execute_{timestamp}.log"
    log_execution(log_file, results, plan_file)
    
    # 输出摘要
    success_count = sum(1 for r in results if r["success"])
    print(f"\n{'='*50}")
    print(f"Execution Complete")
    print(f"Total: {len(results)}, Success: {success_count}, Failed: {len(results) - success_count}")
    print(f"Log saved to: {log_file}")
    
    # 输出用于 agent 解析的摘要
    print(f"\nSUMMARY: {success_count}/{len(results)} operations successful")


if __name__ == "__main__":
    main()
