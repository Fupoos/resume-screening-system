# 快速启动指南

## 一、启动后端服务

```bash
# 1. 进入项目目录
cd /Users/kevin/Desktop/resume-screening-system

# 2. 启动所有Docker服务
docker-compose up -d

# 3. 查看服务状态
docker-compose ps

# 4. 查看后端日志（确认启动成功）
docker-compose logs -f backend
```

看到以下信息表示启动成功：
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## 二、访问API文档

在浏览器打开：http://localhost:8000/docs

你会看到Swagger UI界面，可以测试所有API。

## 三、运行测试脚本

```bash
# 确保已安装requests库
pip install requests

# 运行测试脚本（注意：测试的是已废弃的API，仅作参考）
python test_api.py
```

## 四、手动测试API

### 1. 获取筛选结果

```bash
curl http://localhost:8000/api/v1/screening/results
```

### 2. 获取简历列表

```bash
curl http://localhost:8000/api/v1/resumes/
```

## 五、查看日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 只查看后端日志
docker-compose logs -f backend

# 只查看Celery日志
docker-compose logs -f celery

# 查看数据库日志
docker-compose logs -f db
```

## 六、停止服务

```bash
# 停止所有服务
docker-compose down

# 停止并删除数据卷（⚠️ 会清空数据库数据）
docker-compose down -v
```

## 七、常用问题排查

### 1. 端口冲突

如果8000端口被占用，修改docker-compose.yml：

```yaml
backend:
  ports:
    - "8001:8000"  # 改为8001端口
```

### 2. 容器启动失败

查看详细日志：
```bash
docker-compose logs backend
```

### 3. 重新构建镜像

```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## 八、预设岗位ID

系统预设4种岗位，可以直接使用：

| 岗位 | ID |
|------|-----|
| HR专员 | 00000000-0000-0000-0000-000000000001 |
| Python后端工程师 | 00000000-0000-0000-0000-000000000002 |
| 财务专员 | 00000000-0000-0000-0000-000000000003 |
| 销售代表 | 00000000-0000-0000-0000-000000000004 |

## 九、下一步

当前已完成核心后端功能，接下来可以：

1. **配置邮箱监听**
   - 在.env中配置企业邮箱信息
   - 启动Celery任务

2. **开发前端界面**
   - React + TypeScript + Ant Design
   - 岗位管理页面
   - 简历列表页面
   - 匹配结果展示

3. **数据库集成**
   - 运行Alembic迁移
   - 实现数据持久化

4. **用户认证**
   - JWT登录系统
   - 权限管理

## 十、技术支持

- 查看README.md了解更多信息
- 访问API文档: http://localhost:8000/docs
- 邮箱: es1@cloudpense.com
