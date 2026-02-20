# 获取最近一次提交的哈希
$lastCommitHash = git log -1 --pretty=format:"%H"

# 获取最近一次提交的更改文件列表
$changedFiles = git diff-tree --no-commit-id --name-only -r $lastCommitHash

# 创建一个输出文件
$outputFile = "changes.txt"

# 清空输出文件
Clear-Content -Path $outputFile

# 遍历每个更改的文件并将其更改内容追加到输出文件中
foreach ($file in $changedFiles) {
    
    # 获取文件的更改内容
    $diffContent = git diff $lastCommitHash~1 $lastCommitHash -- $file

    # 将文件名和更改内容写入输出文件
    Add-Content -Path $outputFile -Value "File: $file"
    Add-Content -Path $outputFile -Value $diffContent
    Add-Content -Path $outputFile -Value "`n`n"  # 添加换行以分隔文件
}

Write-Host "所有更改内容已输出到 $outputFile"
