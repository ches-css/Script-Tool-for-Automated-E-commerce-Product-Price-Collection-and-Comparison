"""
数据清洗与去重模块
"""
import re
from typing import List, Dict, Set
from dataclasses import asdict
from .scraper import Product


class DataCleaner:
    """数据清洗器"""

    def __init__(self):
        self.seen_names: Set[str] = set()

    def clean_price(self, price) -> float:
        """清洗价格，统一为浮点数"""
        if isinstance(price, (int, float)):
            return float(price)
        if isinstance(price, str):
            # 去除货币符号和逗号
            cleaned = re.sub(r'[^\d.]', '', price)
            try:
                return float(cleaned) if cleaned else 0.0
            except ValueError:
                return 0.0
        return 0.0

    def clean_sales(self, sales) -> int:
        """清洗销量，统一为整数"""
        if isinstance(sales, int):
            return sales
        if isinstance(sales, str):
            sales = sales.strip()
            # 处理 "1万+", "5000+" 等格式
            if '万' in sales:
                num = re.sub(r'[^\d.]', '', sales)
                try:
                    return int(float(num) * 10000)
                except ValueError:
                    return 0
            elif '千' in sales:
                num = re.sub(r'[^\d.]', '', sales)
                try:
                    return int(float(num) * 1000)
                except ValueError:
                    return 0
            else:
                cleaned = re.sub(r'[^\d]', '', sales)
                try:
                    return int(cleaned) if cleaned else 0
                except ValueError:
                    return 0
        return 0

    def clean_rating(self, rating) -> float:
        """清洗评分，统一为0-5的浮点数"""
        if isinstance(rating, (int, float)):
            return min(5.0, max(0.0, float(rating)))
        if isinstance(rating, str):
            cleaned = re.sub(r'[^\d.]', '', rating)
            try:
                return min(5.0, max(0.0, float(cleaned)))
            except ValueError:
                return 0.0
        return 0.0

    def normalize_name(self, name: str) -> str:
        """标准化商品名称用于去重比较"""
        # 去除多余空格，转小写
        normalized = re.sub(r'\s+', ' ', name.strip().lower())
        # 去除常见的无意义词汇
        stop_words = ['【', '】', '()', '（）', '正品', '包邮', '现货']
        for word in stop_words:
            normalized = normalized.replace(word, '')
        return normalized

    def is_duplicate(self, product: Product) -> bool:
        """检查是否重复商品"""
        normalized = self.normalize_name(product.name)
        # 使用名称+平台的组合作为去重键
        dup_key = f"{normalized}_{product.platform}"
        if dup_key in self.seen_names:
            return True
        self.seen_names.add(dup_key)
        return False

    def clean(self, products: List[Product]) -> List[Product]:
        """
        执行完整的数据清洗流程
        1. 字段标准化
        2. 去重
        3. 缺失值处理
        4. 异常值过滤
        """
        cleaned_products = []
        self.seen_names.clear()

        for product in products:
            # 字段清洗
            product.price = self.clean_price(product.price)
            product.original_price = self.clean_price(product.original_price)
            product.sales = self.clean_sales(product.sales)
            product.shop_rating = self.clean_rating(product.shop_rating)

            # 异常值过滤：价格为0或负数的商品
            if product.price <= 0:
                continue

            # 去重
            if self.is_duplicate(product):
                continue

            cleaned_products.append(product)

        return cleaned_products

    def sort_by_price(self, products: List[Product], ascending: bool = True) -> List[Product]:
        """按价格排序"""
        return sorted(products, key=lambda p: p.price, reverse=not ascending)

    def sort_by_sales(self, products: List[Product], ascending: bool = False) -> List[Product]:
        """按销量排序"""
        return sorted(products, key=lambda p: p.sales, reverse=not ascending)

    def sort_by_rating(self, products: List[Product], ascending: bool = False) -> List[Product]:
        """按评分排序"""
        return sorted(products, key=lambda p: p.shop_rating, reverse=not ascending)

    def get_statistics(self, products: List[Product]) -> Dict:
        """获取数据统计信息"""
        if not products:
            return {}

        prices = [p.price for p in products]
        sales = [p.sales for p in products]
        ratings = [p.shop_rating for p in products]

        platforms = {}
        for p in products:
            platforms[p.platform] = platforms.get(p.platform, 0) + 1

        return {
            "total_count": len(products),
            "avg_price": round(sum(prices) / len(prices), 2),
            "min_price": min(prices),
            "max_price": max(prices),
            "avg_sales": int(sum(sales) / len(sales)),
            "avg_rating": round(sum(ratings) / len(ratings), 2),
            "platform_distribution": platforms
        }
