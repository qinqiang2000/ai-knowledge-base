# 表关系与JOIN模式

本文档说明EOP数据库4个核心表之间的关系，并提供常用的JOIN查询模式。

## 表关系图

```
┌─────────────────────────────┐
│   t_ocm_order_header        │
│   (交易订单 - 主表)          │
│                             │
│   fid (PK)                  │
│   fbillno                   │
│   ftenant ────────┐         │
│   fcreatetime     │         │
│   fbusiness_type  │         │
│   fbiz_type       │         │
└──────────┬──────────────────┘
           │                 │
           │ 1:N             │ N:1
           │                 │
           ▼                 ▼
┌──────────────────┐  ┌──────────────────┐
│ t_ocm_order_lines│  │   t_ocm_tenant   │
│ (产品订单-明细)   │  │   (租户表)        │
│                  │  │                  │
│ fid (PK)         │  │ fid (PK)         │
│ fentryid (FK) ───┘  │ fname            │
│ fproduct_billno  │  │ fenable          │
│ fproduct         │  └──────────────────┘
│ fquantity        │
│ funit_price      │
└──────────────────┘
           ▲
           │ 关联关系
           │ (fproduct_serial_no
           │  或 fproduct_billno)
           │
┌──────────┴──────────────────┐
│ t_ocm_kbc_order_settle      │
│ (销售出库单/结算单)          │
│                             │
│ fbillno (PK)                │
│ fkbc_settle_billno ─────┐   │
│ fproduct_serial_no      │   │
│ fpost_date              │   │
│ fdelivery_status        │   │
└─────────────────────────┴───┘
                          │
                          └─> 关联到 t_ocm_order_header.fbillno
                              或 t_ocm_order_lines.fproduct_billno
```

## 关系说明

### 1. 交易订单 ←→ 产品订单（1:N）

- **关系类型**：一对多
- **关联字段**：
  - 主表：`t_ocm_order_header.fid`
  - 从表：`t_ocm_order_lines.fentryid`
- **说明**：一个交易订单可以包含多个产品订单明细

### 2. 交易订单 ←→ 租户（N:1）

- **关系类型**：多对一
- **关联字段**：
  - 订单表：`t_ocm_order_header.ftenant`
  - 租户表：`t_ocm_tenant.fid`
- **说明**：一个租户可以有多个订单

### 3. 销售出库单 ←→ 交易订单/产品订单（复杂关联）

- **关系类型**：条件关联（根据订单来源不同）
- **关联逻辑**：
  - **如果 forder_source = '金蝶中国'**：
    1. `t_ocm_kbc_order_settle.fkbc_settle_billno` → `t_ocm_order_header.fthird_party_billno`
    2. 再通过 `fproduct_serial_no` → `t_ocm_order_lines.fproduct_serial_no`
  - **如果 forder_source = '运营后台'**：
    - `t_ocm_kbc_order_settle.fkbc_settle_billno` → `t_ocm_order_lines.fproduct_billno`

---

## 常用JOIN模式

### 模式1：订单 + 产品明细

**场景**：查询订单的产品明细信息

```sql
SELECT
    h.fbillno AS 订单号,
    h.fcreatetime AS 订单创建时间,
    h.fbusiness_type AS 业务类型,
    l.fproduct AS 产品名称,
    l.fproduct_billno AS 产品订单号,
    l.fquantity AS 数量,
    l.funit_price AS 单价,
    (l.fquantity * l.funit_price) AS 小计
FROM t_ocm_order_header h
INNER JOIN t_ocm_order_lines l ON h.fid = l.fentryid
WHERE h.fcreatetime >= '2026-01-01'
ORDER BY h.fcreatetime DESC
LIMIT 100;
```

**使用场景**：
- 查询订单的产品构成
- 统计产品销量
- 分析产品组合

---

### 模式2：订单 + 租户

**场景**：查询订单及其关联的租户信息

```sql
SELECT
    h.fbillno AS 订单号,
    h.fcreatetime AS 创建时间,
    h.fbusiness_type AS 业务类型,
    t.fname AS 租户名称,
    t.fcontact_name AS 联系人,
    t.fcontact_phone AS 联系电话,
    t.fenable AS 租户状态
FROM t_ocm_order_header h
LEFT JOIN t_ocm_tenant t ON h.ftenant = t.fid
WHERE h.fcreatetime >= '2026-01-01'
ORDER BY h.fcreatetime DESC
LIMIT 100;
```

**使用场景**：
- 查询租户的订单历史
- 分析租户购买行为
- 租户维度的数据统计

**注意**：使用 LEFT JOIN 以包含租户信息可能缺失的订单

---

### 模式3：订单 + 产品明细 + 租户（完整关联）

**场景**：查询订单的完整信息（含产品和租户）

```sql
SELECT
    h.fbillno AS 订单号,
    h.fcreatetime AS 创建时间,
    h.fbusiness_type AS 业务类型,
    h.fbiz_type AS 订单类型,
    t.fname AS 租户名称,
    l.fproduct AS 产品名称,
    l.fquantity AS 数量,
    l.funit_price AS 单价,
    (l.fquantity * l.funit_price) AS 金额
FROM t_ocm_order_header h
INNER JOIN t_ocm_order_lines l ON h.fid = l.fentryid
LEFT JOIN t_ocm_tenant t ON h.ftenant = t.fid
WHERE h.fcreatetime >= '2026-01-01'
  AND h.fbusiness_type IN ('New', 'Renew')
ORDER BY h.fcreatetime DESC
LIMIT 100;
```

**使用场景**：
- 生成订单报表
- 订单详细信息查询
- 多维度数据分析

---

### 模式4：按订单聚合产品金额

**场景**：统计每个订单的总金额

```sql
SELECT
    h.fbillno AS 订单号,
    h.fcreatetime AS 创建时间,
    t.fname AS 租户名称,
    COUNT(l.fid) AS 产品数量,
    SUM(l.fquantity * l.funit_price) AS 订单总额
FROM t_ocm_order_header h
INNER JOIN t_ocm_order_lines l ON h.fid = l.fentryid
LEFT JOIN t_ocm_tenant t ON h.ftenant = t.fid
WHERE h.fcreatetime >= '2026-01-01'
GROUP BY h.fbillno, h.fcreatetime, t.fname
ORDER BY 订单总额 DESC
LIMIT 100;
```

**使用场景**：
- 订单金额排行
- 大客户识别
- 营收统计

---

### 模式5：结算单 → 产品订单（运营后台订单）

**场景**：查询运营后台产生的结算单及其产品信息

```sql
SELECT
    s.fbillno AS 结算单号,
    s.fpost_date AS 记账日期,
    s.fdelivery_status AS 交付状态,
    s.fsale_product_name AS 销售产品,
    l.fproduct AS 产品编码,
    l.fquantity AS 数量,
    l.funit_price AS 单价
FROM t_ocm_kbc_order_settle s
LEFT JOIN t_ocm_order_lines l
    ON s.fkbc_settle_billno = l.fproduct_billno
WHERE s.fpost_date >= '2026-01-01'
  AND s.fdelivery_status = '已交付'
ORDER BY s.fpost_date DESC
LIMIT 100;
```

**使用场景**：
- 结算数据查询
- 已交付订单统计
- 收款分析

**注意**：此模式适用于 forder_source = '运营后台' 的订单

---

### 模式6：按租户统计订单

**场景**：统计每个租户的订单数量和金额

```sql
SELECT
    t.fid AS 租户ID,
    t.fname AS 租户名称,
    COUNT(DISTINCT h.fbillno) AS 订单数量,
    COUNT(l.fid) AS 产品数量,
    SUM(l.fquantity * l.funit_price) AS 总金额
FROM t_ocm_tenant t
LEFT JOIN t_ocm_order_header h ON t.fid = h.ftenant
LEFT JOIN t_ocm_order_lines l ON h.fid = l.fentryid
WHERE h.fcreatetime >= '2025-01-01'
  AND h.fbusiness_type != 'Upgradation'
GROUP BY t.fid, t.fname
HAVING COUNT(DISTINCT h.fbillno) > 0
ORDER BY 总金额 DESC
LIMIT 100;
```

**使用场景**：
- 租户价值分析
- 客户排名
- 销售业绩统计

---

### 模式7：按产品统计销量

**场景**：统计各产品的销售情况

```sql
SELECT
    l.fproduct AS 产品编码,
    COUNT(DISTINCT l.fentryid) AS 订单数量,
    SUM(l.fquantity) AS 总销量,
    AVG(l.funit_price) AS 平均单价,
    SUM(l.fquantity * l.funit_price) AS 总金额
FROM t_ocm_order_lines l
INNER JOIN t_ocm_order_header h ON l.fentryid = h.fid
WHERE h.fcreatetime >= '2025-01-01'
  AND h.fbusiness_type IN ('New', 'Renew', 'Add')
  AND h.fbiz_type = 'Standard'
GROUP BY l.fproduct
ORDER BY 总金额 DESC
LIMIT 50;
```

**使用场景**：
- 产品销量排行
- 产品线分析
- SKU 优化

---

### 模式8：按时间趋势分析

**场景**：按月统计订单趋势

```sql
SELECT
    DATE_TRUNC('month', h.fcreatetime) AS 月份,
    COUNT(DISTINCT h.fbillno) AS 订单数量,
    COUNT(l.fid) AS 产品数量,
    SUM(l.fquantity * l.funit_price) AS 总金额
FROM t_ocm_order_header h
INNER JOIN t_ocm_order_lines l ON h.fid = l.fentryid
WHERE h.fcreatetime >= '2025-01-01'
  AND h.fbusiness_type != 'Upgradation'
  AND h.fbiz_type = 'Standard'
GROUP BY DATE_TRUNC('month', h.fcreatetime)
ORDER BY 月份 DESC;
```

**使用场景**：
- 月度营收统计
- 趋势分析
- 同比环比计算

---

## JOIN类型选择指南

### INNER JOIN vs LEFT JOIN

**INNER JOIN（内连接）**：
- 只返回两表都有匹配记录的数据
- 用于必须关联成功的场景
- 示例：订单+产品明细（每个订单必须有产品）

**LEFT JOIN（左外连接）**：
- 返回左表所有记录，右表没有匹配时返回 NULL
- 用于可能关联失败的场景
- 示例：订单+租户（租户信息可能缺失）

### 选择建议

| 场景 | 推荐JOIN类型 | 原因 |
|------|-------------|------|
| 订单 + 产品明细 | INNER JOIN | 订单必须有产品 |
| 订单 + 租户 | LEFT JOIN | 租户信息可能缺失 |
| 租户 + 订单 | LEFT JOIN | 某些租户可能没有订单 |
| 结算单 + 产品 | LEFT JOIN | 关联可能失败 |

---

## 性能优化建议

### 1. 添加时间范围过滤

**总是在主表添加时间过滤**，避免全表扫描：

```sql
WHERE h.fcreatetime >= '2025-01-01'  -- 好
WHERE DATE_TRUNC('month', h.fcreatetime) = '2025-01-01'  -- 差（无法使用索引）
```

### 2. 限制返回行数

**在查询明细时添加 LIMIT**：

```sql
LIMIT 100  -- 或其他合理的数量
```

### 3. 避免 SELECT *

**明确指定需要的字段**：

```sql
SELECT h.fbillno, h.fcreatetime, t.fname  -- 好
SELECT *  -- 差
```

### 4. 合理使用聚合

**聚合统计时注意 GROUP BY 字段选择**：

```sql
-- 按月统计（好）
GROUP BY DATE_TRUNC('month', h.fcreatetime)

-- 按订单统计（可能产生大量分组）
GROUP BY h.fbillno
```

---

## 注意事项

### 1. 数据一致性

- 订单可能存在没有租户信息的情况（使用 LEFT JOIN）
- 结算单与订单的关联逻辑依赖 forder_source 字段
- Upgradation 类型订单在统计时通常需要过滤

### 2. 时间字段选择

- **查询订单**：用 `t_ocm_order_header.fcreatetime`
- **查询结算**：用 `t_ocm_kbc_order_settle.fpost_date`

### 3. 状态过滤

- 结算统计时过滤 `fdelivery_status = '已交付'`
- 订单统计时过滤 `fbusiness_type != 'Upgradation'`
- 付费订单过滤 `fbiz_type = 'Standard'`

---

## 相关文档

- [schema.md](./schema.md) - 详细的表结构和字段说明
- [field_enums.md](./field_enums.md) - 枚举值详细说明
- [../DIRECTORY_MAP.md](../DIRECTORY_MAP.md) - 文档导航
