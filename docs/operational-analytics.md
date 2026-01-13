# Operational Analytics Skill

运营分析 Agent 技能，用于查询和分析 EOP（Enterprise Operation Platform，运营平台）数据库。

## 功能概述

这个 skill 为 Claude Agent 提供了查询和分析发票云运营数据的能力，支持：

- ✅ **数据查询** - 根据自然语言生成 SQL 并执行，返回订单、租户等数据
- ✅ **数据统计** - 按时间、产品、租户等维度进行聚合统计
- ✅ **趋势分析** - 按日/周/月/年聚合，分析营收和订单趋势
- ✅ **报表生成** - 生成订单报表、营收报表、租户分析报表

## 快速开始

### 1. 环境配置

确保 `.env` 文件包含以下配置：

```bash
# PostgreSQL 数据库连接
POSTGRES_HOST=bj-postgres-68aob3ms.sql.tencentcdb.com
POSTGRES_PORT=22898
POSTGRES_DATABASE=postgres
POSTGRES_USER=agent_eop
POSTGRES_PASSWORD=Fapiaoyun@2026

# 查询超时（秒）
POSTGRES_QUERY_TIMEOUT=60

# 允许的表（逗号分隔）
POSTGRES_ALLOWED_TABLES=t_ocm_kbc_order_settle,t_ocm_order_header,t_ocm_order_lines,t_ocm_tenant
```

### 2. 安装依赖

```bash
source .venv/bin/activate
pip install asyncpg>=0.29.0
```

### 3. 测试连接

```bash
python3 -c "
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def test():
    conn = await asyncpg.connect(
        host=os.getenv('POSTGRES_HOST'),
        port=int(os.getenv('POSTGRES_PORT')),
        database=os.getenv('POSTGRES_DATABASE'),
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD')
    )
    version = await conn.fetchval('SELECT version()')
    print(f'✅ Connected: {version}')
    await conn.close()

asyncio.run(test())
"
```

### 4. 使用 Skill

#### 通过 API

```bash
curl -X POST http://localhost:9090/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "admin",
    "prompt": "查询2026年1月的订单数量",
    "skill": "operational-analytics",
    "language": "中文"
  }'
```

#### 通过 CLI

```bash
source .venv/bin/activate
python cli.py

# 在 CLI 中输入查询：
> 查询2026年1月的订单
> 统计各业务类型的订单占比
> 按月统计2025年的营收趋势
```

## 数据库表结构

### 核心表

| 表名 | 中文名 | 记录数 | 主要用途 |
|------|--------|--------|---------|
| t_ocm_kbc_order_settle | 销售出库单 | 107,038 | 结算、付款查询 |
| t_ocm_order_header | 交易订单 | 109,475 | 订单主表 |
| t_ocm_order_lines | 产品订单 | 114,532 | 订单明细 |
| t_ocm_tenant | 租户表 | 35,631 | 租户信息 |

### 表关系

```
t_ocm_order_header (订单主表)
    ├─→ t_ocm_order_lines (1:N) - 产品明细
    ├─→ t_ocm_tenant (N:1) - 租户信息
    └─→ t_ocm_kbc_order_settle - 结算单
```

详细表结构参见：[references/schema.md](./references/schema.md)

## 使用示例

### 示例1：查询订单

**用户问题**："查询2026年1月的新购订单"

**Skill 执行**：
1. 识别时间范围：2026-01-01 至 2026-02-01
2. 识别业务类型：New（新购）
3. 生成并执行 SQL
4. 返回 Markdown 表格结果

### 示例2：统计营收

**用户问题**："按月统计2025年的营收趋势"

**Skill 执行**：
1. 使用 t_ocm_kbc_order_settle 表
2. 按 fpost_date 聚合（按月）
3. 过滤：fdelivery_status = '已交付'
4. 返回趋势数据

### 示例3：租户分析

**用户问题**："统计各租户的订单数量"

**Skill 执行**：
1. JOIN t_ocm_order_header 和 t_ocm_tenant
2. GROUP BY 租户
3. COUNT 订单数
4. 按订单数排序

## 文档结构

```
operational-analytics/
├── SKILL.md                    # 执行流程和规范（核心文档）
├── README.md                   # 本文档
├── DIRECTORY_MAP.md            # 快速导航指南
├── references/
│   ├── schema.md               # 表结构和字段说明
│   ├── relationships.md        # 表关系和 JOIN 模式
│   └── field_enums.md          # 枚举值详细说明
└── scripts/
    ├── __init__.py
    ├── db_connector.py         # 数据库连接工具
    ├── query_executor.py       # SQL 执行器
    └── result_formatter.py     # 结果格式化
```

## 安全机制

### SQL 安全检查

- ✅ 只允许 SELECT 查询
- ✅ 表白名单（4个核心表）
- ✅ 关键词黑名单（DROP, DELETE, UPDATE, INSERT 等）
- ✅ 禁止多条语句
- ✅ 查询超时保护（60秒）

### 表白名单管理

通过环境变量 `POSTGRES_ALLOWED_TABLES` 配置，便于扩展：

```bash
# 添加新表只需修改此配置
POSTGRES_ALLOWED_TABLES=table1,table2,table3,new_table
```

## 常见问题

### Q1: 如何添加新表？

**答**：修改 `.env` 中的 `POSTGRES_ALLOWED_TABLES`，添加新表名（逗号分隔），然后重启服务。

```bash
# 添加 t_ocm_payment 表
POSTGRES_ALLOWED_TABLES=t_ocm_kbc_order_settle,t_ocm_order_header,t_ocm_order_lines,t_ocm_tenant,t_ocm_payment
```

同时更新文档：
- `references/schema.md` - 添加表结构
- `references/relationships.md` - 添加关联关系（如有）

### Q2: 查询超时怎么办？

**答**：
1. 添加时间范围限制（如最近 30 天）
2. 添加其他过滤条件缩小范围
3. 增加 `POSTGRES_QUERY_TIMEOUT` 配置值
4. 添加 LIMIT 子句限制返回行数

### Q3: 如何理解枚举值？

**答**：查看 `references/field_enums.md`，包含所有枚举字段的详细说明：
- fbusiness_type：业务类型（New/Renew/Add/Return/Upgradation）
- fbiz_type：订单类别（Standard/Special/Free）
- fdelivery_status：交付状态（已交付/待交付）

### Q4: 营收统计不准确？

**答**：检查是否正确过滤：
```sql
-- 营收统计必须过滤
WHERE fbiz_type = 'Standard'           -- 只统计付费订单
  AND fbusiness_type != 'Upgradation'  -- 过滤升级订单
  AND fdelivery_status = '已交付'      -- 只统计已交付（结算表）
```

### Q5: 如何查看 SQL 执行过程？

**答**：Skill 会自动展示生成的 SQL：
```
<sql>
SELECT ...
FROM ...
WHERE ...
</sql>
```
用户可以查看 SQL 验证查询逻辑的正确性。

## 性能优化

### 查询优化建议

1. **添加时间范围** - 避免全表扫描
   ```sql
   WHERE fcreatetime >= '2025-01-01'  -- 好
   WHERE fcreatetime IS NOT NULL      -- 差
   ```

2. **使用 LIMIT** - 限制返回行数
   ```sql
   LIMIT 100  -- 明细查询
   ```

3. **避免 SELECT *** - 明确字段
   ```sql
   SELECT fbillno, fcreatetime  -- 好
   SELECT *                     -- 差
   ```

4. **合理使用索引** - 时间字段通常有索引
   ```sql
   WHERE fcreatetime >= '2025-01-01'         -- 可用索引
   WHERE DATE(fcreatetime) = '2025-01-01'    -- 无法用索引
   ```

## 维护和扩展

### 添加新查询模板

编辑 `SKILL.md` 的 "常见查询模式" 部分，添加新的查询场景和 SQL 模板。

### 更新表结构文档

当数据库表结构变化时，更新相应文档：
- `references/schema.md` - 表结构变更
- `references/relationships.md` - 关系变更
- `references/field_enums.md` - 枚举值变更

### 监控查询性能

查看日志中的查询执行时间：
```bash
tail -f logs/app.log | grep "Query executed"
```

## 故障排查

### 连接失败

```bash
# 1. 测试网络连通性
ping bj-postgres-68aob3ms.sql.tencentcdb.com

# 2. 测试端口
telnet bj-postgres-68aob3ms.sql.tencentcdb.com 22898

# 3. 检查凭证
cat .env | grep POSTGRES
```

### SQL 执行失败

1. 查看错误信息
2. 检查字段名拼写（参考 schema.md）
3. 检查表名是否正确
4. 验证 SQL 语法

### 结果不符合预期

1. 检查过滤条件（特别是 Upgradation 和 fdelivery_status）
2. 验证时间范围
3. 检查 JOIN 类型（INNER vs LEFT）
4. 确认枚举值含义（参考 field_enums.md）

## 贡献指南

改进此 skill：
1. 添加新的查询模式到 SKILL.md
2. 完善文档说明
3. 优化 SQL 查询性能
4. 添加更多查询示例

## 许可证

内部使用，遵循公司数据安全政策。

## 联系方式

遇到问题请联系：
- 技术支持：[内部支持渠道]
- 文档问题：[文档维护团队]

---

**版本**：1.0.0
**最后更新**：2026-01-12
**维护者**：AI Team
