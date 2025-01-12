"""
演员分类操作计划生成器
"""
import xml.etree.ElementTree as ET

from pathlib import Path
from typing import List, Dict
from core.logger import logger
from core.helpers import (
    get_file_size_mb, is_video_folder, parse_nfo_file, 
    get_first_nfo_file, format_folder_name, sanitize_folder_name
)
from core.classifier import ActorClassifier
from .base_planner import BasePlanner

class ActorPlanner(BasePlanner):
    """演员分类操作计划生成器"""
    
    def __init__(self, config):
        """
        初始化计划生成器
        
        Args:
            config: 配置对象
        """
        super().__init__(config)
        self.classifier = ActorClassifier()
        
    def _add_fc2_ppv_actors(self, nfo_path: Path) -> bool:
        """
        如果是FC2/PPV视频且没有演员，则添加相应的演员标签
        
        Args:
            nfo_path: NFO文件路径
            
        Returns:
            是否进行了修改
        """
        try:
            tree = ET.parse(nfo_path)
            root = tree.getroot()
            
            # 获取标题
            title_elem = root.find('title')
            if title_elem is None or not title_elem.text:
                return False
                
            title = title_elem.text.upper()
            
            # 检查是否有演员
            actors = root.findall('.//actor/name')
            if actors:
                return False
                
            # 检查是否包含FC2/PPV关键字
            is_fc2 = 'FC2' in title
            is_ppv = 'PPV' in title
            
            if not (is_fc2 or is_ppv):
                return False
                
            actors_to_add = ['FC2-PPV', 'FC2', 'PPV']
                
            # 获取或创建actors元素
            actors_elem = root.find('actors')
            if actors_elem is None:
                actors_elem = ET.SubElement(root, 'actors')
                
            # 添加演员
            for actor_name in actors_to_add:
                actor_elem = ET.SubElement(actors_elem, 'actor')
                name_elem = ET.SubElement(actor_elem, 'name')
                name_elem.text = actor_name
                
            # 保存修改
            tree.write(nfo_path, encoding='utf-8', xml_declaration=True)
            logger.info(f"已添加演员标签: {nfo_path}")
            return True
            
        except Exception as e:
            logger.error(f"修改NFO文件出错 {nfo_path}: {str(e)}")
            return False
            
    def _is_classified_folder(self, folder_path: Path) -> bool:
        """
        判断是否为已分类的文件夹（0/99/A-Z）
        
        Args:
            folder_path: 文件夹路径
            
        Returns:
            是否为已分类的文件夹
        """
        if not folder_path.is_dir():
            return False
            
        folder_name = folder_path.name
        
        # 检查是否为0或99分类
        if folder_name in {self.config.JAPANESE_ACTOR_CATEGORY, 
                         self.config.UNKNOWN_ACTOR_CATEGORY,self.config.BIG_VIDEO_DIR}:
            logger.info(f"已分类文件夹(数字): {folder_path}")
            return True
            
        # 检查是否为A-Z分类（只接受ASCII字母）
        if (len(folder_name) == 1 and 
            ord('A') <= ord(folder_name.upper()) <= ord('Z')):
            logger.info(f"已分类文件夹(字母): {folder_path}")
            return True
            
        return False
        
    def _scan_video_folders(self, start_path: Path) -> List[Dict[str, str]]:
        """
        扫描视频文件夹并生成分类计划
        
        Args:
            start_path: 起始路径
            
        Returns:
            操作计划列表
        """
        operations = []
        
        if not start_path.is_dir() or '.delete' in start_path.parts:
            return operations
            
        # 如果是已分类的文件夹，跳过
        if start_path != self.root_dir and self._is_classified_folder(start_path):
            return operations
            
        # 如果当前文件夹是视频文件夹
        if is_video_folder(start_path, self.config):
            # 获取第一个NFO文件
            nfo_file = get_first_nfo_file(start_path)
            if nfo_file:
                # 先尝试添加FC2/PPV演员标签
                self._add_fc2_ppv_actors(nfo_file)
                
                # 解析NFO文件
                actor_name, title, _ = parse_nfo_file(nfo_file)
                
                # 获取演员分类
                category = self.classifier.get_category(actor_name, self.config)
                
                if actor_name:
                    # 净化演员名称
                    actor_name = sanitize_folder_name(actor_name)
                    if actor_name and len(actor_name) > 0:
                        actor_first = actor_name[0]
                    else:
                        actor_first = "other"
                        
                    # 构造新的路径：分类/演员首字/演员名/标题
                    new_path = (self.root_dir / category / 
                              actor_first / actor_name / 
                              format_folder_name(title, self.config))
                else:
                    # 未知演员使用99分类
                    new_path = (self.root_dir / self.config.UNKNOWN_ACTOR_CATEGORY / 
                              format_folder_name(title, self.config))
                    
                operations.append({
                    "function": "func4",
                    "action": "MOVE",
                    "source": str(start_path),
                    "destination": str(new_path),
                    "file_size": round(sum(get_file_size_mb(f) for f in start_path.rglob('*') if f.is_file()), 2)
                })
        
        # 递归处理子文件夹
        for item in start_path.iterdir():
            if item.is_dir():
                operations.extend(self._scan_video_folders(item))
                
        return operations
        
    def generate_actor_classify_plan(self) -> List[Dict[str, str]]:
        """
        生成按演员分类的操作计划（功能4）
        
        Returns:
            操作计划列表
        """
        return self._scan_video_folders(self.root_dir) 