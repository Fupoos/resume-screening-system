# 前端使用说明

## 启动前端

### 方式1：Docker部署（推荐）

```bash
# 启��所有服务（包括前端）
docker-compose up -d

# 访问前端
http://localhost:3000
```

### 方式2：本地开发

```bash
# 进入前端目录
cd frontend

# 安装依赖（如果还没安装）
npm install

# 启动开发服务器
npm run dev

# 访问前端
http://localhost:5173
```

## 功能说明

### 1. 仪表盘 (`/dashboard`)
- 系统概览
- 统计数据
- 快速入口

### 2. 岗位管理 (`/jobs`) ⭐
- 查看预设的4种岗位（HR、软件、财务、销售）
- 新增自定义岗位
- 编辑岗位信息
- 删除岗位

### 3. 简历匹配 (`/match`) ⭐⭐⭐ 核心功能
**使用步骤**：
1. 输入候选人信息：
   - 姓名（必填）
   - 联系电话
   - 电子邮箱
   - 最高学历
   - 工作年限
   - 技能标签（输入��按回车添加）
2. 选择目标岗位
3. 点击"开始匹配"按钮
4. 查看匹配结果：
   - 总分（0-100）
   - 筛选结果（PASS/REVIEW/REJECT）
   - 分项得分（技能、经验、学历）
   - 匹配点列表 ✓
   - 不匹配点列表 ✗
   - 建议说明

### 4. 筛选结果 (`/screening`)
- 查看历史筛选记录
- 按岗位/结果筛选
- 查看详情

## 测试示例

### 示例1：Python工程师匹配

**输入**：
- 姓名：张三
- 学历：本科
- 工作年限：3年
- 技能：Python、FastAPI、React、MySQL、Docker
- 岗位：Python后端工程师

**预期结果**：
- 筛选结果：PASS
- 总分：约85分

### 示例2：HR专员匹配

**输入**：
- 姓名：李四
- 学历：本科
- 工作年限：2年
- 技能：招聘、培训、绩效管理、HRIS系统
- 岗位：HR专员

**预期结果**：
- 筛选结果：PASS
- 总分：约90分

### 示例3：技能不足的候选人

**输入**：
- 姓名：王五
- 学历：大专
- 工作年限：1年
- 技能：Excel、会计
- 岗位：财务专员

**预期结果**：
- 筛选结果：REVIEW 或 REJECT
- 总分：约40-50分

## 技术栈

- **React 18** - UI框架
- **TypeScript 5** - 类型安全
- **Vite** - 构建工具
- **Ant Design 5** - UI组件库
- **React Router v6** - 路由
- **Axios** - HTTP客户端

## 项目结构

```
frontend/
├── src/
│   ├── components/
│   │   └── Layout/
│   │       ├── MainLayout.tsx       # 主布局
│   │       └── MainLayout.css
│   ├── pages/
│   │   ├── Dashboard/               # 仪表盘
│   │   ├── Jobs/                    # 岗位管理
│   │   ├── Match/                   # 简历匹配
│   │   └── Screening/               # 筛选结果
│   ├── services/
│   │   └── api.ts                   # API封装
│   └── types/
│       ├── job.ts                   # 岗位类型
│       └── screening.ts             # 筛选类型
├── Dockerfile
├── nginx.conf
└── package.json
```

## 开发说明

### 添加新页面

1. 在 `src/pages/` 创建新页面组件
2. 在 `src/App.tsx` 添加路由
3. 在 `MainLayout.tsx` 添加菜单项

### API调用

所有API调用统一在 `src/services/api.ts` 中定义：

```typescript
// 获取岗位列表
import { getJobs } from '../../services/api';

const jobs = await getJobs();
```

### 类型定义

所有类型定义在 `src/types/` 目录下：

```typescript
import type { Job, MatchResult } from '../../types';
```

## 常见问题

### 1. 前端无法连接后端

**检查**：
- 后端是否启动：`docker-compose ps`
- API地址是否正确：`frontend/.env`
- 网络是否互通（Docker网络）

**解决方案**：
- Docker部署：使用服务名 `backend`
- 本地开发：使用 `http://localhost:8000`

### 2. 页面空白

**检查**：
- 浏览器控制台是否有错误
- 依赖是否安装完整
- 路由配置是否正确

### 3. 样式错乱

**检查**：
- Ant Design是否正确导入
- CSS是否正确加载

## 后续优化

- [ ] 添加用户认证
- [ ] 添加数据持久化
- [ ] 优化移动端适配
- [ ] 添加更多图表
- [ ] 添加导出功能
