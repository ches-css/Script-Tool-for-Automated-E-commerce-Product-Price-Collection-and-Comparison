#!/usr/bin/env python3
"""
Web API 服务 - 提供HTTP接口和静态页面服务
"""
import json
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.scraper import MultiPlatformScraper, save_products
from core.cleaner import DataCleaner
from core.analyzer import ProductAnalyzer
from core.visualizer import Visualizer

# 确保数据目录存在
for d in ["data/raw", "data/processed", "data/reports"]:
    os.makedirs(d, exist_ok=True)


class APIHandler(BaseHTTPRequestHandler):
    """HTTP请求处理器"""

    def log_message(self, format, *args):
        # 简化日志输出
        print(f"[{self.log_date_time_string()}] {args[0]}")

    def _set_headers(self, content_type="application/json", status=200):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if path == "/":
            self.serve_file("web/index.html", "text/html")
        elif path == "/style.css":
            self.serve_file("web/style.css", "text/css")
        elif path == "/app.js":
            self.serve_file("web/app.js", "application/javascript")
        elif path == "/api/search":
            self.handle_search(query)
        elif path == "/api/demo":
            self.handle_demo()
        else:
            self._set_headers("application/json", 404)
            self.wfile.write(json.dumps({"error": "Not found"}, ensure_ascii=False).encode())

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8')

        try:
            data = json.loads(post_data) if post_data else {}
        except json.JSONDecodeError:
            data = parse_qs(post_data)
            data = {k: v[0] if len(v) == 1 else v for k, v in data.items()}

        if path == "/api/search":
            self.handle_search_post(data)
        else:
            self._set_headers("application/json", 404)
            self.wfile.write(json.dumps({"error": "Not found"}, ensure_ascii=False).encode())

    def serve_file(self, filepath, content_type):
        """提供静态文件"""
        full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filepath)
        if os.path.exists(full_path):
            self._set_headers(content_type, 200)
            with open(full_path, 'rb') as f:
                self.wfile.write(f.read())
        else:
            self._set_headers("text/plain", 404)
            self.wfile.write(b"File not found")

    def handle_search(self, query):
        """处理搜索请求 (GET)"""
        keyword = query.get("keyword", [""])[0]
        platforms = query.get("platforms", ["jd,tb,pdd"])[0].split(",")
        limit = int(query.get("limit", ["10"])[0])

        if not keyword:
            self._set_headers("application/json", 400)
            self.wfile.write(json.dumps({"error": "缺少关键词"}, ensure_ascii=False).encode())
            return

        result = self.run_scraper(keyword, platforms, limit)
        self._set_headers()
        self.wfile.write(json.dumps(result, ensure_ascii=False).encode())

    def handle_search_post(self, data):
        """处理搜索请求 (POST)"""
        keyword = data.get("keyword", "")
        platforms = data.get("platforms", "jd,tb,pdd").split(",")
        limit = int(data.get("limit", 10))

        if not keyword:
            self._set_headers("application/json", 400)
            self.wfile.write(json.dumps({"error": "缺少关键词"}, ensure_ascii=False).encode())
            return

        result = self.run_scraper(keyword, platforms, limit)
        self._set_headers()
        self.wfile.write(json.dumps(result, ensure_ascii=False).encode())

    def handle_demo(self):
        """返回演示数据"""
        result = self.run_scraper("蓝牙耳机", ["jd", "tb", "pdd"], 8)
        self._set_headers()
        self.wfile.write(json.dumps(result, ensure_ascii=False).encode())

    def run_scraper(self, keyword, platforms, limit):
        """运行采集流程"""
        try:
            scraper = MultiPlatformScraper(platforms=platforms, delay=0.05)
            products = scraper.search(keyword, limit_per_platform=limit)

            # 清洗
            cleaner = DataCleaner()
            cleaned = cleaner.clean(products)
            cleaned = cleaner.sort_by_price(cleaned)

            # 分析
            analyzer = ProductAnalyzer()
            report = analyzer.generate_report(cleaned)

            # 可视化数据
            visualizer = Visualizer()
            chart_data = visualizer.generate_chart_data(cleaned)

            return {
                "success": True,
                "keyword": keyword,
                "total_raw": len(products),
                "total_cleaned": len(cleaned),
                "report": report,
                "chart_data": chart_data,
                "products": [
                    {
                        "id": p.id,
                        "name": p.name,
                        "price": p.price,
                        "original_price": p.original_price,
                        "sales": p.sales,
                        "shop_name": p.shop_name,
                        "shop_rating": p.shop_rating,
                        "platform": p.platform,
                        "url": p.url
                    }
                    for p in cleaned
                ]
            }
        except Exception as e:
            import traceback
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }


def run_server(port=8080):
    """启动服务器"""
    server = HTTPServer(("", port), APIHandler)
    print(f"🚀 服务器启动成功!")
    print(f"📱 演示页面: http://localhost:{port}")
    print(f"🔌 API 端点: http://localhost:{port}/api/search")
    print(f"📊 演示数据: http://localhost:{port}/api/demo")
    print("按 Ctrl+C 停止服务器")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
        server.shutdown()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    run_server(port)
