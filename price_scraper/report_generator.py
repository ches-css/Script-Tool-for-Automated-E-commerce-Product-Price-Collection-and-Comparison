#!/usr/bin/env python3
import pandas as pd
from datetime import datetime
from typing import List, Dict
import os
import logging

logger = logging.getLogger(__name__)


class ReportGenerator:
    def __init__(self, output_dir: str = "reports"):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    def generate_excel_report(self, products: List[Dict], keyword: str) -> str:
        """生成Excel报告"""
        if not products:
            logger.warning("没有商品数据，无法生成报告")
            return ""
        
        df = pd.DataFrame(products)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"价格报告_{keyword}_{timestamp}.xlsx"
        filepath = os.path.join(self.output_dir, filename)
        
        df = df.sort_values('price', ascending=True)
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='价格对比', index=False)
            
            workbook = writer.book
            worksheet = writer.sheets['价格对比']
            
            for idx, col in enumerate(df.columns):
                max_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
                worksheet.column_dimensions[chr(65 + idx)].width = max_len
        
        logger.info(f"Excel报告已生成: {filepath}")
        return filepath
    
    def generate_markdown_report(self, products: List[Dict], keyword: str) -> str:
        """生成Markdown报告"""
        if not products:
            logger.warning("没有商品数据，无法生成报告")
            return ""
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        markdown = f"# {keyword} 价格采集报告\n\n"
        markdown += f"**生成时间**: {timestamp}\n\n"
        markdown += f"**采集商品数**: {len(products)}\n\n"
        
        if products:
            avg_price = sum(p['price'] for p in products) / len(products)
            min_price_item = min(products, key=lambda x: x['price'])
            max_price_item = max(products, key=lambda x: x['price'])
            
            markdown += "## 价格统计\n\n"
            markdown += f"- 平均价格: ¥{avg_price:.2f}\n"
            markdown += f"- 最低价格: ¥{min_price_item['price']:.2f} ({min_price_item['title'][:30]}...)\n"
            markdown += f"- 最高价格: ¥{max_price_item['price']:.2f} ({max_price_item['title'][:30]}...)\n\n"
        
        markdown += "## 商品列表\n\n"
        markdown += "| 平台 | 商品标题 | 价格 | 店铺 | 链接 |\n"
        markdown += "|------|----------|------|------|------|\n"
        
        for product in products:
            title = product['title'].replace('|', ' ').replace('\n', ' ')
            markdown += f"| {product['platform']} | {title[:50]} | ¥{product['price']:.2f} | {product['shop']} | [链接]({product['url']}) |\n"
        
        timestamp_file = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"价格报告_{keyword}_{timestamp_file}.md"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(markdown)
        
        logger.info(f"Markdown报告已生成: {filepath}")
        return filepath
