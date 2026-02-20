# 配置字段说明

## [video] 视频相关

- `extensions`：视频文件扩展名列表。skill 会根据此列表判断文件是否为视频。
- `min_size_mb`：最小视频大小（MB）。小于此值的文件不被视为有效视频，影响"清理非视频文件夹"功能。

## [image] 图片相关

- `extensions`：图片文件扩展名列表。
- `valid_keywords`：有效图片关键词。包含这些关键词的图片（如 poster.jpg）会被保留，其他图片会被清理。

## [nfo] NFO 文件相关

- `match_length`：NFO 文件名匹配长度。清理时，若 NFO 文件名前 N 个字符与某个视频文件名匹配，则保留。

## [rename] 重命名相关

- `pattern`：重命名序号模式。
  - `number`：1, 2, 3, ...
  - `letter`：A, B, C, ...
  - `number2`：01, 02, 03, ...

## [cleanup] 清理相关

- `delete_dir_name`：删除文件存放目录名（默认 `.delete`）。被清理的文件/文件夹会移动到此目录。

## [bigvideo] 超宽视频相关

- `dir_name`：超宽视频存放目录名（默认 `BIG`）。
- `width_threshold`：超宽视频宽度阈值（像素）。视频宽度超过此值且非 16:9 的会被移动到 BIG 目录。

## [actor] 演员分类相关

- `unknown_category`：未知演员分类（默认 `99`）。
- `japanese_category`：日文名演员分类（默认 `0`）。
- `title_max_length`：标题最大长度，超过会被截断（用于文件夹命名）。

## [movie] 电影整理相关

- `force_reorganize`：是否强制重新整理已整理的文件夹（默认 `false`）。已整理的文件夹会带 `.fixed` 后缀。

## [plan] 计划相关

- `batch_size`：每个计划 JSON 文件的最大操作数。超过此数量会分批生成多个 JSON 文件。
