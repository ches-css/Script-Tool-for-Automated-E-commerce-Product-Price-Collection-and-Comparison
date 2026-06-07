#!/usr/bin/env python3
import sys
import time
import logging
import schedule
from price_scraper import PriceScraper, ReportGenerator, FeishuUploader

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scraper.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def run_price_collection(keyword: str = "儿童智能手表"):
    """执行价格采集任务"""
    logger.info(f"开始价格采集任务，关键词: {keyword}")
    
    scraper = PriceScraper()
    products = scraper.collect_prices(keyword)
    
    if not products:
        logger.warning("未采集到任何商品数据")
        return
    
    logger.info(f"成功采集 {len(products)} 个商品")
    
    report_gen = ReportGenerator()
    markdown_path = report_gen.generate_markdown_report(products, keyword)
    excel_path = report_gen.generate_excel_report(products, keyword)
    
    feishu = FeishuUploader()
    feishu.upload_report_to_feishu(markdown_path, keyword)
    
    logger.info("价格采集任务完成")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='电商商品价格自动化采集与对比工具')
    parser.add_argument('--keyword', type=str, default='儿童智能手表', help='搜索关键词')
    parser.add_argument('--run-once', action='store_true', help='立即执行一次任务')
    parser.add_argument('--schedule', action='store_true', help='启动定时调度（每周日21:20）')
    
    args = parser.parse_args()
    
    if args.run_once:
        run_price_collection(args.keyword)
    elif args.schedule:
        logger.info("启动定时调度，每周日 21:20 执行价格采集")
        
        schedule.every().sunday.at("21:20").do(run_price_collection, keyword=args.keyword)
        
        logger.info("定时调度已启动，按 Ctrl+C 停止")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            logger.info("定时调度已停止")
    else:
        run_price_collection(args.keyword)


if __name__ == "__main__":
    main()
