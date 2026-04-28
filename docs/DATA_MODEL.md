# 数据模型说明

## Source 层

Source 层保存官网来源、原始 ID 和快照。

- `source_sites`
- `source_pages`
- `source_product_mappings`
- `crawler_snapshots`
- `crawler_jobs`

## Canonical 层

Canonical 层是平台统一商品模型。

- `brands`
- `bike_series`
- `bike_models`
- `bike_variants`
- `bike_images`
- `bike_components`
- `bike_geometry_profiles`
- `bike_geometry_values`
- `bike_size_recommendations`
- `price_history`

## 设计取舍

- `bike_models` 是主要展示对象，对应官网上的一个整车商品或配置版本。
- `bike_variants` 存颜色、SKU、尺码、库存等变体信息。
- `raw_summary` 和 `raw_data` 保留官网字段，避免解析规则变化后无法追溯。
- 规格配置使用行式结构，便于支持不同品牌不一致的组件表。
- 几何数据拆成 profile 和 values，便于做跨尺码、跨车型对比。
