#!/usr/bin/env python3
"""
电商商品价格采集与对比 - 命令行工具
"""
import argparse
import json
import os
import sys
from datetime import datetime

from core.scraper import MultiPlatformScraper, save_products, load_products
from core.cleaner import DataCleaner
from core.analyzer import ProductAnalyzer
from core.visualizer import Visualizer


def ensure_dirs():
    """确保数据目录存在"""
    for d in ["data/raw", "data/processed", "data/reports"]:
        os.makedirs(d, exist_ok=True)


def cmd_search(args):
    """搜索采集命令"""
    print(f"🔍 开始采集关键词: {args.keyword}")
    print(f"📦 平台: {', '.join(args.platforms)}")
    print(f"📊 每平台采集数量: {args.limit}")

    scraper = MultiPlatformScraper(platforms=args.platforms, delay=args.delay)
    products = scraper.search(args.keyword, limit_per_platform=args.limit)

    print(f"✅ 采集完成，共 {len(products)} 条原始数据")

    # 清洗数据
    cleaner = DataCleaner()
    cleaned = cleaner.clean(products)
    print(f"🧹 清洗后剩余 {len(cleaned)} 条有效数据")

    # 排序
    if args.sort == "price":
        cleaned = cleaner.sort_by_price(cleaned)
    elif args.sort == "sales":
        cleaned = cleaner.sort_by_sales(cleaned)
    elif args.sort == "rating":
        cleaned = cleaner.sort_by_rating(cleaned)

    # 保存原始数据
    raw_file = f"data/raw/{args.keyword}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    save_products(products, raw_file)
    print(f"💾 原始数据已保存: {raw_file}")

    # 保存清洗后数据
    processed_file = f"data/processed/{args.keyword}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    save_products(cleaned, processed_file)
    print(f"💾 清洗数据已保存: {processed_file}")

    # 生成报告
    analyzer = ProductAnalyzer()
    report = analyzer.generate_report(cleaned)

    # 打印摘要
    print("\n" + "="*60)
    print("📈 采集摘要")
    print("="*60)
    print(f"商品总数: {report['summary']['total_products']}")
    print(f"平均价格: ¥{report['summary']['avg_price']}")
    print(f"价格区间: {report['summary']['price_range']}")
    print(f"覆盖平台: {', '.join(report['summary']['platforms']).upper()}")

    print("\n🏆 性价比 TOP 5")
    print("-"*60)
    for i, item in enumerate(report['top_value'], 1):
        tags = ' '.join([f'[{t}]' for t in item['tags']])
        print(f"{i}. [{item['platform'].upper()}] ¥{item['price']} {item['name'][:40]} {tags}")

    print("\n💰 各平台最低价")
    print("-"*60)
    for platform, item in report['platform_cheapest'].items():
        print(f"[{platform.upper()}] ¥{item['price']} - {item['name'][:40]}")

    # 生成可视化报告
    if args.chart:
        visualizer = Visualizer()
        report_file = f"data/reports/{args.keyword}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        visualizer.save_html_report(cleaned, report_file, args.keyword)
        print(f"\n📊 可视化报告已生成: {report_file}")

    return cleaned


def cmd_report(args):
    """查看报告命令"""
    # 查找最新的处理数据文件
    processed_dir = "data/processed"
    if not os.path.exists(processed_dir):
        print("❌ 没有找到处理数据，请先运行 search 命令")
        return

    files = sorted([f for f in os.listdir(processed_dir) if f.endswith('.json')])
    if not files:
        print("❌ 没有找到处理数据，请先运行 search 命令")
        return

    # 使用最新的文件或指定文件
    if args.file:
        filepath = args.file
    else:
        filepath = os.path.join(processed_dir, files[-1])

    print(f"📂 加载数据: {filepath}")
    products = load_products(filepath)

    cleaner = DataCleaner()
    if args.sort == "price":
        products = cleaner.sort_by_price(products)
    elif args.sort == "sales":
        products = cleaner.sort_by_sales(products)
    elif args.sort == "rating":
        products = cleaner.sort_by_rating(products)

    analyzer = ProductAnalyzer()
    report = analyzer.generate_report(products)

    print("\n" + "="*80)
    print("📊 商品对比矩阵")
    print("="*80)
    print(f"{'排名':<4} {'平台':<6} {'价格':<10} {'性价比':<8} {'评分':<6} {'销量':<8} {'名称'}")
    print("-"*80)
    for i, item in enumerate(report['comparison_matrix'][:20], 1):
        tags = ','.join(item['tags'])
        print(f"{i:<4} {item['platform'].upper():<6} ¥{item['price']:<9} {item['value_score']:<8} {item['shop_rating']:<6} {item['sales']:<8} {item['name'][:30]} [{tags}]")

    if args.chart:
        visualizer = Visualizer()
        keyword = os.path.basename(filepath).split('_')[0]
        report_file = f"data/reports/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        visualizer.save_html_report(products, report_file, keyword)
        print(f"\n📊 可视化报告已生成: {report_file}")


def cmd_export(args):
    """导出数据命令"""
    processed_dir = "data/processed"
    if not os.path.exists(processed_dir):
        print("❌ 没有找到处理数据")
        return

    files = sorted([f for f in os.listdir(processed_dir) if f.endswith('.json')])
    if not files:
        print("❌ 没有找到处理数据")
        return

    filepath = os.path.join(processed_dir, files[-1])
    products = load_products(filepath)

    output = args.output or f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{args.format}"

    if args.format == "json":
        save_products(products, output)
    elif args.format == "csv":
        import csv
        with open(output, 'w', newline='', encoding='utf-8-sig') as f:
            if products:
                writer = csv.DictWriter(f, fieldvars=products[0].__dict__.keys())
                writer.writeheader()
                for p in products:
                    writer.writerow(p.__dict__)

    print(f"💾 数据已导出: {output}")


def main():
    parser = argparse.ArgumentParser(
        description="电商商品价格自动化采集与对比工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python cli.py search "iPhone 15" --platforms jd,tb,pdd --limit 20
  python cli.py search "蓝牙耳机" --sort price --chart
  python cli.py report --sort sales --chart
  python cli.py export --format csv --output result.csv
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # search 命令
    search_parser = subparsers.add_parser("search", help="按关键词搜索采集")
    search_parser.add_argument("keyword", help="搜索关键词")
    search_parser.add_argument("--platforms", nargs="?", default="jd,tb,pdd",
                              help="要采集的平台，逗号分隔 (默认: jd,tb,pdd)")
    search_parser.add_argument("--limit", type=int, default=10,
                              help="每平台采集数量 (默认: 10)")
    search_parser.add_argument("--sort", choices=["price", "sales", "rating"], default="price",
                              help="排序方式 (默认: price)")
    search_parser.add_argument("--chart", action="store_true",
                              help="生成可视化图表")
    search_parser.add_argument("--delay", type=float, default=0.1,
                              help="采集间隔延迟(秒) (默认: 0.1)")

    # report 命令
    report_parser = subparsers.add_parser("report", help="查看最近采集报告")
    report_parser.add_argument("--file", help="指定数据文件")
    report_parser.add_argument("--sort", choices=["price", "sales", "rating"], default="price",
                              help="排序方式 (默认: price)")
    report_parser.add_argument("--chart", action="store_true",
                              help="生成可视化图表")

    # export 命令
    export_parser = subparsers.add_parser("export", help="导出数据")
    export_parser.add_argument("--format", choices=["json", "csv"], default="json",
                              help="导出格式 (默认: json)")
    export_parser.add_argument("--output", help="输出文件路径")

    args = parser.parse_args()
    ensure_dirs()

    if args.command == "search":
        args.platforms = [p.strip() for p in args.platforms.split(",")]
        cmd_search(args)
    elif args.command == "report":
        cmd_report(args)
    elif args.command == "export":
        cmd_export(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
