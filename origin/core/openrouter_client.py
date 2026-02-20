"""
OpenRouter API客户端：用于调用AI模型分析电影信息
"""
import json
import time
from typing import Dict, Optional, List
import requests
from core.logger import logger


class OpenRouterClient:
    """OpenRouter API客户端类"""
    
    def __init__(self, api_key: str, model: str, api_url: str):
        """
        初始化OpenRouter客户端
        
        Args:
            api_key: API密钥
            model: 使用的模型名称
            api_url: API端点URL
        """
        self.api_key = api_key
        self.model = model
        self.api_url = api_url
        self.max_retries = 3  # 最大重试次数
        self.retry_delay = 2  # 重试延迟（秒）
        
    def analyze_movie_info(self, 
                          folder_name: str, 
                          video_files: List[str], 
                          nfo_content: str = "") -> Optional[Dict[str, any]]:
        """
        分析电影信息，提取中英文名称和年份
        
        Args:
            folder_name: 文件夹名称
            video_files: 视频文件名列表
            nfo_content: NFO文件内容摘要
            
        Returns:
            包含电影信息的字典，格式为:
            {
                "chinese_name": "霍比特人",
                "english_name": "The.Hobbit.An.Unexpected.Journey",
                "year": "2012",
                "confidence": 0.95
            }
            如果失败返回None
            
        @process:
            1. 构建提示词，包含文件夹名、视频文件名和NFO内容
            2. 调用OpenRouter API进行分析
            3. 解析返回的JSON结果
            4. 失败时进行重试，达到最大重试次数后返回None
        """
        if not self.api_key:
            logger.warning("OpenRouter API密钥未配置，跳过AI分析")
            return None
            
        # 构建提示词
        from config import Config
        config = Config.load_config()
        
        prompt = config.MOVIE_NAME_EXTRACTION_PROMPT.format(
            folder_name=folder_name,
            video_files=", ".join(video_files),
            nfo_content=nfo_content if nfo_content else "无NFO文件"
        )
        
        # 构建请求
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,  # 使用较低的温度以获得更稳定的结果
            "response_format": {"type": "json_object"}  # 请求JSON格式响应
        }
        
        # 打印发送的prompt，便于调试
        logger.info(f"发送给AI的Prompt:\n{prompt}\n")
        
        # 尝试调用API，带重试机制
        for attempt in range(self.max_retries):
            try:
                logger.info(f"调用OpenRouter API分析电影信息（尝试 {attempt + 1}/{self.max_retries}）")
                
                response = requests.post(
                    self.api_url,
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                
                # 检查HTTP状态码
                if response.status_code == 200:
                    result = response.json()
                    
                    # 提取AI生成的内容
                    if "choices" in result and len(result["choices"]) > 0:
                        content = result["choices"][0]["message"]["content"]
                        
                        # 打印AI的原始响应，便于调试
                        logger.info(f"AI原始响应内容:\n{content}")
                        
                        try:
                            # 解析JSON内容
                            movie_info = json.loads(content)
                            
                            # 如果返回的是数组，取第一个元素
                            if isinstance(movie_info, list):
                                if len(movie_info) > 0:
                                    logger.info(f"AI返回了数组，取第一个元素")
                                    movie_info = movie_info[0]
                                else:
                                    logger.warning(f"AI返回了空数组")
                                    continue
                            
                            # 验证必需字段
                            required_fields = ["chinese_name", "english_name", "year"]
                            if all(field in movie_info for field in required_fields):
                                logger.info(f"成功分析电影信息: {movie_info}")
                                return movie_info
                            else:
                                logger.warning(f"返回的JSON缺少必需字段: {movie_info}")
                        except json.JSONDecodeError as e:
                            logger.error(f"解析AI响应JSON失败: {str(e)}, 原始内容: {content}")
                            
                elif response.status_code == 429:  # 速率限制
                    logger.warning(f"API速率限制，等待后重试...")
                    time.sleep(self.retry_delay * 2)
                    continue
                    
                else:
                    logger.error(f"API请求失败，状态码: {response.status_code}, 响应: {response.text}")
                    
            except requests.exceptions.Timeout:
                logger.warning(f"API请求超时（尝试 {attempt + 1}/{self.max_retries}）")
                
            except requests.exceptions.RequestException as e:
                logger.error(f"API请求异常: {str(e)}")
                
            except json.JSONDecodeError as e:
                logger.error(f"解析API响应JSON失败: {str(e)}")
                
            except Exception as e:
                logger.error(f"分析电影信息时发生未知错误: {str(e)}")
                
            # 等待后重试
            if attempt < self.max_retries - 1:
                time.sleep(self.retry_delay)
                
        logger.error(f"达到最大重试次数，放弃分析")
        return None
        
    def test_connection(self) -> bool:
        """
        测试API连接是否正常
        
        Returns:
            连接是否成功
            
        @process:
            1. 发送简单的测试请求
            2. 检查是否能正常返回结果
        """
        if not self.api_key:
            logger.error("API密钥未配置")
            return False
            
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": "Hello"
                    }
                ],
                "max_tokens": 10
            }
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("OpenRouter API连接测试成功")
                return True
            else:
                logger.error(f"API连接测试失败，状态码: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"API连接测试异常: {str(e)}")
            return False

