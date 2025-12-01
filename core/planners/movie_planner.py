"""
电影整理操作计划生成器
"""
from pathlib import Path
from typing import List, Dict, Optional
import xml.etree.ElementTree as ET
from core.logger import logger
from core.helpers import (
    get_file_size_mb, is_video_file, is_image_file, 
    is_nfo_file, is_subtitle_file, sanitize_folder_name,
    extract_technical_info, build_movie_filename, parse_movie_folder_name,
    get_first_nfo_file, is_movie_folder_organized
)
from core.openrouter_client import OpenRouterClient
from .base_planner import BasePlanner


class MoviePlanner(BasePlanner):
    """电影整理操作计划生成器"""
    
    def __init__(self, config):
        """
        初始化计划生成器
        
        Args:
            config: 配置对象
        """
        super().__init__(config)
        # 电影功能使用MOVIE_DIR，如果未设置则使用ROOT_DIR
        if hasattr(config, 'MOVIE_DIR') and config.MOVIE_DIR:
            self.root_dir = Path(config.MOVIE_DIR)
        # 初始化OpenRouter客户端
        self.ai_client = OpenRouterClient(
            api_key=config.OPENROUTER_API_KEY,
            model=config.OPENROUTER_MODEL,
            api_url=config.OPENROUTER_API_URL
        )
        
    def _extract_nfo_summary(self, nfo_path: Path) -> str:
        """
        从NFO文件中提取摘要信息
        
        Args:
            nfo_path: NFO文件路径
            
        Returns:
            NFO摘要信息字符串
            
        @process:
            1. 解析NFO XML文件
            2. 提取关键信息：标题、年份、演员等
            3. 组合成摘要字符串
        """
        try:
            tree = ET.parse(nfo_path)
            root = tree.getroot()
            
            info_parts = []
            
            # 提取标题
            title_elem = root.find('title')
            if title_elem is not None and title_elem.text:
                info_parts.append(f"标题: {title_elem.text}")
                
            # 提取原始标题
            originaltitle_elem = root.find('originaltitle')
            if originaltitle_elem is not None and originaltitle_elem.text:
                info_parts.append(f"原始标题: {originaltitle_elem.text}")
                
            # 提取年份
            year_elem = root.find('year')
            if year_elem is not None and year_elem.text:
                info_parts.append(f"年份: {year_elem.text}")
                
            # 提取演员（最多3个）
            actors = root.findall('.//actor/name')
            if actors:
                actor_names = [actor.text for actor in actors[:3] if actor.text]
                if actor_names:
                    info_parts.append(f"演员: {', '.join(actor_names)}")
            
            return "; ".join(info_parts) if info_parts else ""
            
        except Exception as e:
            logger.warning(f"解析NFO文件失败 {nfo_path}: {str(e)}")
            return ""
            
    def _collect_movie_folder_info(self, folder_path: Path) -> Optional[Dict]:
        """
        收集电影文件夹的所有相关信息
        
        Args:
            folder_path: 电影文件夹路径
            
        Returns:
            包含文件夹信息的字典，如果不是有效的电影文件夹则返回None
            
        @process:
            1. 检查是否包含大视频文件
            2. 收集所有相关文件：视频、字幕、图片、NFO等
            3. 提取NFO摘要信息
        """
        # 收集文件夹内的所有文件
        video_files = []
        subtitle_files = []
        image_files = []
        nfo_files = []
        other_files = []
        
        for item in folder_path.rglob('*'):
            if item.is_file():
                if is_video_file(item, self.config):
                    video_files.append(item)
                elif is_subtitle_file(item):
                    subtitle_files.append(item)
                elif is_image_file(item, self.config):
                    image_files.append(item)
                elif is_nfo_file(item):
                    nfo_files.append(item)
                else:
                    other_files.append(item)
        
        # 如果没有视频文件，不是有效的电影文件夹
        if not video_files:
            return None
            
        # 提取NFO摘要
        nfo_summary = ""
        if nfo_files:
            nfo_summary = self._extract_nfo_summary(nfo_files[0])
            
        return {
            'path': folder_path,
            'name': folder_path.name,
            'video_files': video_files,
            'subtitle_files': subtitle_files,
            'image_files': image_files,
            'nfo_files': nfo_files,
            'other_files': other_files,
            'nfo_summary': nfo_summary,
            'total_size': sum(get_file_size_mb(f) for f in video_files)
        }
        
    def _scan_movie_folders(self, start_path: Path, depth: int = 0, is_root: bool = True) -> List[Dict]:
        """
        递归扫描电影文件夹
        
        Args:
            start_path: 起始路径
            depth: 当前深度（用于判断是否需要移动到根目录）
            is_root: 是否是根目录（根目录本身不作为电影文件夹处理）
            
        Returns:
            电影文件夹信息列表
            
        @process:
            1. 如果是根目录，跳过自身，只扫描子文件夹
            2. 如果不是根目录，检查当前文件夹是否是电影文件夹
            3. 如果是电影文件夹，收集信息并添加到列表
            4. 否则递归扫描子文件夹
            5. 跳过.delete等特殊文件夹
        """
        movie_folders = []
        
        if not start_path.is_dir() or '.delete' in start_path.parts:
            return movie_folders
        
        # 如果是根目录，直接扫描子文件夹，不检查根目录本身
        if is_root:
            logger.info(f"扫描根目录的子文件夹: {start_path}")
            try:
                for item in start_path.iterdir():
                    if item.is_dir():
                        # 子文件夹depth为0，因为它们是顶层电影文件夹
                        movie_folders.extend(self._scan_movie_folders(item, depth=0, is_root=False))
            except PermissionError:
                logger.warning(f"无权限访问文件夹: {start_path}")
            return movie_folders
            
        # 非根目录：检查当前文件夹是否是电影文件夹
        folder_info = self._collect_movie_folder_info(start_path)
        
        if folder_info:
            # 记录深度信息（用于后续判断是否需要移动）
            folder_info['depth'] = depth
            movie_folders.append(folder_info)
            logger.info(f"发现电影文件夹: {start_path.name} (深度: {depth})")
            # 如果当前文件夹已经是电影文件夹，不再扫描其子文件夹
            return movie_folders
            
        # 如果当前文件夹不是电影文件夹，递归扫描子文件夹
        try:
            for item in start_path.iterdir():
                if item.is_dir():
                    movie_folders.extend(self._scan_movie_folders(item, depth + 1, is_root=False))
        except PermissionError:
            logger.warning(f"无权限访问文件夹: {start_path}")
            
        return movie_folders
        
    def _analyze_and_generate_plan(self, folder_info: Dict) -> List[Dict[str, str]]:
        """
        分析电影文件夹信息并生成操作计划
        
        Args:
            folder_info: 文件夹信息字典
            
        Returns:
            操作计划列表
            
        @process:
            1. 检查文件夹是否已经整理好
            2. 如果已整理，跳过
            3. 调用AI分析电影信息
            4. 如果AI失败，使用fallback策略（解析文件夹名）
            5. 生成新的文件夹名称和文件名称
            6. 创建MOVE或RENAME操作
        """
        operations = []
        folder_path = folder_info['path']
        
        # 检查文件夹是否已经整理好（除非配置了强制重新整理）
        force_reorganize = getattr(self.config, 'MOVIE_FORCE_REORGANIZE', False)
        if not force_reorganize and is_movie_folder_organized(folder_info['name'], folder_info['video_files']):
            logger.info(f"文件夹已经整理好，跳过: {folder_info['name']}")
            return operations
        
        # 准备视频文件名列表
        video_filenames = [vf.name for vf in folder_info['video_files']]
        
        # 调用AI分析
        logger.info(f"开始分析电影信息: {folder_info['name']}")
        ai_result = self.ai_client.analyze_movie_info(
            folder_name=folder_info['name'],
            video_files=video_filenames,
            nfo_content=folder_info['nfo_summary']
        )
        
        # 如果AI分析成功
        if ai_result and ai_result.get('english_name'):
            chinese_name = ai_result.get('chinese_name', '')
            english_name = ai_result['english_name']
            year = str(ai_result.get('year', '')) if ai_result.get('year') else ''
            confidence = ai_result.get('confidence', 0.0)
            
            logger.info(f"AI分析成功 (置信度: {confidence}): 中文={chinese_name}, 英文={english_name}, 年份={year}")
        else:
            # Fallback: 使用文件夹名解析
            logger.warning(f"AI分析失败，使用fallback策略（保留原文件夹名）: {folder_info['name']}")
            parsed = parse_movie_folder_name(folder_info['name'])
            
            # 优先使用解析结果，如果解析失败则使用原名
            chinese_name = parsed.get('chinese_name', '')
            english_name = parsed.get('english_name', '') or folder_info['name']
            year = parsed.get('year', '')
            
            # 如果解析出的英文名包含空格，转换为点分隔
            if english_name and ' ' in english_name:
                english_name = english_name.replace(' ', '.')
            
            # 如果没有英文名，使用原文件夹名
            if not english_name:
                english_name = folder_info['name'].replace(' ', '.')
            
            logger.info(f"Fallback结果: 中文={chinese_name}, 英文={english_name}, 年份={year}")
                
        # 净化名称
        chinese_name = sanitize_folder_name(chinese_name) if chinese_name else ""
        english_name = sanitize_folder_name(english_name)
        
        # 构建新的文件夹名称（加上.fixed后缀标识已整理）
        if chinese_name and year:
            new_folder_name = f"{chinese_name}.{english_name} ({year}).fixed"
        elif chinese_name:
            new_folder_name = f"{chinese_name}.{english_name}.fixed"
        elif year:
            new_folder_name = f"{english_name} ({year}).fixed"
        else:
            new_folder_name = f"{english_name}.fixed"
            
        # 确定目标路径
        # 如果在子目录中（depth > 0），移动到根目录
        if folder_info['depth'] > 0:
            target_folder = self.root_dir / new_folder_name
            action_type = "MOVE"
        else:
            # 如果已经在根目录，只需重命名
            target_folder = self.root_dir / new_folder_name
            action_type = "RENAME" if target_folder != folder_path else "SKIP"
            
        if action_type == "SKIP":
            logger.info(f"文件夹名称无需修改: {folder_path}")
            return operations
            
        # 为文件夹创建操作
        operations.append({
            "function": "func6",
            "action": action_type,
            "source": str(folder_path),
            "destination": str(target_folder),
            "file_size": round(folder_info['total_size'], 2)
        })
        
        # 为文件夹内的文件创建重命名计划
        # 注意：文件的实际重命名会在文件夹移动/重命名后进行
        # 这里我们生成"目标位置的文件重命名"操作
        
        # 处理视频文件
        for video_file in folder_info['video_files']:
            # 提取技术信息
            tech_info = extract_technical_info(video_file.stem)
            
            # 构建新文件名
            new_video_name = build_movie_filename(
                english_name=english_name,
                year=year,
                tech_info=tech_info,
                extension=video_file.suffix
            )
            
            # 计算目标路径
            # 保持文件在文件夹内的相对位置
            relative_path = video_file.relative_to(folder_path)
            source_in_target = target_folder / relative_path
            dest_in_target = target_folder / new_video_name
            
            if source_in_target != dest_in_target:
                operations.append({
                    "function": "func6",
                    "action": "RENAME",
                    "source": str(source_in_target),
                    "destination": str(dest_in_target),
                    "file_size": round(get_file_size_mb(video_file), 2)
                })
        
        # 处理字幕文件（使用与主视频相同的基础名）
        if folder_info['video_files'] and folder_info['subtitle_files']:
            # 使用第一个视频的基础名
            base_name = build_movie_filename(
                english_name=english_name,
                year=year,
                tech_info=extract_technical_info(folder_info['video_files'][0].stem),
                extension=""
            ).rstrip('.')
            
            for sub_file in folder_info['subtitle_files']:
                # 保留字幕的语言标识（如果有）
                sub_stem = sub_file.stem
                # 检查是否有语言标识（通常在最后，如.chs, .eng等）
                lang_suffix = ""
                if '.' in sub_stem:
                    parts = sub_stem.split('.')
                    # 常见语言标识
                    lang_codes = ['chs', 'cht', 'eng', 'jpn', 'kor', 'zh', 'en', 'ja', 'ko', 'zh-cn', 'zh-tw']
                    if parts[-1].lower() in lang_codes:
                        lang_suffix = f".{parts[-1]}"
                
                new_sub_name = f"{base_name}{lang_suffix}{sub_file.suffix}"
                
                relative_path = sub_file.relative_to(folder_path)
                source_in_target = target_folder / relative_path
                dest_in_target = target_folder / new_sub_name
                
                if source_in_target != dest_in_target:
                    operations.append({
                        "function": "func6",
                        "action": "RENAME",
                        "source": str(source_in_target),
                        "destination": str(dest_in_target),
                        "file_size": round(get_file_size_mb(sub_file), 2)
                    })
        
        # 处理图片文件（poster, fanart等保持关键词）
        for img_file in folder_info['image_files']:
            img_stem = img_file.stem.lower()
            
            # 检查是否包含特定关键词
            keywords = ['poster', 'fanart', 'banner', 'clearart', 'thumb', 
                       'landscape', 'logo', 'clearlogo', 'backdrop', 'cover', 'folder']
            keyword = None
            for kw in keywords:
                if kw in img_stem:
                    keyword = kw
                    break
            
            if keyword:
                new_img_name = f"{keyword}{img_file.suffix}"
            else:
                # 使用通用命名
                new_img_name = f"image{img_file.suffix}"
            
            relative_path = img_file.relative_to(folder_path)
            source_in_target = target_folder / relative_path
            dest_in_target = target_folder / new_img_name
            
            if source_in_target != dest_in_target:
                operations.append({
                    "function": "func6",
                    "action": "RENAME",
                    "source": str(source_in_target),
                    "destination": str(dest_in_target),
                    "file_size": round(get_file_size_mb(img_file), 2)
                })
        
        # 处理NFO文件（重命名为movie.nfo）
        for nfo_file in folder_info['nfo_files']:
            new_nfo_name = "movie.nfo"
            
            relative_path = nfo_file.relative_to(folder_path)
            source_in_target = target_folder / relative_path
            dest_in_target = target_folder / new_nfo_name
            
            if source_in_target != dest_in_target:
                operations.append({
                    "function": "func6",
                    "action": "RENAME",
                    "source": str(source_in_target),
                    "destination": str(dest_in_target),
                    "file_size": round(get_file_size_mb(nfo_file), 2)
                })
        
        return operations
        
    def generate_movie_organize_plan(self) -> List[Dict[str, str]]:
        """
        生成电影整理的完整操作计划
        
        Returns:
            操作计划列表
            
        @process:
            1. 扫描所有电影文件夹
            2. 对每个文件夹进行分析并生成操作计划
            3. 合并所有操作计划
            4. 返回完整列表
        """
        logger.info(f"开始扫描电影文件夹: {self.root_dir}")
        
        # 扫描所有电影文件夹（is_root=True表示从根目录开始）
        movie_folders = self._scan_movie_folders(self.root_dir, depth=0, is_root=True)
        
        if not movie_folders:
            logger.info("未找到需要整理的电影文件夹")
            return []
            
        logger.info(f"共发现 {len(movie_folders)} 个电影文件夹")
        
        # 生成操作计划
        all_operations = []
        success_count = 0
        fail_count = 0
        
        for idx, folder_info in enumerate(movie_folders, 1):
            try:
                logger.info(f"处理电影文件夹 [{idx}/{len(movie_folders)}]: {folder_info['name']}")
                operations = self._analyze_and_generate_plan(folder_info)
                all_operations.extend(operations)
                success_count += 1
            except Exception as e:
                logger.error(f"处理文件夹时出错 {folder_info['path']}: {str(e)}")
                fail_count += 1
                continue
                
        logger.info(f"处理完成：成功 {success_count} 个，失败 {fail_count} 个，共生成 {len(all_operations)} 个操作")
        return all_operations

