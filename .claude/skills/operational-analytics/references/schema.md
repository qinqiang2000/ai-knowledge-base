# EOP数据库表结构详细说明

本文档详细说明EOP（Enterprise Operation Platform，运营平台）的4个核心表结构。

## 概览

| 表名 | 中文名 | 主要用途 | 默认时间字段 |
|------|--------|---------|-------------|
| t_ocm_kbc_order_settle | 销售出库单 | 结算、付款查询 | fpost_date |
| t_ocm_order_header | 交易订单 | 订单主表 | fcreatetime |
| t_ocm_order_lines | 产品订单 | 订单明细 | - |
| t_ocm_tenant | 租户表 | 租户信息 | - |

---

## 1. t_ocm_kbc_order_settle（销售出库单）

### 用途
存储销售出库、结算、付款等业务数据。主要用于查询结算、收款信息及相关的客户及订单信息。

### 核心字段

| 字段名 | 字段备注 | 补充描述 |
|--------|----------|---------|
| fbillno | 单据编号 | - |
| fmodifytime | 更新时间 | - |
| fcreatetime | 创建时间 | - |
| fkbc_settle_billno | 关联单据编号 | 如果forder_source='金蝶中国'，则本字段关联到[交易订单]的fthird_party_billno，然后用fproduct_serial_no关联到[交易订单]所包含的[产品订单]的fproduct_serial_no；如果forder_source='运营后台'，则本字段直接关联到[产品订单]的fproduct_billno |
| fproduct_serial_no | 产品序列号 | - |
| fsale_product_name | 销售产品 | - |
| fversion_no | 版本号 | - |
| fsale_product_code | 销售产品编码 | - |
| fpost_date | 记账日期 | **默认用此字段作为时间轴**，表示订单创建时间 |
| fdelivery_status | 交付状态 | 表示订单是否已经交付，只有状态为"已交付"的才能结算，计算收款时需要过滤 |
| frenew_status | 续费状态 | - |
| fcontract_no | 合同编号 | - |
| fbusiness_date | 业务日期 | - |

### 枚举值

**fdelivery_status（交付状态）**：
- `已交付` - 已完成交付，可以结算
- `待交付` - 尚未交付
- 计算收款时需要过滤，只统计已交付的订单

### 查询示例

```sql
-- 按月统计已交付订单的营收
SELECT
    DATE_TRUNC('month', fpost_date) as month,
    COUNT(*) as order_count,
    SUM(famount) as total_revenue
FROM t_ocm_kbc_order_settle
WHERE fpost_date >= '2025-01-01'
  AND fdelivery_status = '已交付'
GROUP BY DATE_TRUNC('month', fpost_date)
ORDER BY month DESC;
```

---

## 2. t_ocm_order_header（交易订单）

### 用途
用于查询订单的销售金额及相关订单信息，销售金额表示客户支付的金额。交易订单是主表，与产品订单（t_ocm_order_lines）为一对多关系。

### 核心字段

| 字段名 | 字段备注 | 补充描述 |
|--------|----------|---------|
| fid | 主键ID | - |
| fbillno | 交易订单编号 | - |
| fbillstatus | 单据状态 | - |
| fauditdate | 审核日期 | - |
| fmodifytime | 修改时间 | - |
| fcreatetime | 创建时间 | **默认用这个字段作为时间轴** |
| fbusiness_type | 购买类型 | Add: 加购<br>New: 新购<br>Renew: 续费<br>Return: 退货<br>Upgradation: 升级（升级订单不属于有效订单，计算订单收款时要过滤） |
| fbiz_type | 订单类别 | Standard: 标准订单，表示付费的正式订单<br>Special: 特批订单，是不付费的经过审批的免费订单<br>Free: 免费的试用订单 |
| fcontract | 关联合同号 | - |
| ftenant | 租户 | 租户编码，可以用这个编码去租户表[t_ocm_tenant]查询租户名称 |
| fcontact_name | 联系人姓名 | - |
| fcontact_phone | 联系人电话 | - |
| fbill_source | 订单来源名称 | 1: 发票云直销<br>2: 生态伙伴<br>3: 营销伙伴<br>4: 金蝶中国直销<br>5: 金蝶中国分销<br>6: 个人伙伴<br>7: 发票云特批 |

### 业务类型（fbusiness_type）说明

| 值 | 中文 | 说明 | 是否计入营收 |
|----|------|------|-------------|
| New | 新购 | 首次购买 | ✅ 是 |
| Renew | 续费 | 续期购买 | ✅ 是 |
| Add | 加购 | 增加数量/模块 | ✅ 是 |
| Return | 退货 | 退款 | ❌ 否（负数） |
| Upgradation | 升级 | 版本升级 | ❌ 否（不单独计费，计算订单收款时要过滤） |

### 订单类型（fbiz_type）说明

| 值 | 说明 | 是否付费 |
|----|------|---------|
| Standard | 标准订单 | ✅ 付费的正式订单 |
| Special | 特批订单 | ❌ 不付费的经过审批的免费订单 |
| Free | 试用订单 | ❌ 免费试用 |

### 查询示例

```sql
-- 查询2026年1月的新购和续费订单
SELECT
    fbillno,
    fcreatetime,
    fbusiness_type,
    fbiz_type,
    ftenant
FROM t_ocm_order_header
WHERE fcreatetime >= '2026-01-01'
  AND fcreatetime < '2026-02-01'
  AND fbusiness_type IN ('New', 'Renew')
  AND fbiz_type = 'Standard'
ORDER BY fcreatetime DESC
LIMIT 100;
```

---

## 3. t_ocm_order_lines（产品订单）

### 用途
属于交易订单的明细，用于记录具体产品/权益信息。与交易订单（t_ocm_order_header）为多对一关系。

### 核心字段

| 字段名 | 字段备注 | 补充描述 |
|--------|----------|---------|
| fid | 主键ID | - |
| fentryid | 关联到交易订单id | 对应 t_ocm_order_header.fid |
| fproduct | 产品编码 | - |
| funit | 单位 | - |
| fsubscription_duration | 订阅权益时长 | - |
| fproduct_billno | 产品订单编号 | - |
| fprepaid_period | 订阅周期 | - |
| fquantity | 订购数量 | - |
| fnote | 备注 | - |
| funit_price | 单价 | - |
| ftax_price | 含税单价 | - |
| fdiscount_rate | 折扣率(%) | - |
| fdiscount_amount | 折扣额 | - |

### 查询示例

```sql
-- 查询某个订单的产品明细
SELECT
    l.fproduct,
    l.fproduct_billno,
    l.fquantity,
    l.funit_price,
    l.ftax_price,
    (l.fquantity * l.ftax_price) as total_amount
FROM t_ocm_order_lines l
WHERE l.fentryid = 123456  -- 交易订单ID
ORDER BY l.fid;
```

---

## 4. t_ocm_tenant（租户表）

### 用途
记录客户的基本信息。

### 核心字段

| 字段名 | 字段备注 | 补充描述 |
|--------|----------|---------|
| fid | 主键ID | 用于关联其他表单的租户编码 |
| fnumber | 租户编码 | - |
| fname | 租户名称 | **一般问租户时默认查询这个字段** |
| fenable | 使用状态 | 0: 禁用<br>1: 可用 |
| fcontact_phone | 联系人电话 | - |
| fcontact_name | 联系人名字 | - |
| fcontact_email | 联系人email | - |
| fclient_id | 客户端ID | - |
| fclient_secret | 客户端密钥 | - |
| fenc_key_aes128 | AES128加密密钥 | - |
| factivate_code | 全电客户端激活码 | - |
| factivate_code_time | 全电客户端激活时间 | - |

### 枚举值

**fenable（使用状态）**：
- `0` - 禁用
- `1` - 可用

### 查询示例

```sql
-- 查询可用的租户列表
SELECT
    fid,
    fnumber,
    fname,
    fcontact_name,
    fcontact_phone
FROM t_ocm_tenant
WHERE fenable = 1
ORDER BY fname
LIMIT 100;
```

---

## 常用查询场景

### 场景1：按时间范围查询订单

**使用表**：t_ocm_order_header
**时间字段**：fcreatetime
**示例**：查询2026年1月的订单

```sql
SELECT * FROM t_ocm_order_header
WHERE fcreatetime >= '2026-01-01'
  AND fcreatetime < '2026-02-01';
```

### 场景2：统计营收（结算数据）

**使用表**：t_ocm_kbc_order_settle
**时间字段**：fpost_date
**注意**：只统计已交付的订单（fdelivery_status = '已交付'）

```sql
SELECT
    DATE_TRUNC('month', fpost_date) as month,
    COUNT(*) as order_count
FROM t_ocm_kbc_order_settle
WHERE fdelivery_status = '已交付'
GROUP BY month;
```

### 场景3：按业务类型统计

**使用表**：t_ocm_order_header
**分组字段**：fbusiness_type
**注意**：Upgradation 类型不计入有效订单

```sql
SELECT
    fbusiness_type,
    COUNT(*) as count
FROM t_ocm_order_header
WHERE fbusiness_type != 'Upgradation'
GROUP BY fbusiness_type;
```

---

## 字段命名规范

EOP数据库字段遵循以下命名规范：

- **f** 开头：所有字段都以 `f` 开头（可能是 "field" 的缩写）
- **驼峰命名**：使用小写开头的驼峰命名（如 fcreatetime, fbillno）
- **常见前缀**：
  - `fbill*` - 单据相关（fbillno, fbillstatus）
  - `fcontact*` - 联系人相关（fcontact_name, fcontact_phone）
  - `f*_date / f*_time` - 时间相关（fpost_date, fcreatetime）

---

## 注意事项

1. **时间字段选择**：
   - 订单查询用 `t_ocm_order_header.fcreatetime`
   - 结算查询用 `t_ocm_kbc_order_settle.fpost_date`

2. **过滤无效数据**：
   - Upgradation 类型订单不计入营收统计
   - 未交付订单不计入结算统计
   - 非 Standard 类型订单可能是免费订单

3. **租户关联**：
   - 通过 `t_ocm_order_header.ftenant` 关联 `t_ocm_tenant.fid`
   - 显示租户名称用 `t_ocm_tenant.fname`

4. **订单关联**：
   - 订单主表用 `t_ocm_order_header`
   - 订单明细用 `t_ocm_order_lines`（通过 fentryid 关联）

详细的表关系和 JOIN 模式请参考 [relationships.md](./relationships.md)
