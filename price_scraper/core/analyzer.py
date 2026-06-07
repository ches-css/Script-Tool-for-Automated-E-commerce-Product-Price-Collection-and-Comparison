"""
商品分析与推荐模块
"""
import math
from typing import List, Dict, Tuple
from .scraper import Product


class ProductAnalyzer:
    """商品分析器"""

    def __init__(self):
        pass

    def calculate_value_score(self, product: Product) -> float:
        """
        计算性价比得分
        综合考虑：价格（越低越好）、销量（越高越好）、评分（越高越好）
        返回 0-100 的得分
        """
        # 价格得分：假设合理价格区间，价格越低得分越高
        # 使用对数压缩避免极端值影响
        price_score = max(0, 100 - math.log10(max(product.price, 1)) * 15)

        # 销量得分：使用对数尺度
        sales_score = min(100, math.log10(max(product.sales, 1)) * 12)

        # 评分得分
        rating_score = (product.shop_rating / 5.0) * 100

        # 综合得分权重：价格40%，销量30%，评分30%
        value_score = price_score * 0.4 + sales_score * 0.3 + rating_score * 0.3

        return round(value_score, 2)

    def analyze_products(self, products: List[Product]) -> List[Dict]:
        """分析所有商品并添加性价比标签"""
        analyzed = []

        for product in products:
            value_score = self.calculate_value_score(product)

            # 推荐标签
            tags = []
            if value_score >= 80:
                tags.append("高性价比")
            if product.sales > 5000:
                tags.append("热销")
            if product.shop_rating >= 4.8:
                tags.append("高评分")
            if product.price < getattr(product, 'original_price', product.price) * 0.8:
                tags.append("大优惠")

            analyzed.append({
                "product": product,
                "value_score": value_score,
                "tags": tags,
                "discount_rate": round(product.price / max(product.original_price, 1), 2)
            })

        # 按性价比得分排序
        analyzed.sort(key=lambda x: x["value_score"], reverse=True)
        return analyzed

    def get_best_value(self, products: List[Product], top_n: int = 5) -> List[Dict]:
        """获取性价比最高的商品"""
        analyzed = self.analyze_products(products)
        return analyzed[:top_n]

    def get_cheapest(self, products: List[Product], top_n: int = 5) -> List[Product]:
        """获取价格最低的商品"""
        sorted_products = sorted(products, key=lambda p: p.price)
        return sorted_products[:top_n]

    def get_platform_comparison(self, products: List[Product]) -> Dict:
        """平台横向对比分析"""
        platform_stats = {}

        for p in products:
            if p.platform not in platform_stats:
                platform_stats[p.platform] = {
                    "count": 0,
                    "total_price": 0,
                    "total_sales": 0,
                    "total_rating": 0,
                    "products": []
                }

            stats = platform_stats[p.platform]
            stats["count"] += 1
            stats["total_price"] += p.price
            stats["total_sales"] += p.sales
            stats["total_rating"] += p.shop_rating
            stats["products"].append(p)

        # 计算平均值
        for platform, stats in platform_stats.items():
            count = stats["count"]
            stats["avg_price"] = round(stats["total_price"] / count, 2)
            stats["avg_sales"] = int(stats["total_sales"] / count)
            stats["avg_rating"] = round(stats["total_rating"] / count, 2)
            stats["min_price"] = min(p.price for p in stats["products"])
            stats["max_price"] = max(p.price for p in stats["products"])

        return platform_stats

    def get_price_trend(self, products: List[Product]) -> Dict:
        """
        生成价格分布数据用于趋势图表
        """
        if not products:
            return {}

        prices = [p.price for p in products]
        min_price = min(prices)
        max_price = max(prices)

        # 创建价格区间
        if max_price == min_price:
            bins = [min_price - 1, min_price + 1]
        else:
            bin_count = min(10, len(products))
            bin_width = (max_price - min_price) / bin_count
            bins = [min_price + i * bin_width for i in range(bin_count + 1)]

        # 统计每个区间的商品数量
        distribution = []
        for i in range(len(bins) - 1):
            count = sum(1 for p in prices if bins[i] <= p < bins[i + 1])
            distribution.append({
                "range": f"{round(bins[i], 0)}-{round(bins[i+1], 0)}",
                "count": count,
                "min": round(bins[i], 2),
                "max": round(bins[i+1], 2)
            })

        # 最后一个区间包含最大值
        if distribution:
            distribution[-1]["count"] += sum(1 for p in prices if p >= bins[-1])
            distribution[-1]["max"] = max_price

        return {
            "min_price": min_price,
            "max_price": max_price,
            "avg_price": round(sum(prices) / len(prices), 2),
            "distribution": distribution
        }

    def generate_comparison_matrix(self, products: List[Product]) -> List[Dict]:
        """生成商品横向对比矩阵"""
        if not products:
            return []

        analyzed = self.analyze_products(products)

        matrix = []
        for item in analyzed:
            p = item["product"]
            matrix.append({
                "name": p.name,
                "platform": p.platform,
                "price": p.price,
                "original_price": p.original_price,
                "sales": p.sales,
                "shop_rating": p.shop_rating,
                "shop_name": p.shop_name,
                "value_score": item["value_score"],
                "tags": item["tags"],
                "discount": f"{round((1 - item['discount_rate']) * 100, 1)}%",
                "url": p.url
            })

        return matrix

    def generate_report(self, products: List[Product]) -> Dict:
        """生成完整的分析报告"""
        if not products:
            return {"error": "没有商品数据"}

        analyzed = self.analyze_products(products)
        platform_comparison = self.get_platform_comparison(products)
        price_trend = self.get_price_trend(products)
        comparison_matrix = self.generate_comparison_matrix(products)

        # 找出各平台最低价
        platform_cheapest = {}
        for platform, stats in platform_comparison.items():
            cheapest = min(stats["products"], key=lambda p: p.price)
            platform_cheapest[platform] = {
                "name": cheapest.name,
                "price": cheapest.price,
                "url": cheapest.url
            }

        # 清理 platform_comparison 中的 Product 对象，使其可 JSON 序列化
        clean_platform_comparison = {}
        for platform, stats in platform_comparison.items():
            clean_platform_comparison[platform] = {
                "count": stats["count"],
                "avg_price": stats["avg_price"],
                "avg_sales": stats["avg_sales"],
                "avg_rating": stats["avg_rating"],
                "min_price": stats["min_price"],
                "max_price": stats["max_price"]
            }

        return {
            "summary": {
                "total_products": len(products),
                "platforms": list(platform_comparison.keys()),
                "avg_price": price_trend["avg_price"],
                "price_range": f"{price_trend['min_price']} - {price_trend['max_price']}"
            },
            "top_value": [
                {
                    "name": item["product"].name,
                    "platform": item["product"].platform,
                    "price": item["product"].price,
                    "value_score": item["value_score"],
                    "tags": item["tags"]
                }
                for item in analyzed[:5]
            ],
            "platform_comparison": clean_platform_comparison,
            "price_trend": price_trend,
            "platform_cheapest": platform_cheapest,
            "comparison_matrix": comparison_matrix
        }
