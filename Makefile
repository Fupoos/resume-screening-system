# 简历筛选系统 - Makefile
# 常用命令快捷方式

.PHONY: help build up down restart logs security-scan lint test clean install

help:  ## 显示帮助信息
	@echo "简历筛选系统 - 可用命令："
	@echo ""
	@echo "  build         - 构建Docker镜像"
	@echo "  up            - 启动所有服务"
	@echo "  down          - 停止所有服务"
	@echo "  restart       - 重启所有服务"
	@echo "  logs          - 查看服务日志"
	@echo "  install       - 安装后端依赖"
	@echo "  security-scan - 安全漏洞扫描"
	@echo "  lint          - 代码质量检查"
	@echo "  test          - 运行测试"
	@echo "  clean         - 清理容器和数据卷"

build:  ## 构建Docker镜像
	docker-compose build

up:  ## 启动所有服务
	docker-compose up -d

down:  ## 停止所有服务
	docker-compose down

restart:  ## 重启所有服务
	docker-compose restart

logs:  ## 查看服务日志
	docker-compose logs -f backend celery

install:  ## 安装后端依赖
	@echo "=== 安装Python依赖 ==="
	cd backend && pip install -r requirements.txt

security-scan:  ## 安全漏洞扫描
	@echo "=== 依赖漏洞扫描 ==="
	cd backend && pip-audit || true
	@echo ""
	@echo "=== 代码安全扫描 ==="
	cd backend && bandit -r app/ -f screen -ll || true

lint:  ## 代码质量检查
	@echo "=== Python代码检查 ==="
	cd backend && pylint app/ || true

test:  ## 运行测试
	@echo "=== 运行单元测试 ==="
	cd backend && pytest tests/ -v || true

clean:  ## 清理容器和数据卷
	docker-compose down -v
	docker system prune -f
