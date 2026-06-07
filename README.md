# 电商商品价格自动化采集与对比脚本工具

## 功能介绍

- **价格采集**: 从京东等电商平台采集商品价格信息
- **报告生成**: 生成 Excel 和 Markdown 格式的价格报告
- **定时调度**: 支持每周日 21:20 自动运行
- **飞书集成**: 支持将报告上传到飞书云文档

## 项目结构

```
/workspace/
├── price_scraper/          # 核心模块
│   ├── __init__.py
│   ├── scraper.py          # 价格采集模块
│   ├── report_generator.py # 报告生成模块
│   └── feishu_uploader.py  # 飞书上传播
├── reports/                # 报告输出目录
├── logs/                   # 日志目录
├── main.py                 # 主程序
├── requirements.txt        # 依赖库
└── .env.example            # 配置示例
```

## 安装步骤

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 配置环境变量：
```bash
cp .env.example .env
# 编辑 .env 文件，填入飞书应用凭证
```

## 使用方法

### 1. 立即执行一次采集
```bash
python main.py --keyword "儿童智能手表" --run-once
```

### 2. 启动定时调度（每周日 21:20 执行）
```bash
python main.py --keyword "儿童智能手表" --schedule
```

### 3. 普通运行（立即执行一次）
```bash
python main.py --keyword "儿童智能手表"
```

## 配置说明

在 [`.env.example`](file:///workspace/.env.example) 中配置：
- `KEYWORD`: 搜索关键词
- `SCHEDULE_TIME`: 定时执行时间
- 飞书应用凭证（可选，用于上传到飞书）

## 报告输出

采集完成后，会在 `reports/` 目录下生成：
- Excel 格式报告（.xlsx）
- Markdown 格式报告（.md）

## 注意事项

1. 电商平台可能有反爬虫机制，使用时请遵守相关网站规则
2. 淘宝、拼多多等平台需要登录，当前示例中未实现完整功能
3. 飞书上传播需要配置飞书应用凭证
