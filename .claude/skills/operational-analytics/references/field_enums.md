# 字段枚举值详细说明

本文档详细说明EOP数据库中各字段的枚举值及其含义。

## 目录

- [t_ocm_order_header（交易订单）](#t_ocm_order_header交易订单)
  - [fbusiness_type（业务类型）](#fbusiness_type业务类型)
  - [fbiz_type（订单类别）](#fbiz_type订单类别)
  - [fbill_source（订单来源）](#fbill_source订单来源)
- [t_ocm_kbc_order_settle（销售出库单）](#t_ocm_kbc_order_settle销售出库单)
  - [fdelivery_status（交付状态）](#fdelivery_status交付状态)
- [t_ocm_tenant（租户表）](#t_ocm_tenant租户表)
  - [fenable（使用状态）](#fenable使用状态)

---

## t_ocm_order_header（交易订单）

### fbusiness_type（业务类型）

**字段说明**：表示订单的购买类型，影响营收统计逻辑。

| 枚举值 | 中文名称 | 含义 | 是否计入营收 | SQL过滤建议 |
|--------|---------|------|-------------|-----------|
| `New` | 新购 | 客户首次购买产品 | ✅ 是 | 包含在统计中 |
| `Renew` | 续费 | 客户续期已有产品 | ✅ 是 | 包含在统计中 |
| `Add` | 加购 | 在现有订单基础上增加数量或模块 | ✅ 是 | 包含在统计中 |
| `Return` | 退货 | 客户退款 | ❌ 否 | 金额为负数，需特殊处理 |
| `Upgradation` | 升级 | 版本升级（不单独计费） | ❌ 否 | **必须过滤掉** |

#### 使用示例

```sql
-- 查询有效订单（过滤掉升级订单）
WHERE fbusiness_type != 'Upgradation'

-- 仅查询新购和续费
WHERE fbusiness_type IN ('New', 'Renew')

-- 包含所有正常业务类型
WHERE fbusiness_type IN ('New', 'Renew', 'Add')
```

#### 重要提示

⚠️ **Upgradation（升级）订单不属于有效订单**，计算订单收款时**必须过滤**：
- 升级订单不单独计费
- 在营收统计、订单数量统计等场景中应排除
- 示例：`WHERE fbusiness_type != 'Upgradation'`

---

### fbiz_type（订单类别）

**字段说明**：表示订单的付费类型，区分标准订单、特批订单和试用订单。

| 枚举值 | 中文名称 | 含义 | 是否付费 | 使用场景 |
|--------|---------|------|---------|---------|
| `Standard` | 标准订单 | 正式付费订单 | ✅ 是 | 营收统计 |
| `Special` | 特批订单 | 经审批的免费订单 | ❌ 否 | 特殊客户、合作伙伴 |
| `Free` | 试用订单 | 免费试用 | ❌ 否 | 产品试用 |

#### 使用示例

```sql
-- 仅查询付费订单
WHERE fbiz_type = 'Standard'

-- 查询所有免费订单
WHERE fbiz_type IN ('Special', 'Free')

-- 营收统计（标准订单 + 有效业务类型）
WHERE fbiz_type = 'Standard'
  AND fbusiness_type IN ('New', 'Renew', 'Add')
```

#### 统计建议

- **营收统计**：通常只统计 `fbiz_type = 'Standard'` 的订单
- **订单量统计**：可能需要包含所有类型
- **客户分析**：区分付费客户和试用客户

---

### fbill_source（订单来源）

**字段说明**：表示订单的销售渠道。

| 枚举值 | 渠道名称 | 说明 |
|--------|---------|------|
| `1` | 发票云直销 | 发票云团队直接销售 |
| `2` | 生态伙伴 | 通过生态合作伙伴销售 |
| `3` | 营销伙伴 | 通过营销渠道伙伴销售 |
| `4` | 金蝶中国直销 | 金蝶中国团队直接销售 |
| `5` | 金蝶中国分销 | 通过金蝶中国分销渠道销售 |
| `6` | 个人伙伴 | 个人代理销售 |
| `7` | 发票云特批 | 发票云特批订单 |

#### 使用示例

```sql
-- 按渠道统计订单
SELECT
    CASE fbill_source
        WHEN 1 THEN '发票云直销'
        WHEN 2 THEN '生态伙伴'
        WHEN 3 THEN '营销伙伴'
        WHEN 4 THEN '金蝶中国直销'
        WHEN 5 THEN '金蝶中国分销'
        WHEN 6 THEN '个人伙伴'
        WHEN 7 THEN '发票云特批'
        ELSE '未知'
    END AS 渠道,
    COUNT(*) AS 订单数
FROM t_ocm_order_header
GROUP BY fbill_source
ORDER BY fbill_source;

-- 查询直销渠道订单
WHERE fbill_source IN (1, 4)  -- 发票云直销 + 金蝶中国直销

-- 查询伙伴渠道订单
WHERE fbill_source IN (2, 3, 5, 6)  -- 各类伙伴渠道
```

#### 分析维度

- **直销 vs 分销**：渠道 1,4 vs 渠道 2,3,5,6
- **发票云 vs 金蝶中国**：渠道 1,7 vs 渠道 4,5
- **渠道绩效分析**：各渠道的订单量、金额对比

---

## t_ocm_kbc_order_settle（销售出库单）

### fdelivery_status（交付状态）

**字段说明**：表示订单是否已经交付，影响结算统计。

| 枚举值 | 中文名称 | 含义 | 是否可结算 |
|--------|---------|------|----------|
| `已交付` | 已交付 | 订单已完成交付 | ✅ 是 |
| `待交付` | 待交付 | 订单尚未交付 | ❌ 否 |
| `已取消` | 已取消 | 订单已取消（如果存在） | ❌ 否 |

#### 使用示例

```sql
-- 查询已交付订单（可结算）
WHERE fdelivery_status = '已交付'

-- 统计营收（只统计已交付）
SELECT
    DATE_TRUNC('month', fpost_date) AS 月份,
    COUNT(*) AS 订单数,
    SUM(famount) AS 总金额
FROM t_ocm_kbc_order_settle
WHERE fdelivery_status = '已交付'
GROUP BY 月份;

-- 查询待交付订单
WHERE fdelivery_status = '待交付'
```

#### 重要提示

⚠️ **计算收款时需要过滤**：
- 只有 `fdelivery_status = '已交付'` 的订单才能计入结算
- 待交付订单不应计入营收统计
- 结算报表必须加此过滤条件

---

## t_ocm_tenant（租户表）

### fenable（使用状态）

**字段说明**：表示租户账号是否可用。

| 枚举值 | 含义 | 说明 |
|--------|-----|------|
| `0` | 禁用 | 租户账号已禁用，不能使用 |
| `1` | 可用 | 租户账号正常可用 |

#### 使用示例

```sql
-- 查询可用租户
WHERE fenable = 1

-- 查询已禁用租户
WHERE fenable = 0

-- 统计租户状态分布
SELECT
    CASE fenable
        WHEN 1 THEN '可用'
        WHEN 0 THEN '禁用'
        ELSE '未知'
    END AS 状态,
    COUNT(*) AS 数量
FROM t_ocm_tenant
GROUP BY fenable;
```

#### 使用建议

- **活跃客户分析**：通常只查询 `fenable = 1` 的租户
- **流失客户分析**：可以查询 `fenable = 0` 的租户
- **订单查询**：关联租户时可能不需要过滤此字段（已禁用的租户可能还有历史订单）

---

## 常见查询场景的过滤组合

### 场景1：标准营收统计

```sql
SELECT ...
FROM t_ocm_order_header h
WHERE h.fbiz_type = 'Standard'           -- 只统计付费订单
  AND h.fbusiness_type != 'Upgradation'  -- 过滤升级订单
  AND h.fbusiness_type != 'Return'       -- 过滤退货（或单独统计）
```

### 场景2：新购续费分析

```sql
SELECT ...
FROM t_ocm_order_header h
WHERE h.fbusiness_type IN ('New', 'Renew')  -- 只看新购和续费
  AND h.fbiz_type = 'Standard'              -- 只看付费订单
```

### 场景3：结算收款统计

```sql
SELECT ...
FROM t_ocm_kbc_order_settle s
WHERE s.fdelivery_status = '已交付'  -- 只统计已交付的
  AND s.fpost_date >= '2025-01-01'  -- 时间范围
```

### 场景4：渠道绩效对比

```sql
SELECT
    CASE fbill_source
        WHEN 1 THEN '发票云直销'
        WHEN 4 THEN '金蝶中国直销'
        ELSE '伙伴渠道'
    END AS 渠道类型,
    COUNT(*) AS 订单数
FROM t_ocm_order_header
WHERE fbiz_type = 'Standard'
  AND fbusiness_type IN ('New', 'Renew', 'Add')
GROUP BY 渠道类型;
```

---

## 字段组合使用指南

### 订单有效性判断

**有效订单**必须同时满足：
1. ✅ `fbiz_type = 'Standard'`（标准付费订单）
2. ✅ `fbusiness_type NOT IN ('Upgradation', 'Return')`（排除升级和退货）
3. ✅ 可选：根据业务需求选择特定的 fbusiness_type

### 营收统计标准

**计入营收的订单**：
```sql
WHERE fbiz_type = 'Standard'
  AND fbusiness_type IN ('New', 'Renew', 'Add')
  AND fcreatetime >= '开始时间'
```

**结算收款统计**：
```sql
WHERE fdelivery_status = '已交付'
  AND fpost_date >= '开始时间'
```

### 特殊订单处理

**退货订单（Return）**：
- 金额通常为负数
- 需要单独统计或在营收中扣除
- 不能简单过滤掉，要看具体业务需求

**升级订单（Upgradation）**：
- 必须过滤掉，不计入任何营收统计
- 不计入订单数量统计

**特批/试用订单（Special/Free）**：
- 不计入营收统计
- 但可能需要统计订单量（例如试用转化率分析）

---

## 相关文档

- [schema.md](./schema.md) - 详细的表结构和字段说明
- [relationships.md](./relationships.md) - 表关系和 JOIN 模式
- [../DIRECTORY_MAP.md](../DIRECTORY_MAP.md) - 文档导航
