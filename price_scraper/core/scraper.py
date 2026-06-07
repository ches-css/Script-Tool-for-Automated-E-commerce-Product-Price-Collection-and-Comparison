"""
电商商品数据采集器
支持多平台模拟采集（京东、淘宝、拼多多）
"""
import random
import time
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict


@dataclass
class Product:
    """商品数据模型"""
    id: str
    name: str
    price: float
    original_price: float
    sales: int
    shop_name: str
    shop_rating: float
    platform: str
    url: str
    keyword: str
    collected_at: str


class BaseScraper:
    """采集器基类"""

    PLATFORM_NAME = "base"
    BASE_URL = ""

    # 模拟商品池，用于生成逼真的模拟数据
    PRODUCT_TEMPLATES = {
        "手机": [
            ("{brand} {model} 5G智能手机", [2999, 4999, 6999, 8999]),
            ("{brand} {model} Pro 旗舰手机", [3999, 5999, 7999, 9999]),
            ("{brand} {model} 青春版", [1499, 1999, 2499]),
        ],
        "耳机": [
            ("{brand} 无线蓝牙耳机 {model}", [199, 399, 599, 899]),
            ("{brand} 降噪耳机 {model}", [499, 799, 1299]),
            ("{brand} 运动耳机 {model}", [149, 299, 499]),
        ],
        "电脑": [
            ("{brand} 轻薄笔记本 {model}", [3499, 4999, 6499]),
            ("{brand} 游戏本 {model}", [5499, 7999, 10999]),
            ("{brand} 平板电脑 {model}", [1999, 2999, 4499]),
        ],
        "默认": [
            ("{brand} {category} {model}", [99, 199, 299, 499, 999]),
            ("{brand} 新款 {category} {model}", [149, 299, 599, 1299]),
        ]
    }

    BRANDS = {
        "手机": ["Apple", "华为", "小米", "OPPO", "vivo", "荣耀", "三星", "一加"],
        "耳机": ["Sony", "Bose", "AirPods", "华为", "小米", "JBL", "Beats"],
        "电脑": ["联想", "戴尔", "惠普", "华硕", "MacBook", "华为", "小米"],
        "默认": ["品牌A", "品牌B", "品牌C", "品牌D", "品牌E"]
    }

    SHOP_NAMES = [
        "官方旗舰店", "品牌直营店", "数码专营店", "电子产品商城",
        "优选数码", "科技生活馆", "正品保障店", "旗舰体验店"
    ]

    def __init__(self, delay: float = 0.5):
        self.delay = delay
        self._random = random.Random()

    def _generate_id(self, keyword: str, index: int) -> str:
        """生成唯一商品ID"""
        content = f"{self.PLATFORM_NAME}_{keyword}_{index}_{datetime.now().isoformat()}"
        return hashlib.md5(content.encode()).hexdigest()[:12]

    def _detect_category(self, keyword: str) -> str:
        """根据关键词检测商品类别"""
        keyword_lower = keyword.lower()
        if any(x in keyword_lower for x in ["手机", "iphone", "华为", "小米", "oppo", "vivo"]):
            return "手机"
        elif any(x in keyword_lower for x in ["耳机", "airpods", "蓝牙", "降噪", "bose", "sony"]):
            return "耳机"
        elif any(x in keyword_lower for x in ["电脑", "笔记本", "平板", "macbook", "联想"]):
            return "电脑"
        return "默认"

    def _generate_product_name(self, keyword: str, index: int) -> tuple:
        """生成模拟商品名称和价格区间"""
        category = self._detect_category(keyword)
        templates = self.PRODUCT_TEMPLATES.get(category, self.PRODUCT_TEMPLATES["默认"])
        brands = self.BRANDS.get(category, self.BRANDS["默认"])

        template, price_range = self._random.choice(templates)
        brand = self._random.choice(brands)
        model = f"{self._random.choice(['X', 'Pro', 'Max', 'Ultra', 'Plus', 'SE'])}{self._random.randint(1, 20)}"

        # 将关键词融入名称
        if self._random.random() > 0.5:
            name = template.format(brand=brand, model=model, category=category)
            if keyword not in name:
                name = f"{keyword} {name}"
        else:
            name = f"{brand} {keyword} {model}"

        return name, price_range

    def search(self, keyword: str, limit: int = 10) -> List[Product]:
        """搜索商品（模拟实现）"""
        time.sleep(self.delay)
        products = []

        for i in range(limit):
            name, price_range = self._generate_product_name(keyword, i)
            base_price = self._random.choice(price_range)

            # 平台价格差异：京东偏高，淘宝中等，拼多多偏低
            platform_factor = {
                "jd": 1.05,
                "tb": 1.0,
                "pdd": 0.88
            }.get(self.PLATFORM_NAME, 1.0)

            price = round(base_price * platform_factor * self._random.uniform(0.9, 1.1), 2)
            original_price = round(price * self._random.uniform(1.1, 1.5), 2)

            # 销量：拼多多销量通常更高
            sales_factor = {
                "jd": 1,
                "tb": 1.5,
                "pdd": 3
            }.get(self.PLATFORM_NAME, 1)
            sales = int(self._random.randint(100, 10000) * sales_factor)

            # 店铺评分：京东通常更高
            rating_base = {
                "jd": 4.7,
                "tb": 4.5,
                "pdd": 4.3
            }.get(self.PLATFORM_NAME, 4.5)
            shop_rating = round(self._random.uniform(rating_base - 0.3, rating_base + 0.2), 1)

            shop_name = f"{name.split()[0]}{self._random.choice(self.SHOP_NAMES)}"

            product = Product(
                id=self._generate_id(keyword, i),
                name=name,
                price=price,
                original_price=original_price,
                sales=sales,
                shop_name=shop_name,
                shop_rating=shop_rating,
                platform=self.PLATFORM_NAME,
                url=f"{self.BASE_URL}/item/{self._generate_id(keyword, i)}",
                keyword=keyword,
                collected_at=datetime.now().isoformat()
            )
            products.append(product)

        return products


class JDScraper(BaseScraper):
    """京东采集器"""
    PLATFORM_NAME = "jd"
    BASE_URL = "https://item.jd.com"


class TaoBaoScraper(BaseScraper):
    """淘宝采集器"""
    PLATFORM_NAME = "tb"
    BASE_URL = "https://item.taobao.com"


class PDDScraper(BaseScraper):
    """拼多多采集器"""
    PLATFORM_NAME = "pdd"
    BASE_URL = "https://mobile.yangkeduo.com"


class MultiPlatformScraper:
    """多平台聚合采集器"""

    SCRAPERS = {
        "jd": JDScraper,
        "tb": TaoBaoScraper,
        "pdd": PDDScraper
    }

    def __init__(self, platforms: Optional[List[str]] = None, delay: float = 0.3):
        self.platforms = platforms or list(self.SCRAPERS.keys())
        self.scrapers = {
            name: cls(delay=delay)
            for name, cls in self.SCRAPERS.items()
            if name in self.platforms
        }

    def search(self, keyword: str, limit_per_platform: int = 10) -> List[Product]:
        """多平台搜索采集"""
        all_products = []
        for name, scraper in self.scrapers.items():
            try:
                products = scraper.search(keyword, limit_per_platform)
                all_products.extend(products)
            except Exception as e:
                print(f"[{name}] 采集失败: {e}")
        return all_products

    def search_all(self, keywords: List[str], limit_per_platform: int = 10) -> List[Product]:
        """批量关键词采集"""
        all_products = []
        for keyword in keywords:
            products = self.search(keyword, limit_per_platform)
            all_products.extend(products)
        return all_products


def save_products(products: List[Product], filepath: str):
    """保存商品数据到JSON文件"""
    data = [asdict(p) for p in products]
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_products(filepath: str) -> List[Product]:
    """从JSON文件加载商品数据"""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return [Product(**item) for item in data]
