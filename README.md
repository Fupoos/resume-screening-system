# 简历智能初筛系统

基于 FastAPI + React 的简历智能初筛系统，支持从企业邮箱自动获取简历，并使用外部Agent进行智能评估。

## 系统功能

### 已实现功能
- ✅ **邮箱服务**: 支持企业邮箱IMAP连接，自动获取简历附件
- ✅ **简历解析**: 支持PDF和DOCX格式，提取候选人关键信息
- ✅ **Agent评估**: 外部Agent（FastGPT）进行简历评分和筛选
- ✅ **API接口**: RESTful API，支持岗位管理和简历筛选
- ✅ **前端界面**: React + TypeScript + Ant Design 管理界面

### 待开发功能
- ⏳ **更多Agent集成**: 扩展到更多职位类别的Agent
- ⏳ **用户认证**: JWT登录系统
- ⏳ **通知功能**: 企业微信/邮件通知

## 技术栈

### 后端
- FastAPI 0.109.0
- SQLAlchemy 2.0.25
- Celery 5.3.4
- PostgreSQL 15
- Redis 7

### 前端
- React 18
- TypeScript 5
- Ant Design 5
- Axios

### 部署
- Docker + Docker Compose

## 快速开始

### 前置要求
- Docker
- Docker Compose
- Python 3.9+

### 1. 启动服务

```bash
# 进入项目目录
cd Desktop/resume-screening-system

# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f backend
```

### 2. 访问API文档

启动成功后，访问：
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

### 3. 测试API

#### 3.1 获取岗位列表

```bash
curl http://localhost:8000/api/v1/jobs/
```

系统预设4种岗位：
- HR专员 (ID: 00000000-0000-0000-0000-000000000001)
- Python后端工程师 (ID: 00000000-0000-0000-0000-000000000002)
- 财务专员 (ID: 00000000-0000-0000-0000-000000000003)
- 销售代表 (ID: 00000000-0000-0000-0000-000000000004)

#### 3.2 获取筛选结果

```bash
curl http://localhost:8000/api/v1/screening/results
```

响应示例：
```json
{
  "total": 10,
  "results": [
    {
      "id": "uuid",
      "candidate_name": "张三",
      "job_name": "实施顾问",
      "agent_score": 75,
      "screening_result": "PASS",
      "evaluated": true
    }
  ]
}
```

## 项目结构

```
resume-screening-system/
├── backend/                    # FastAPI后端
│   ├── app/
│   │   ├── main.py            # FastAPI入口
│   │   ├── core/              # 核心配置
│   │   ├── models/            # 数据库模型
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── api/v1/            # API路由
│   │   ├── services/          # 业务逻辑
│   │   └── tasks/             # Celery任务
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                   # React前端（待开发）
├── docker-compose.yml
├── .env.example
└── README.md
```

## 核心功能说明

### 1. 邮箱监听

系统会自动监听配置的企业邮箱，每隔5分钟检查新邮件：
- 筛选包含"简历"或"应聘"关键词的邮件
- 下载PDF/DOCX格式的附件
- 将已处理的邮件移动到"已处理"文件夹

### 2. 简历解析

支持解析PDF和DOCX格式的简历，提取：
- **基本信息**: 姓名、电话、邮箱
- **教育背景**: 学校、学历、专业
- **工作经历**: 公司、职位、时长
- **项目经历**: 项目名称、角色、技术栈
- **技能标签**: 使用jieba分词提取技能关键词

### 3. 外部Agent评估

使用外部Agent（FastGPT）进行简历评分：

#### 评分标准
- **90-100分**: 完全匹配，可以进入面试
- **70-89分**: 基本匹配，可以考虑面试
- **50-69分**: 部分匹配，需要进一步评估
- **0-49分**: 不匹配，不建议面试

#### 筛选结果
- **PASS**: Agent评分 ≥ 70
- **REVIEW**: 40 ≤ Agent评分 < 70
- **REJECT**: Agent评分 < 40

#### 支持的职位类别
目前支持通过Agent评估的职位：
- **实施顾问**: 已配置FastGPT Agent
- 更多职位类别开发中...

## 环境变量配置

复制 `.env.example` 为 `.env` 并修改：

```env
# 数据库配置
DATABASE_URL=postgresql+asyncpg://resume:resume123@db:5432/resume_screening

# Redis配置
REDIS_URL=redis://redis:6379/0

# JWT配置
SECRET_KEY=your-secret-key-change-in-production
ENCRYPTION_KEY=your-encryption-key-32-bytes-long-change

# 邮箱配置
DEMO_EMAIL=your_email@example.com
DEMO_AUTH_CODE=your_auth_code
```

## 常用命令

```bash
# 启动所有服务
docker-compose up -d

# 停止所有服务
docker-compose down

# 查看后端日志
docker-compose logs -f backend

# 查看Celery日志
docker-compose logs -f celery

# 进入后端容器
docker-compose exec backend bash

# 运行数据库迁移
docker-compose exec backend alembic upgrade head

# 重启服务
docker-compose restart backend
```

## API文档

详细的API文档请访问: http://localhost:8000/docs

### 主要端点

- `GET /` - 根路径
- `GET /health` - 健康检查
- `GET /api/v1/jobs/` - 获取岗位列表
- `GET /api/v1/jobs/{id}` - 获取岗位详情
- `POST /api/v1/jobs/` - 创建岗位
- `PUT /api/v1/jobs/{id}` - 更新岗位
- `DELETE /api/v1/jobs/{id}` - 删除岗位
- `GET /api/v1/screening/results` - 获取筛选结果列表
- `GET /api/v1/resumes/` - 获取简历列表

## 开发进度

### 已完成 ✅
- [x] 项目结构搭建
- [x] Docker配置
- [x] 数据库模型设计（PostgreSQL）
- [x] 邮箱服务（IMAP连接）
- [x] 简历解析服务（PDF/DOCX）
- [x] 外部Agent集成（FastGPT）
- [x] 核心API接口
- [x] React前端界面

### 进行中 🚧
- [ ] Celery异步任务集成

### 待开发 📋
- [ ] 用户认证系统
- [ ] 邮箱配置管理
- [ ] 通知功能

## 注意事项

1. **邮箱配置**: 企业邮箱需要使用授权码而非登录密码
2. **文件格式**: 目前只支持PDF和DOCX格式的简历
3. **Agent评估**: 所有评分通过外部Agent（FastGPT）完成，本地无评分逻辑
4. **简历保留**: 只保留有PDF附件+正文的简历

## 常见问题

### 1. 邮箱连接失败

检查以下配置：
- 邮箱地址是否正确
- 授权码是否正确（非登录密码）
- IMAP服务器和端口是否正确

### 2. Docker容器启动失败

检查Docker是否正常运行：
```bash
docker ps
docker-compose logs
```

### 3. 简历解析失败

确保：
- 文件格式为PDF或DOCX
- 文件没有损坏
- 安装了必要的依赖包（pdfplumber、python-docx）

## 后续计划

- [ ] 实现完整的前端界面
- [ ] 集成数据库持久化
- [ ] 添加用户认证和权限管理
- [ ] 实现操作日志
- [ ] 添加企业微信通知
- [ ] 优化简历解析算法
- [ ] 支持更多简历格式

## 联系方式

如有问题，请通过以下方式联系：
- 邮箱: es1@cloudpense.com
- 项目地址: /Users/kevin/Desktop/resume-screening-system

## 许可证

MIT License
