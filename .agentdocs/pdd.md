# 简历智能初筛系统 - 产品设计文档 (PDD)

## 一、信息架构

### 1.1 页面结构

```
简历智能初筛系统
├── Dashboard（仪表盘）
│   ├── 概览统计卡片
│   ├── 筛选结果分布（饼图）
│   ├── 城市排名（列表）
│   └── 职位排名（列表）
│
├── Resumes（简历列表）
│   ├── 筛选器（状态、职位、城市）
│   ├── 简历列表（表格）- 显示可解析的简历（PDF + DOCX）
│   ├── 上传简历
│   └── 简历详情弹窗
│
├── ManualReview（人工审核）
│   ├── 待审核列表（无法解析的简历）
│   ├── 编辑候选人信息表单
│   ├── 查看原始附件
│   └── 删除无效记录
│
├── Screening（筛选结果）
│   ├── 筛选器（状态、职位、城市）
│   ├── 结果列表（表格）
│   └── 评估详情
│
└── Jobs（岗位管理）
    ├── 岗位列表
    ├── 创建岗位
    └── 编辑岗位
```

### 1.2 数据流转

```
企业邮箱 → IMAP监听 → 下载附件 → 简历解析 → Agent评估 → 数据存储 → 前端展示
```

---

## 二、页面设计

### 2.1 Dashboard（仪表盘）

**布局**：
```
+--------------------------------------------------+
|  概览统计                                        |
|  +-----+  +-----+  +-----+  +-----+                 |
|  |总数 |  |通过 |  |待定 |  |拒绝 |                 |
|  +-----+  +-----+  +-----+  +-----+                 |
+--------------------------------------------------+
|  筛选结果分布          |  城市排名                  |
|  [饼图]               |  [列表]                   |
+--------------------------------------------------+
|  职位排名                                        |
|  [列表]                                         |
+--------------------------------------------------+
```

**数据指标**：
- 总简历数
- 可以发offer数（agent_score ≥ 70）
- 待定数（40 ≤ agent_score < 70）
- 不合格数（agent_score < 40）
- 通过率

### 2.2 Resumes（简历列表）

**功能说明**：显示所有可解析的简历（`raw_text > 100字符`）

**表格列**：
- 候选人姓名
- 联系方式（电话、邮箱）
- 学历
- 工作年限
- 技能标签（最多3个）
- 状态
- 操作（查看详情、删除）

### 2.3 ManualReview（人工审核）

**功能说明**：显示无法自动解析的简历（`raw_text <= 100字符`）

**表格列**：
- 候选人姓名
- 文件类型（PDF/DOCX）
- 文本长度
- 状态
- 操作（查看详情、编辑、删除）

**编辑表单字段**：
- 姓名（必填）
- 手机号
- 邮箱
- 学历（下拉选择）
- 工作年限（数字输入）
- 技能标签（逗号分隔）

### 2.4 Screening（筛选结果）

**表格列**：
- 候选人姓名
- 应聘职位
- Agent评分
- 筛选结果（PASS/REVIEW/REJECT）
- 学历等级（QS前50/100/200、985/211、双非）
- 技能标签（最多3个）
- 操作（查看详情）

**状态颜色**：
- PASS：绿色
- REVIEW：橙色
- REJECT：红色
- PENDING：灰色

### 2.4 Jobs（岗位管理）

**表格列**：
- 岗位名称
- 类别
- 是否启用
- Agent类型
- 操作（编辑、删除）

---

## 三、数据模型设计

### 3.1 核心数据表

#### resumes（简历表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| candidate_name | String | 候选人姓名 |
| phone | String | 电话 |
| email | String | 邮箱 |
| education | String | 学历 |
| education_level | String | 学历等级（QS前50/100/200、985、211、双非） |
| work_years | Integer | 工作年限 |
| skills | JSONB | 技能标签数组 |
| work_experience | JSONB | 工作经历数组 |
| project_experience | JSONB | 项目经历数组 |
| education_history | JSONB | 教育背景数组 |
| raw_text | Text | 简历原文 |
| file_path | String | 文件路径 |
| file_type | String | 文件类型（pdf/docx） |
| city | String | 城市 |
| job_category | String | 职位类别 |
| agent_score | Integer | Agent评分（0-100） |
| screening_status | String | 筛选状态（可以发offer/待定/不合格/pending） |
| status | String | 处理状态 |
| raw_text_length | Integer | 原始文本长度（用于判断是否需要人工审核） |

**筛选规则**：
- **可解析简历**：`raw_text_length > 100` → 显示在简历列表
- **需人工审核**：`raw_text_length <= 100` → 显示在人工审核页面

#### jobs（岗位表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| name | String | 岗位名称 |
| category | String | 岗位类别 |
| description | Text | 岗位描述 |
| required_skills | JSONB | 必备技能 |
| preferred_skills | JSONB | 加分技能 |
| agent_type | String | Agent类型（fastgpt/http） |
| agent_url | String | Agent URL |
| is_active | Boolean | 是否启用 |

#### screening_results（筛选结果表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| resume_id | UUID | 简历ID |
| job_id | UUID | 岗位ID |
| agent_score | Integer | Agent评分 |
| screening_result | String | 筛选结果（PASS/REVIEW/REJECT） |
| suggestion | Text | 评估建议 |

---

## 四、API接口设计

### 4.1 基础信息

- **Base URL**: `http://localhost:8000/api/v1`
- **认证方式**: JWT（待实现）
- **响应格式**: JSON

### 4.2 核心接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/resumes` | 获取简历列表 |
| GET | `/resumes/{id}` | 获取简历详情 |
| POST | `/resumes/upload` | 上传简历 |
| DELETE | `/resumes/{id}` | 删除简历 |
| GET | `/screening/results` | 获取筛选结果 |
| GET | `/statistics/dashboard` | 获取仪表盘统计 |
| GET | `/statistics/by-city` | 按城市统计 |
| GET | `/statistics/by-job` | 按职位统计 |
| GET | `/jobs` | 获取岗位列表 |
| POST | `/jobs` | 创建岗位 |
| PUT | `/jobs/{id}` | 更新岗位 |
| DELETE | `/jobs/{id}` | 删除岗位 |

### 4.3 接口响应示例

**获取仪表盘统计**：
```json
{
  "overview": {
    "total_resumes": 600,
    "pass_count": 34,
    "review_count": 3,
    "reject_count": 0,
    "pass_rate": 0.919,
    "avg_score": 76.5
  }
}
```

---

## 五、技术架构

### 5.1 技术栈

**后端**：
- FastAPI + Python 3.11+
- SQLAlchemy 2.0 + Alembic
- PostgreSQL 15
- Redis 7
- Celery（异步任务）

**前端**：
- React + TypeScript
- Ant Design 5
- Vite
- Axios

**部署**：
- Docker + Docker Compose

### 5.2 架构图

```
+------------------+      +------------------+      +------------------+
|   Nginx (Frontend)|      |  FastAPI (Backend) |      |  PostgreSQL (DB)  |
|      :3000        | <---> |      :8000        | <---> |      :5432        |
+------------------+      +------------------+      +------------------+
                                 |
                                 v
                        +------------------+      +------------------+
                        |  Redis (Cache)   |      |  Celery Worker    |
                        |      :6379        |      +  FastGPT Agent   |
                        +------------------+      +------------------+
```

### 5.3 外部集成

**FastGPT Agent**：
- API地址：`https://ai.cloudpense.com/api`
- 认证方式：API Key
- 超时时间：30秒
- 重试次数：3次

---

## 六、核心原则与约束

### 6.1 评分原则

> **核心原则**：所有简历评分必须通过外部Agent完成，系统不进行本地评分。

**允许的本地逻辑**：
- 数据解析（PDF、邮件解析）
- 数据提取（姓名、电话、技能等）
- 数据存储与展示
- 简单的字符串匹配（非评分用途）

**禁止的本地逻辑**：
- 任何形式的分数计算
- 技能匹配评分
- 学历评估打分
- 筛选结果分类判断

### 6.2 简历过滤原则

> **核心原则**：只保留有PDF附件+正文内容的简历。

**保留条件**（必须同时满足）：
- `file_type == 'pdf'`
- `pdf_path` 不为空
- `raw_text` 不为空且不为None

**删除条件**（任一满足即删除）：
- 无PDF附件
- 无正文内容
- 邮件正文类型

---

## 七、部署说明

### 7.1 环境要求

- Docker
- Docker Compose
- 8GB+ 内存

### 7.2 启动步骤

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 2. 启动服务
docker-compose up -d

# 3. 查看日志
docker-compose logs -f backend
```

### 7.3 访问地址

- **前端**: http://localhost:3000
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs

---

*文档版本: v1.0*
*创建日期: 2026-01-05*
