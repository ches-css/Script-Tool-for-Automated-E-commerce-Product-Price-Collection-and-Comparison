"""
数据可视化模块
生成价格趋势图表、平台对比图表等
"""
import json
import base64
from typing import List, Dict
from .scraper import Product
from .analyzer import ProductAnalyzer


class Visualizer:
    """可视化生成器"""

    def __init__(self):
        self.analyzer = ProductAnalyzer()

    def generate_chart_data(self, products: List[Product]) -> Dict:
        """生成前端图表所需的JSON数据"""
        if not products:
            return {}

        report = self.analyzer.generate_report(products)

        # 1. 价格分布数据（柱状图）
        price_distribution = report.get("price_trend", {}).get("distribution", [])

        # 2. 平台对比数据（雷达图/柱状图）
        platform_comparison = report.get("platform_comparison", {})
        platform_chart_data = []
        for platform, stats in platform_comparison.items():
            platform_chart_data.append({
                "platform": platform.upper(),
                "avg_price": stats.get("avg_price", 0),
                "avg_sales": stats.get("avg_sales", 0),
                "avg_rating": stats.get("avg_rating", 0),
                "count": stats.get("count", 0)
            })

        # 3. 性价比散点图数据
        analyzed = self.analyzer.analyze_products(products)
        scatter_data = []
        for item in analyzed:
            p = item["product"]
            scatter_data.append({
                "name": p.name[:30] + "..." if len(p.name) > 30 else p.name,
                "price": p.price,
                "value_score": item["value_score"],
                "sales": p.sales,
                "platform": p.platform,
                "rating": p.shop_rating
            })

        # 4. 价格排序数据（横向条形图）
        sorted_by_price = sorted(products, key=lambda p: p.price)
        price_rank_data = []
        for p in sorted_by_price[:15]:  # 取前15个
            price_rank_data.append({
                "name": p.name[:25] + "..." if len(p.name) > 25 else p.name,
                "price": p.price,
                "platform": p.platform
            })

        return {
            "summary": report.get("summary", {}),
            "price_distribution": price_distribution,
            "platform_comparison": platform_chart_data,
            "scatter_data": scatter_data,
            "price_rank": price_rank_data,
            "top_value": report.get("top_value", []),
            "platform_cheapest": report.get("platform_cheapest", {}),
            "comparison_matrix": report.get("comparison_matrix", [])
        }

    def generate_html_report(self, products: List[Product], keyword: str = "") -> str:
        """生成包含图表的HTML报告"""
        chart_data = self.generate_chart_data(products)

        html_template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>商品价格采集报告 - {keyword}</title>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #e0e0e0;
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        .header {{
            text-align: center;
            padding: 40px 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 16px;
            margin-bottom: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
        }}
        .header h1 {{ font-size: 2.5em; margin-bottom: 10px; color: #fff; }}
        .header p {{ font-size: 1.1em; opacity: 0.9; }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: rgba(255,255,255,0.05);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            padding: 24px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.1);
            transition: transform 0.3s;
        }}
        .stat-card:hover {{ transform: translateY(-5px); }}
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
            margin: 10px 0;
        }}
        .stat-label {{ font-size: 0.9em; opacity: 0.7; }}
        .chart-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .chart-container {{
            background: rgba(255,255,255,0.05);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .chart-title {{
            font-size: 1.2em;
            margin-bottom: 15px;
            color: #fff;
            border-left: 4px solid #667eea;
            padding-left: 12px;
        }}
        .chart {{ width: 100%; height: 350px; }}
        .table-container {{
            background: rgba(255,255,255,0.05);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid rgba(255,255,255,0.1);
            overflow-x: auto;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}
        th {{
            background: rgba(102, 126, 234, 0.2);
            font-weight: 600;
            color: #667eea;
        }}
        tr:hover {{ background: rgba(255,255,255,0.03); }}
        .tag {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            margin-right: 4px;
        }}
        .tag-value {{ background: #4caf50; color: white; }}
        .tag-hot {{ background: #ff5722; color: white; }}
        .tag-rating {{ background: #2196f3; color: white; }}
        .tag-discount {{ background: #ff9800; color: white; }}
        .platform-jd {{ color: #e4393c; }}
        .platform-tb {{ color: #ff5000; }}
        .platform-pdd {{ color: #e02e24; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>商品价格采集分析报告</h1>
            <p>关键词：{keyword} | 采集时间：{chart_data.get('summary', {}).get('collected_at', '刚刚')}</p>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">商品总数</div>
                <div class="stat-value">{chart_data.get('summary', {}).get('total_products', 0)}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">平均价格</div>
                <div class="stat-value">¥{chart_data.get('summary', {}).get('avg_price', 0)}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">价格区间</div>
                <div class="stat-value">{chart_data.get('summary', {}).get('price_range', 'N/A')}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">覆盖平台</div>
                <div class="stat-value">{', '.join(chart_data.get('summary', {}).get('platforms', [])).upper()}</div>
            </div>
        </div>

        <div class="chart-grid">
            <div class="chart-container">
                <div class="chart-title">价格分布</div>
                <div id="priceDistChart" class="chart"></div>
            </div>
            <div class="chart-container">
                <div class="chart-title">平台对比</div>
                <div id="platformChart" class="chart"></div>
            </div>
            <div class="chart-container">
                <div class="chart-title">性价比分析</div>
                <div id="scatterChart" class="chart"></div>
            </div>
            <div class="chart-container">
                <div class="chart-title">价格排行（低到高）</div>
                <div id="rankChart" class="chart"></div>
            </div>
        </div>

        <div class="table-container">
            <div class="chart-title">商品对比矩阵</div>
            <table>
                <thead>
                    <tr>
                        <th>排名</th>
                        <th>商品名称</th>
                        <th>平台</th>
                        <th>价格</th>
                        <th>原价</th>
                        <th>销量</th>
                        <th>评分</th>
                        <th>性价比</th>
                        <th>标签</th>
                    </tr>
                </thead>
                <tbody id="productTable"></tbody>
            </table>
        </div>
    </div>

    <script>
        const chartData = {json.dumps(chart_data, ensure_ascii=False, indent=2)};

        // 价格分布图
        const priceDistChart = echarts.init(document.getElementById('priceDistChart'));
        priceDistChart.setOption({{
            tooltip: {{ trigger: 'axis' }},
            xAxis: {{
                type: 'category',
                data: chartData.price_distribution.map(d => d.range),
                axisLabel: {{ color: '#999', rotate: 30 }}
            }},
            yAxis: {{
                type: 'value',
                axisLabel: {{ color: '#999' }}
            }},
            series: [{{
                data: chartData.price_distribution.map(d => d.count),
                type: 'bar',
                itemStyle: {{
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        {{ offset: 0, color: '#667eea' }},
                        {{ offset: 1, color: '#764ba2' }}
                    ])
                }}
            }}]
        }});

        // 平台对比图
        const platformChart = echarts.init(document.getElementById('platformChart'));
        platformChart.setOption({{
            tooltip: {{ trigger: 'axis' }},
            legend: {{ data: ['平均价格', '平均销量/100', '平均评分*10'], textStyle: {{ color: '#999' }} }},
            radar: {{
                indicator: chartData.platform_comparison.map(p => ({{
                    name: p.platform,
                    max: Math.max(...chartData.platform_comparison.map(x => x.avg_price)) * 1.2
                }}))
            }},
            series: [{{
                type: 'radar',
                data: [
                    {{
                        value: chartData.platform_comparison.map(p => p.avg_price),
                        name: '平均价格',
                        areaStyle: {{ opacity: 0.3 }}
                    }}
                ]
            }}]
        }});

        // 性价比散点图
        const scatterChart = echarts.init(document.getElementById('scatterChart'));
        scatterChart.setOption({{
            tooltip: {{
                formatter: function(params) {{
                    return params.data[3] + '<br/>价格: ¥' + params.data[0] + '<br/>性价比: ' + params.data[1];
                }}
            }},
            xAxis: {{
                type: 'value',
                name: '价格',
                axisLabel: {{ color: '#999' }},
                nameTextStyle: {{ color: '#999' }}
            }},
            yAxis: {{
                type: 'value',
                name: '性价比得分',
                axisLabel: {{ color: '#999' }},
                nameTextStyle: {{ color: '#999' }}
            }},
            series: [{{
                type: 'scatter',
                data: chartData.scatter_data.map(d => [d.price, d.value_score, d.sales, d.name]),
                symbolSize: function(data) {{ return Math.sqrt(data[2]) / 5; }},
                itemStyle: {{
                    color: new echarts.graphic.RadialGradient(0.4, 0.3, 1, [
                        {{ offset: 0, color: '#667eea' }},
                        {{ offset: 1, color: '#764ba2' }}
                    ])
                }}
            }}]
        }});

        // 价格排行图
        const rankChart = echarts.init(document.getElementById('rankChart'));
        rankChart.setOption({{
            tooltip: {{ trigger: 'axis' }},
            xAxis: {{
                type: 'value',
                axisLabel: {{ color: '#999' }}
            }},
            yAxis: {{
                type: 'category',
                data: chartData.price_rank.map(d => d.name).reverse(),
                axisLabel: {{ color: '#999', fontSize: 10 }}
            }},
            series: [{{
                type: 'bar',
                data: chartData.price_rank.map(d => d.price).reverse(),
                itemStyle: {{
                    color: function(params) {{
                        const colors = ['#4caf50', '#8bc34a', '#cddc39', '#ffeb3b', '#ffc107'];
                        return colors[Math.min(params.dataIndex, colors.length - 1)];
                    }}
                }}
            }}]
        }});

        // 填充表格
        const tbody = document.getElementById('productTable');
        chartData.comparison_matrix.forEach((item, index) => {{
            const row = document.createElement('tr');
            const platformClass = 'platform-' + item.platform;
            const tagsHtml = item.tags.map(tag => {{
                const tagClass = tag === '高性价比' ? 'tag-value' :
                                tag === '热销' ? 'tag-hot' :
                                tag === '高评分' ? 'tag-rating' : 'tag-discount';
                return `<span class="tag ${{tagClass}}">${{tag}}</span>`;
            }}).join('');

            row.innerHTML = `
                <td>${{index + 1}}</td>
                <td>${{item.name}}</td>
                <td class="${{platformClass}}">${{item.platform.toUpperCase()}}</td>
                <td>¥${{item.price}}</td>
                <td style="text-decoration: line-through; opacity: 0.6;">¥${{item.original_price}}</td>
                <td>${{item.sales}}</td>
                <td>${{item.shop_rating}}</td>
                <td>${{item.value_score}}</td>
                <td>${{tagsHtml}}</td>
            `;
            tbody.appendChild(row);
        }});

        window.addEventListener('resize', () => {{
            priceDistChart.resize();
            platformChart.resize();
            scatterChart.resize();
            rankChart.resize();
        }});
    </script>
</body>
</html>"""

        return html_template

    def save_html_report(self, products: List[Product], filepath: str, keyword: str = ""):
        """保存HTML报告到文件"""
        html = self.generate_html_report(products, keyword)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
