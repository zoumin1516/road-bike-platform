# 公路车商品数据聚合平台

目标是聚合 Canyon、Specialized、Trek、Giant、Pinarello 等品牌官网的公路车商品数据。

## 目录

```text
backend/   FastAPI + SQLAlchemy + Alembic + crawler
frontend/  Next.js + TypeScript 前端
docs/      工程说明与数据字典
```

## MVP 范围

- 仅覆盖公路车整车商品。
- 首批品牌优先级：Giant、Trek、Specialized、Pinarello。
- 已实现 Giant、Specialized 和 Pinarello 中国官网：列表抓取、详情抓取、标准化、入库、API、前端展示。

## 后端启动

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload
```

默认数据库地址可通过 `DATABASE_URL` 配置，例如：

```bash
export DATABASE_URL=postgresql+psycopg://roadbike:roadbike@localhost:5432/roadbike
```

## 前端启动

```bash
cd frontend
npm install
npm run dev
```

默认 API 地址为 `http://localhost:8000`，可通过 `NEXT_PUBLIC_API_BASE_URL` 覆盖。

品牌 CDN 图片会先经 `/api/image-cache` 拉取并落在本地磁盘（默认 `frontend/.cache/image-cache`，可用环境变量 `IMAGE_CACHE_DIR` 修改），浏览器侧响应头为长期缓存 `max-age=31536000`；白名单与 `next.config.mjs` 的 `remotePatterns` 一致。

## Giant 抓取

手动运行：

```bash
cd backend
python -m app.tasks.run_giant --limit 20
```

该任务会：

1. 抓取 Giant `bike_finder.html` 列表页。
2. 提取 `bike_view.html?id=...` 商品。
3. 请求 `get_bike_info?id=...` 详情 JSON。
4. 抓取详情 HTML 中的规格表。
5. 保存 raw snapshot。
6. upsert 到标准化数据表。

## Specialized 抓取

手动运行：

```bash
cd backend
python -m app.tasks.run_specialized --limit 20
```

该任务会：

1. 请求 Specialized Hybris OCC 搜索接口，筛选中国官网在售公路车整车。
2. 请求商品详情、规格和几何接口。
3. 保存 raw snapshot。
4. upsert 到标准化数据表。

## Pinarello 抓取

手动运行：

```bash
cd backend
python -m app.tasks.run_pinarello --limit 20
```

该任务会：

1. 解析 Pinarello 中国官网公路车列表页中的商品卡片。
2. 抓取商品详情页 HTML，提取变体、图片、组件和几何表。
3. 保存 raw snapshot。
4. upsert 到标准化数据表。

## 定时抓取

项目使用 Celery Beat + Redis 调度正式抓取任务。默认配置：

- 每天 `03:15`（`Asia/Shanghai`）运行 Giant 全量同步。
- 每天 `04:15`（`Asia/Shanghai`）运行 Specialized 全量同步。
- 每天 `05:15`（`Asia/Shanghai`）运行 Pinarello 全量同步。

```bash
cd backend
celery -A app.core.celery_app.celery_app worker --loglevel=info
celery -A app.core.celery_app.celery_app beat --loglevel=info
```

如果使用 Docker Compose：

```bash
docker-compose up -d postgres redis backend-worker backend-beat
```

任务入口：

- Celery task：`app.tasks.celery_tasks.sync_giant_products`
- Celery task：`app.tasks.celery_tasks.sync_specialized_products`
- Celery task：`app.tasks.celery_tasks.sync_pinarello_products`
- 手动脚本：`app.tasks.run_giant`
- 手动脚本：`app.tasks.run_specialized`
- 手动脚本：`app.tasks.run_pinarello`
- 调度配置：`backend/app/core/celery_app.py`

每次运行都会写入 `crawler_jobs`，记录开始时间、结束时间、状态和统计信息。
