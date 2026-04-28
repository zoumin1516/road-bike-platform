# API 草案

接口前缀：`/api`

## `GET /api/brands`

返回品牌列表。

## `GET /api/bikes`

返回车型列表。

查询参数：

- `brand`
- `category`
- `usage_type`
- `keyword`
- `page`
- `page_size`

## `GET /api/bikes/{bike_id}`

返回车型详情，包含：

- 品牌
- 车系
- 图片
- 颜色变体
- 价格
- 规格配置
- 原始摘要

## `GET /api/search?q=keyword`

按车型名称搜索。

## `GET /api/compare?ids=1,2,3`

返回最多 4 个车型详情，用于前端横向对比。
