/**
 * PriceScout 前端应用逻辑
 */

// 全局图表实例
let charts = {};

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    initEventListeners();
    // 页面加载时自动加载演示数据
    setTimeout(() => loadDemoData(), 500);
});

function initEventListeners() {
    // 搜索按钮
    document.getElementById('searchBtn').addEventListener('click', handleSearch);

    // 回车搜索
    document.getElementById('keywordInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleSearch();
    });

    // 演示数据按钮
    document.getElementById('demoBtn').addEventListener('click', loadDemoData);

    // 窗口大小变化时重绘图表
    window.addEventListener('resize', () => {
        Object.values(charts).forEach(chart => chart && chart.resize());
    });
}

// 获取选中的平台
function getSelectedPlatforms() {
    const checks = document.querySelectorAll('.platform-check:checked');
    return Array.from(checks).map(c => c.value).join(',');
}

// 显示/隐藏加载状态
function setLoading(loading) {
    const el = document.getElementById('loadingState');
    if (loading) {
        el.classList.remove('hidden');
        document.getElementById('statsSection').classList.add('hidden');
        document.getElementById('chartsSection').classList.add('hidden');
        document.getElementById('tableSection').classList.add('hidden');
        document.getElementById('exampleSection').classList.add('hidden');
    } else {
        el.classList.add('hidden');
    }
}

// 处理搜索
async function handleSearch() {
    const keyword = document.getElementById('keywordInput').value.trim();
    if (!keyword) {
        alert('请输入搜索关键词');
        return;
    }

    const platforms = getSelectedPlatforms();
    const limit = document.getElementById('limitSelect').value;

    setLoading(true);

    try {
        const response = await fetch('/api/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ keyword, platforms, limit: parseInt(limit) })
        });

        const data = await response.json();

        if (data.success) {
            renderResults(data);
        } else {
            alert('采集失败: ' + (data.error || '未知错误'));
        }
    } catch (error) {
        alert('请求失败: ' + error.message);
    } finally {
        setLoading(false);
    }
}

// 加载演示数据
async function loadDemoData() {
    setLoading(true);

    try {
        const response = await fetch('/api/demo');
        const data = await response.json();

        if (data.success) {
            document.getElementById('keywordInput').value = data.keyword || '蓝牙耳机';
            renderResults(data);
        }
    } catch (error) {
        console.error('加载演示数据失败:', error);
    } finally {
        setLoading(false);
    }
}

// 渲染结果
function renderResults(data) {
    const { report, chart_data, products, keyword } = data;

    // 显示区域
    document.getElementById('statsSection').classList.remove('hidden');
    document.getElementById('chartsSection').classList.remove('hidden');
    document.getElementById('tableSection').classList.remove('hidden');

    // 更新统计卡片
    updateStats(report, chart_data);

    // 渲染图表
    renderCharts(chart_data);

    // 渲染表格
    renderTable(report.comparison_matrix || []);
}

// 更新统计卡片
function updateStats(report, chartData) {
    const summary = report.summary || {};
    const topValue = report.top_value || [];

    document.getElementById('statTotal').textContent = summary.total_products || 0;
    document.getElementById('statAvgPrice').textContent = '¥' + (summary.avg_price || 0);

    const priceTrend = report.price_trend || {};
    document.getElementById('statMinPrice').textContent = '¥' + (priceTrend.min_price || 0);

    if (topValue.length > 0) {
        const best = topValue[0];
        document.getElementById('statBestValue').textContent = '¥' + best.price;
        document.getElementById('statBestValue').title = best.name;
    }
}

// 渲染图表
function renderCharts(chartData) {
    // 销毁旧图表
    Object.values(charts).forEach(c => c && c.dispose());
    charts = {};

    // 1. 价格分布柱状图
    renderPriceDistChart(chartData.price_distribution || []);

    // 2. 平台对比雷达图
    renderPlatformRadarChart(chartData.platform_comparison || []);

    // 3. 性价比散点图
    renderScatterChart(chartData.scatter_data || []);

    // 4. 价格排行条形图
    renderRankChart(chartData.price_rank || []);
}

// 价格分布图
function renderPriceDistChart(distribution) {
    const dom = document.getElementById('priceDistChart');
    if (!dom) return;

    const chart = echarts.init(dom);
    charts.priceDist = chart;

    chart.setOption({
        tooltip: { trigger: 'axis' },
        grid: { left: '3%', right: '4%', bottom: '15%', top: '10%', containLabel: true },
        xAxis: {
            type: 'category',
            data: distribution.map(d => d.range),
            axisLabel: { color: '#94a3b8', rotate: 30, fontSize: 10 },
            axisLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } }
        },
        yAxis: {
            type: 'value',
            axisLabel: { color: '#94a3b8' },
            axisLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } },
            splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } }
        },
        series: [{
            data: distribution.map(d => d.count),
            type: 'bar',
            barWidth: '60%',
            itemStyle: {
                borderRadius: [4, 4, 0, 0],
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                    { offset: 0, color: '#6366f1' },
                    { offset: 1, color: '#8b5cf6' }
                ])
            }
        }]
    });
}

// 平台对比雷达图
function renderPlatformRadarChart(platformData) {
    const dom = document.getElementById('platformRadarChart');
    if (!dom || platformData.length === 0) return;

    const chart = echarts.init(dom);
    charts.platformRadar = chart;

    const maxPrice = Math.max(...platformData.map(p => p.avg_price)) * 1.2;
    const maxSales = Math.max(...platformData.map(p => p.avg_sales)) * 1.2;
    const maxRating = 5;

    chart.setOption({
        tooltip: {},
        legend: {
            data: platformData.map(p => p.platform),
            textStyle: { color: '#94a3b8' },
            bottom: 0
        },
        radar: {
            indicator: [
                { name: '平均价格', max: maxPrice },
                { name: '平均销量', max: maxSales },
                { name: '平均评分', max: maxRating },
                { name: '商品数量', max: Math.max(...platformData.map(p => p.count)) * 1.5 }
            ],
            axisName: { color: '#94a3b8' },
            splitArea: {
                areaStyle: {
                    color: ['rgba(99,102,241,0.02)', 'rgba(99,102,241,0.05)']
                }
            }
        },
        series: [{
            type: 'radar',
            data: platformData.map(p => ({
                value: [p.avg_price, p.avg_sales, p.avg_rating, p.count],
                name: p.platform,
                areaStyle: { opacity: 0.2 }
            })),
            lineStyle: { width: 2 }
        }]
    });
}

// 性价比散点图
function renderScatterChart(scatterData) {
    const dom = document.getElementById('scatterChart');
    if (!dom) return;

    const chart = echarts.init(dom);
    charts.scatter = chart;

    chart.setOption({
        tooltip: {
            formatter: function(params) {
                return `<strong>${params.data[3]}</strong><br/>` +
                       `价格: ¥${params.data[0]}<br/>` +
                       `性价比: ${params.data[1]}<br/>` +
                       `销量: ${params.data[2]}`;
            }
        },
        grid: { left: '3%', right: '8%', bottom: '10%', top: '10%', containLabel: true },
        xAxis: {
            type: 'value',
            name: '价格',
            nameTextStyle: { color: '#94a3b8' },
            axisLabel: { color: '#94a3b8' },
            axisLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } },
            splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } }
        },
        yAxis: {
            type: 'value',
            name: '性价比得分',
            nameTextStyle: { color: '#94a3b8' },
            axisLabel: { color: '#94a3b8' },
            axisLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } },
            splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } }
        },
        series: [{
            type: 'scatter',
            data: scatterData.map(d => [d.price, d.value_score, d.sales, d.name]),
            symbolSize: function(data) {
                return Math.max(8, Math.min(30, Math.sqrt(data[2]) / 8));
            },
            itemStyle: {
                color: new echarts.graphic.RadialGradient(0.4, 0.3, 1, [
                    { offset: 0, color: '#6366f1' },
                    { offset: 1, color: '#a855f7' }
                ]),
                opacity: 0.8
            }
        }]
    });
}

// 价格排行图
function renderRankChart(rankData) {
    const dom = document.getElementById('rankChart');
    if (!dom) return;

    const chart = echarts.init(dom);
    charts.rank = chart;

    // 取前15个
    const data = rankData.slice(0, 15);

    chart.setOption({
        tooltip: { trigger: 'axis' },
        grid: { left: '3%', right: '8%', bottom: '5%', top: '5%', containLabel: true },
        xAxis: {
            type: 'value',
            axisLabel: { color: '#94a3b8', formatter: '¥{value}' },
            axisLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } },
            splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } }
        },
        yAxis: {
            type: 'category',
            data: data.map(d => d.name).reverse(),
            axisLabel: { color: '#94a3b8', fontSize: 10 },
            axisLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } }
        },
        series: [{
            type: 'bar',
            data: data.map(d => d.price).reverse(),
            barWidth: '60%',
            itemStyle: {
                borderRadius: [0, 4, 4, 0],
                color: function(params) {
                    const colors = ['#10b981', '#34d399', '#6ee7b7', '#a7f3d0', '#059669'];
                    return colors[params.dataIndex % colors.length];
                }
            }
        }]
    });
}

// 渲染表格
function renderTable(matrix) {
    const tbody = document.getElementById('productTableBody');
    tbody.innerHTML = '';

    matrix.forEach((item, index) => {
        const row = document.createElement('tr');

        // 平台样式
        const platformClass = `platform-${item.platform}`;

        // 标签HTML
        const tagsHtml = (item.tags || []).map(tag => {
            const tagClass = tag === '高性价比' ? 'tag-value' :
                            tag === '热销' ? 'tag-hot' :
                            tag === '高评分' ? 'tag-rating' : 'tag-discount';
            return `<span class="tag ${tagClass}">${tag}</span>`;
        }).join('');

        // 折扣计算
        const discountRate = item.original_price > 0
            ? Math.round((1 - item.price / item.original_price) * 100)
            : 0;
        const discountText = discountRate > 0 ? `${discountRate}%` : '-';

        row.innerHTML = `
            <td>${index + 1}</td>
            <td title="${item.name}">${truncate(item.name, 35)}</td>
            <td class="${platformClass}">${item.platform.toUpperCase()}</td>
            <td><strong>¥${item.price}</strong></td>
            <td style="text-decoration: line-through; opacity: 0.5;">¥${item.original_price}</td>
            <td>${discountText}</td>
            <td>${formatNumber(item.sales)}</td>
            <td>${item.shop_rating}</td>
            <td>${item.value_score}</td>
            <td>${tagsHtml}</td>
        `;

        tbody.appendChild(row);
    });
}

// 工具函数
function truncate(str, len) {
    if (str.length <= len) return str;
    return str.substring(0, len) + '...';
}

function formatNumber(num) {
    if (num >= 10000) {
        return (num / 10000).toFixed(1) + '万';
    }
    if (num >= 1000) {
        return (num / 1000).toFixed(1) + '千';
    }
    return num.toString();
}
