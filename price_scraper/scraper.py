#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import time
import random
import json
from typing import List, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PriceScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    
    def search_jd(self, keyword: str, max_items: int = 10) -> List[Dict]:
        """搜索京东商品"""
        products = []
        try:
            url = f"https://search.jd.com/Search?keyword={keyword}&enc=utf-8"
            response = requests.get(url, headers=self.headers, timeout=30)
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'lxml')
            items = soup.select('.gl-item')
            
            for idx, item in enumerate(items[:max_items]):
                try:
                    title_elem = item.select_one('.p-name em')
                    price_elem = item.select_one('.p-price i')
                    link_elem = item.select_one('.p-name a')
                    shop_elem = item.select_one('.p-shop a')
                    
                    if title_elem and price_elem:
                        product = {
                            'platform': '京东',
                            'title': title_elem.text.strip(),
                            'price': float(price_elem.text) if price_elem.text else 0.0,
                            'url': f"https:{link_elem.get('href', '')}" if link_elem else '',
                            'shop': shop_elem.text.strip() if shop_elem else '未知店铺'
                        }
                        products.append(product)
                        logger.info(f"京东: {product['title'][:30]}... - {product['price']}元")
                except Exception as e:
                    logger.warning(f"解析京东商品失败: {e}")
                    continue
                    
            time.sleep(random.uniform(1, 3))
        except Exception as e:
            logger.error(f"京东搜索失败: {e}")
        
        return products
    
    def search_taobao(self, keyword: str, max_items: int = 10) -> List[Dict]:
        """模拟淘宝商品搜索（示例函数）"""
        products = []
        logger.info("淘宝搜索功能需要登录，暂不可用")
        return products
    
    def search_pdd(self, keyword: str, max_items: int = 10) -> List[Dict]:
        """模拟拼多多商品搜索（示例函数）"""
        products = []
        logger.info("拼多多搜索功能需要特殊处理，暂不可用")
        return products
    
    def collect_prices(self, keyword: str, platforms: List[str] = None) -> List[Dict]:
        """采集多个平台的价格"""
        if platforms is None:
            platforms = ['jd']
        
        all_products = []
        
        if 'jd' in platforms:
            logger.info(f"开始采集京东: {keyword}")
            jd_products = self.search_jd(keyword)
            all_products.extend(jd_products)
        
        if 'taobao' in platforms:
            all_products.extend(self.search_taobao(keyword))
        
        if 'pdd' in platforms:
            all_products.extend(self.search_pdd(keyword))
        
        return all_products
