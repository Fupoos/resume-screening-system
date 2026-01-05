# 简历智能初筛系统 - 前端

基于 React + TypeScript + Vite + Ant Design 的前端管理界面。

## 技术栈

- **框架**: React 18
- **语言**: TypeScript 5
- **构建工具**: Vite
- **UI组件库**: Ant Design 5
- **HTTP客户端**: Axios
- **路由**: React Router v6

## 页面列表

- **Dashboard** - 数据概览仪表盘
- **Resumes** - 简历列表和详情
- **Screening** - 筛选结果展示
- **Jobs** - 岗位管理

## 快速开始

### 安装依赖

```bash
npm install
```

### 启动开发服务器

```bash
npm run dev
```

访问 http://localhost:3000

### 构建生产版本

```bash
npm run build
```

### 预览生产构建

```bash
npm run preview
```

## 项目结构

```
frontend/
├── src/
│   ├── pages/          # 页面组件
│   │   ├── Dashboard/
│   │   ├── Resumes/
│   │   ├── Screening/
│   │   └── Jobs/
│   ├── components/     # 通用组件
│   ├── services/       # API调用
│   ├── types/          # TypeScript类型定义
│   ├── App.tsx
│   └── main.tsx
├── package.json
├── tsconfig.json
└── vite.config.ts
```

## API 配置

API 地址配置在 `src/services/api.ts`：

```typescript
const API_BASE_URL = 'http://localhost:8000/api/v1';
```

## 开发注意事项

1. **API 跨域**: 开发环境需要后端运行在 http://localhost:8000
2. **类型定义**: 所有 API 响应类型定义在 `src/types/` 目录
3. **组件规范**: 使用函数组件 + Hooks

## 可用脚本

- `npm run dev` - 启动开发服务器
- `npm run build` - 构建生产版本
- `npm run preview` - 预览生产构建
- `npm run lint` - 运行 ESLint
