import requests
from bs4 import BeautifulSoup
import logging
import time
from typing import Dict, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)

class JavDBScraper:
    """JavDB网站爬虫类"""
    
    BASE_URL = "https://javdb.com"
    
    def __init__(self):
        """初始化爬虫"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
    def search_movie(self, query: str, debug: bool = True) -> Optional[Dict]:
        """
        搜索影片信息
        
        Args:
            query: 搜索关键词
            debug: 是否输出调试信息
            
        Returns:
            影片信息字典，如果未找到则返回None
        """
        try:
            # 构建搜索URL
            search_url = f"{self.BASE_URL}/search?q={query}&f=all"
            if debug:
                logger.info(f"搜索URL: {search_url}")
            
            # 发送请求
            response = self.session.get(search_url)
            response.raise_for_status()
            
            # 解析页面
            soup = BeautifulSoup(response.text, 'lxml')
            
            # 查找所有搜索结果
            movie_items = soup.select('.movie-list .item')
            if not movie_items:
                if debug:
                    logger.info("未找到任何搜索结果")
                return None
            
            if debug:
                logger.info(f"找到 {len(movie_items)} 个搜索结果")
                
            # 遍历并显示所有搜索结果
            results = []
            for idx, item in enumerate(movie_items, 1):
                title_elem = item.select_one('.video-title')
                number_elem = item.select_one('.video-number')
                date_elem = item.select_one('.meta')
                
                title = title_elem.text.strip() if title_elem else "未知标题"
                number = number_elem.text.strip() if number_elem else "未知番号"
                date = date_elem.text.strip() if date_elem else "未知日期"
                
                if debug:
                    logger.info(f"\n结果 {idx}:")
                    logger.info(f"标题: {title}")
                    logger.info(f"番号: {number}")
                    logger.info(f"日期: {date}")
                
                link = item.select_one('a')
                if link and link.get('href'):
                    if debug:
                        logger.info(f"详情页链接: {self.BASE_URL + link['href']}")
                    
                results.append({
                    'title': title,
                    'number': number,
                    'date': date,
                    'detail_url': self.BASE_URL + link['href'] if link and link.get('href') else None
                })
            
            if debug:
                logger.info("\n请选择要获取详细信息的结果编号（1-{len(results)}）")
            
            return results[0] if results else None
            
        except Exception as e:
            logger.error(f"搜索出错: {str(e)}")
            if debug:
                import traceback
                logger.error(traceback.format_exc())
            return None
            
    def get_movie_detail(self, detail_url: str, debug: bool = True) -> Optional[Dict]:
        """
        获取影片详细信息
        
        Args:
            detail_url: 详情页URL
            debug: 是否输出调试信息
            
        Returns:
            影片详细信息字典
        """
        try:
            if debug:
                logger.info(f"正在获取详情页: {detail_url}")
                
            time.sleep(1)  # 添加延迟，避免请求过快
            
            response = self.session.get(detail_url)
            response.raise_for_status()
            
            detail_soup = BeautifulSoup(response.text, 'lxml')
            
            # 提取影片信息
            info = {}
            
            # 获取标题 (从h2.title.is-4中获取)
            title_elem = detail_soup.select_one('h2.title.is-4 strong.current-title')
            if title_elem:
                info['title'] = title_elem.text.strip()
                if debug:
                    logger.info(f"标题: {info['title']}")
            
            # 获取番号 (从panel-block中获取)
            number_elem = detail_soup.select_one('.movie-panel-info .panel-block.first-block span.value')
            if number_elem:
                info['number'] = number_elem.text.strip()
                if debug:
                    logger.info(f"番号: {info['number']}")
            
            # 获取发行日期
            date_elem = detail_soup.select_one('.movie-panel-info .panel-block:has(strong:contains("日期")) span.value')
            if date_elem:
                info['release_date'] = date_elem.text.strip()
                if debug:
                    logger.info(f"发行日期: {info['release_date']}")
            
            # 获取时长
            duration_elem = detail_soup.select_one('.movie-panel-info .panel-block:has(strong:contains("時長")) span.value')
            if duration_elem:
                info['duration'] = duration_elem.text.strip()
                if debug:
                    logger.info(f"时长: {info['duration']}")
            
            # 获取导演
            director_elem = detail_soup.select_one('.movie-panel-info .panel-block:has(strong:contains("導演")) span.value')
            if director_elem:
                info['director'] = director_elem.text.strip()
                if debug:
                    logger.info(f"导演: {info['director']}")
            
            # 获取制作商
            maker_elem = detail_soup.select_one('.movie-panel-info .panel-block:has(strong:contains("片商")) span.value')
            if maker_elem:
                info['maker'] = maker_elem.text.strip()
                if debug:
                    logger.info(f"制作商: {info['maker']}")
            
            # 获取评分
            score_elem = detail_soup.select_one('.movie-panel-info .panel-block:has(strong:contains("評分")) span.value')
            if score_elem:
                info['score'] = score_elem.text.strip()
                if debug:
                    logger.info(f"评分: {info['score']}")
            
            # 获取类别标签
            tags_elem = detail_soup.select('.movie-panel-info .panel-block:has(strong:contains("類別")) span.value a')
            if tags_elem:
                info['tags'] = [tag.text.strip() for tag in tags_elem]
                if debug:
                    logger.info(f"标签: {info['tags']}")
            
            # 获取演员
            actors_elem = detail_soup.select('.movie-panel-info .panel-block:has(strong:contains("演員")) span.value a')
            if actors_elem:
                info['actors'] = [actor.text.strip() for actor in actors_elem]
                if debug:
                    logger.info(f"演员: {info['actors']}")
            
            # 获取观看统计
            stats_elem = detail_soup.select_one('.movie-panel-info .panel-block .is-size-7')
            if stats_elem:
                stats_text = stats_elem.text.strip()
                info['stats'] = stats_text
                if debug:
                    logger.info(f"观看统计: {stats_text}")
            
            # 获取封面图片URL
            cover = detail_soup.select_one('.video-cover img')
            if cover and cover.get('src'):
                info['cover_url'] = cover['src']
                if debug:
                    logger.info(f"封面URL: {info['cover_url']}")
            
            return info
            
        except Exception as e:
            logger.error(f"获取详情出错: {str(e)}")
            if debug:
                import traceback
                logger.error(traceback.format_exc())
            return None
            
    def download_cover(self, url: str, save_path: Path) -> bool:
        """
        下载封面图片
        
        Args:
            url: 图片URL
            save_path: 保存路径
            
        Returns:
            是否下载成功
        """
        try:
            response = self.session.get(url, stream=True)
            response.raise_for_status()
            
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            return True
            
        except Exception as e:
            logger.error(f"Error downloading cover: {str(e)}")
            return False 