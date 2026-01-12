---
name: operational-analytics
description: |
  运营分析Agent，负责EOP（Enterprise Operation Platform，运营平台）数据库查询与分析。支持订单查询、租户数据统计、营收趋势分析、运营报表生成。

  触发词：EOP、运营平台、Enterprise operation platform、订单查询、租户数据、销售数据、营收分析、运营报表、数据统计、交易订单、产品订单、结算单、销售出库单、t_ocm_kbc_order_settle、t_ocm_order_header、t_ocm_order_lines、t_ocm_tenant
---

# 运营分析 Skill

根据自然语言查询EOP数据库，生成SQL并返回结果。

---

## 查询工具

```bash
# 执行 SQL 查询（自动安全检查：SELECT-only, 4表白名单, 60秒超时）
source .venv/bin/activate
python .claude/skills/operational-analytics/scripts/query.py "SELECT ..."

# 结果为空时诊断
python .claude/skills/operational-analytics/scripts/diagnose.py --tenant "租户名" --year 2025
```

---

## 表结构

### 1. t_ocm_kbc_order_settle（销售出库单/结算表）

**用途**：结算、付款查询，**按客户名搜索最直接**

| 字段名 | 含义 | 备注 |
|--------|------|------|
| fbillno | 结算单号 | - |
| fkbc_settle_billno | 关联订单号 | 关联逻辑复杂，不建议依赖 |
| **fuse_customer** | 使用客户 | **客户名搜索首选字段** |
| **fsign_customer** | 签约客户 | **客户名搜索备选字段** |
| **fsale_product_name** | 销售产品 | 产品名称 |
| fversion_no | 版本号 | - |
| **fpost_date** | 记账日期 | **时间轴字段** |
| **fdelivery_status** | 交付状态 | '已交付' / '待交付' |
| **famount** | 金额（不含税） | - |
| ftax_amount | 税额 | - |
| **fprice_tax_amount** | 金额（含税） | - |
| forder_source | 订单来源 | '金蝶中国' / '运营后台' |

### 2. t_ocm_order_header（交易订单主表）

**用途**：订单查询

| 字段名 | 含义 | 备注 |
|--------|------|------|
| fid | 主键ID | 关联 t_ocm_order_lines.fentryid |
| fbillno | 订单号 | - |
| **fcreatetime** | 创建时间 | **时间轴字段** |
| **ftenant** | 租户ID | 关联 t_ocm_tenant.fid |
| **fbiz_type** | 订单类别 | 'Standard' / 'Special' / 'Free' |
| **fbusiness_type** | 业务类型 | 'New' / 'Renew' / 'Add' / 'Upgradation' / 'Return' |
| ftotal_amount | 订单总额 | 产品明细缺失时用此字段 |
| fproduct_num | 产品数量 | - |
| fbillstatus | 单据状态 | - |
| fbill_source | 订单来源 | 1-7 (数字) |

### 3. t_ocm_order_lines（产品订单明细）

**用途**：订单产品明细，**数据可能不完整**

| 字段名 | 含义 | 备注 |
|--------|------|------|
| fid | 主键ID | - |
| **fentryid** | 关联订单ID | 关联 t_ocm_order_header.fid |
| fproduct | 产品编码 | - |
| fproduct_billno | 产品订单号 | - |
| fquantity | 数量 | - |
| funit_price | 单价 | - |
| ftax_price | 含税单价 | - |

**⚠️ 数据完整性**：此表经常无数据，优先使用：
- 结算表 (t_ocm_kbc_order_settle) 查产品信息
- 订单表 (t_ocm_order_header.ftotal_amount) 查金额

### 4. t_ocm_tenant（租户表）

**用途**：租户基本信息

| 字段名 | 含义 | 备注 |
|--------|------|------|
| **fid** | 租户ID | 关联 t_ocm_order_header.ftenant |
| **fname** | 租户名称 | **用于搜索** |
| fenable | 使用状态 | '0' 禁用 / '1' 可用 |
| fcontact_name | 联系人 | - |
| fcontact_phone | 联系电话 | - |

---

## 表关系

```
t_ocm_order_header.fid (1) ←→ (N) t_ocm_order_lines.fentryid
t_ocm_order_header.ftenant (N) ←→ (1) t_ocm_tenant.fid
t_ocm_kbc_order_settle ← (复杂关联，不推荐) → t_ocm_order_header
```

**JOIN 建议**：
- 订单 + 产品明细：`INNER JOIN` (如果产品明细表有数据)
- 订单 + 租户：`LEFT JOIN` (租户信息可能缺失)

---

## 枚举值

### fbiz_type（订单类别）

| 值 | 含义 | 是否付费 |
|----|------|---------|
| **Standard** | 标准订单 | ✅ 付费 |
| Special | 特批订单 | ❌ 免费 |
| Free | 试用订单 | ❌ 免费 |

### fbusiness_type（业务类型）

| 值 | 含义 | 是否计入营收 |
|----|------|-------------|
| New | 新购 | ✅ 是 |
| Renew | 续费 | ✅ 是 |
| Add | 加购 | ✅ 是 |
| Return | 退货 | ❌ 否（负数） |
| **Upgradation** | 升级 | ❌ **否（必须排除）** |

### fdelivery_status（交付状态）

| 值 | 含义 | 是否可结算 |
|----|------|----------|
| **已交付** | 已完成交付 | ✅ 是 |
| 待交付 | 尚未交付 | ❌ 否 |

### fbill_source（订单来源）

| 值 | 渠道 |
|----|------|
| 1 | 发票云直销 |
| 2 | 生态伙伴 |
| 3 | 营销伙伴 |
| 4 | 金蝶中国直销 |
| 5 | 金蝶中国分销 |
| 6 | 个人伙伴 |
| 7 | 发票云特批 |

---

## 关键业务规则

### 营收统计标准过滤

```sql
-- 订单表查询
WHERE fbiz_type = 'Standard'              -- 只统计标准付费订单
  AND fbusiness_type != 'Upgradation'     -- 排除升级订单（不计费）
  AND fbusiness_type != 'Return'          -- 排除退货（或单独统计）

-- 结算表查询
WHERE fdelivery_status = '已交付'          -- 只统计已交付订单
  AND fpost_date >= '开始时间'
```

---

## 常见查询场景

### 1. 按客户名查产品（最常用）

```sql
-- 直接在结算表搜索，无需 JOIN
SELECT
    fuse_customer AS 客户,
    fsale_product_name AS 产品,
    SUM(fprice_tax_amount) AS 总金额
FROM t_ocm_kbc_order_settle
WHERE fpost_date >= '2025-01-01'
  AND (fuse_customer LIKE '%关键字%' OR fsign_customer LIKE '%关键字%')
  AND fdelivery_status = '已交付'
GROUP BY fuse_customer, fsale_product_name;
```

### 2. 按租户查订单

```sql
-- 先查租户ID，再关联订单
SELECT h.fbillno, h.fcreatetime, h.ftotal_amount, t.fname
FROM t_ocm_order_header h
LEFT JOIN t_ocm_tenant t ON h.ftenant = t.fid
WHERE t.fname LIKE '%关键字%'
  AND h.fcreatetime >= '2025-01-01'
  AND h.fbiz_type = 'Standard';
```

### 3. 按时间统计订单

```sql
-- 按月汇总
SELECT
    DATE_TRUNC('month', fcreatetime) AS 月份,
    COUNT(*) AS 订单数,
    SUM(ftotal_amount) AS 总金额
FROM t_ocm_order_header
WHERE fcreatetime >= '2025-01-01'
  AND fbiz_type = 'Standard'
  AND fbusiness_type != 'Upgradation'
GROUP BY DATE_TRUNC('month', fcreatetime)
ORDER BY 月份;
```

---

## 数据完整性提示

1. **产品明细表(t_ocm_order_lines)经常无数据**
   - 优先用结算表(t_ocm_kbc_order_settle)查产品信息
   - 或用订单表(t_ocm_order_header.ftotal_amount)查金额

2. **结算表与订单表关联复杂**
   - 依赖 forder_source 字段判断关联方式
   - 不建议依赖关联，直接按客户名搜索结算表更简单

3. **租户信息可能缺失**
   - 订单关联租户时用 LEFT JOIN

---

## 输出要求

1. **展示生成的SQL** - 让用户了解查询逻辑

2. **结构化列表展示结果** - 使用清晰的列表格式（适配微信、云之家等聊天工具）
   ```
   【标题】

   ▪ 项目1
     • 字段1：值1
     • 字段2：值2

   ▪ 项目2
     • 字段1：值1
     • 字段2：值2

   ━━━━━━━━━━━━━━
   💰 汇总信息
   ```

3. **自然语言解释** - 说明查询思路、数据来源、业务含义

4. **复杂查询时说明过程（审计用）** - 如果经历多步探索、尝试多个查询或遇到问题，简要说明查询路径（包括每步SQL和结果）
