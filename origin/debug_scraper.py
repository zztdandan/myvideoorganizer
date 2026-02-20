from core.scraper import JavDBScraper
import logging
import json

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_movie(scraper: JavDBScraper, query: str):
    """调试单个番号"""
    logger.info(f"\n{'='*50}")
    logger.info(f"开始调试番号: {query}")
    logger.info(f"{'='*50}")
    
    # 搜索影片
    results = scraper.search_movie(query)
    if not results:
        logger.error(f"未找到影片: {query}")
        return
        
    # 获取详情页信息
    if results.get('detail_url'):
        info = scraper.get_movie_detail(results['detail_url'])
        if info:
            logger.info("\n获取到的详细信息:")
            print(json.dumps(info, ensure_ascii=False, indent=2))
        else:
            logger.error("获取详情失败")
    else:
        logger.error("未找到详情页链接")

def main():
    # 初始化爬虫
    scraper = JavDBScraper()
    
    # 要调试的番号列表
    queries = [
        "CAWD-764",
        "WAAA-428",
        "WAAA-461"
    ]
    
    # 依次调试每个番号
    for query in queries:
        debug_movie(scraper, query)

if __name__ == '__main__':
    main() 