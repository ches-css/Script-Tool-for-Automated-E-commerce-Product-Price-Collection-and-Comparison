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
    
    def generate_demo_data(self, keyword: str) -> List[Dict]:
        """生成演示数据，用于测试报告生成和上传功能"""
        demo_products = [
            {
                'platform': '京东',
                'title': f'{keyword} 旗舰版 4G全网通 GPS定位 视频通话',
                'price': 299.00,
                'url': 'https://item.jd.com/100012043978.html',
                'shop': '京东自营'
            },
            {
                'platform': '京东',
                'title': f'{keyword} 标准版 防水防摔 长续航',
                'price': 199.00,
                'url': 'https://item.jd.com/100023456789.html',
                'shop': '品牌旗舰店'
            },
            {
                'platform': '京东',
                'title': f'{keyword} 尊享版 高清双摄 AI语音助手',
                'price': 499.00,
                'url': 'https://item.jd.com/100034567890.html',
                'shop': '官方旗舰店'
            },
            {
                'platform': '淘宝',
                'title': f'{keyword} 基础款 2G通话 精准定位',
                'price': 159.00,
                'url': 'https://item.taobao.com/item.htm?id=12345678901',
                'shop': '天猫旗舰店'
            },
            {
                'platform': '淘宝',
                'title': f'{keyword} 运动版 心率监测 运动计步',
                'price': 259.00,
                'url': 'https://item.taobao.com/item.htm?id=12345678902',
                'shop': '品牌直销店'
            },
            {
                'platform': '拼多多',
                'title': f'{keyword} 经济版 基础通话 安全围栏',
                'price': 99.00,
                'url': 'https://mobile.yangkeduo.com/goods.html?goods_id=123456789',
                'shop': '百亿补贴店'
            },
            {
                'platform': '拼多多',
                'title': f'{keyword} 升级版 视频通话 学习助手',
                'price': 189.00,
                'url': 'https://mobile.yangkeduo.com/goods.html?goods_id=987654321',
                'shop': '品牌特卖店'
            }
        ]
        logger.info(f"生成演示数据: {len(demo_products)} 条")
        return demo_products
    
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
