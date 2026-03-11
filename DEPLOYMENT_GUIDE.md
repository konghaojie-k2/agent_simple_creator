# Market Service 部署指南

## 系统要求

| 项目 | 最低配置 | 推荐配置 |
|------|---------|---------|
| CPU | 2 核 | 4 核 |
| 内存 | 4GB | 8GB+ |
| 存储 | 20GB | 100GB+ |
| 系统 | Ubuntu 20.04+ / Windows 10+ / macOS 12+ | Ubuntu 22.04 LTS |

---

## 快速开始

### 1. 克隆代码

```bash
git clone https://github.com/konghaojie-k2/agent_simple_creator.git
cd agent_simple_creator
```

### 2. 后端部署

#### 使用 Docker（推荐）

```bash
cd backend

# 构建镜像
docker build -t market-service .

# 运行容器
docker run -d \
  --name market-service \
  -p 8000:8000 \
  -v ./market:/app/backend/market \
  -v ./data:/app/backend/data \
  market-service
```

#### 本地运行

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 运行服务
uvicorn src.agent_builder.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. 验证部署

```bash
# 检查服务健康
curl http://localhost:8000/health

# 检查技能列表
curl http://localhost:8000/api/market/skills
```

---

## 目录结构

```
market/
├── data/
│   ├── public/           # 公开资源
│   │   ├── datasets/
│   │   ├── documents/
│   │   └── skills/
│   ├── private/          # 私有资源
│   │   └── {user_id}/
│   │       ├── datasets/
│   │       ├── documents/
│   │       └── skills/
│   └── shared/           # 共享资源
│       ├── datasets/
│       ├── documents/
│       └── skills/
└── skills/               # 技能目录
    └── public/
```

---

## 配置说明

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `PORT` | 8000 | 服务端口 |
| `HOST` | 0.0.0.0 | 服务地址 |
| `JWT_SECRET` | - | JWT 密钥（生产环境必须修改） |
| `MARKET_DATA_DIR` | ./market/data | 数据目录 |
| `LOG_LEVEL` | INFO | 日志级别 |

### 配置文件

编辑 `backend/src/agent_builder/core/config.py`：

```python
class Settings(BaseSettings):
    # API 配置
    API_V1_STR: str = "/api"
    
    # 数据库
    DATABASE_URL: str = "sqlite+aiosqlite:///./market.db"
    
    # JWT
    JWT_SECRET: str = "your-secret-key"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30 * 24 * 60  # 30 days
    
    # Market 配置
    MARKET_DATA_DIR: str = "market/data"
```

---

## OpenClaw 集成

### 1. 安装 Lab Tools 插件

将 `lab-tools/` 目录复制到 OpenClaw 插件目录：

```bash
cp -r lab-tools ~/.openclaw/plugins/
```

### 2. 配置插件

在 OpenClaw 配置文件中添加：

```json
{
  "plugins": {
    "entries": {
      "lab-tools": {
        "enabled": true,
        "config": {
          "market_service_url": "http://localhost:8000"
        }
      }
    }
  }
}
```

### 3. 使用示例

```
Agent: "列出所有数据集"
Tool: market_list_datasets

Agent: "分析 sales_data 数据集"
Tool: market_analyze_dataset dataset_id="xxx"

Agent: "安装 python-skill"
Tool: market_install_skill skill_id="xxx"
```

---

## 功能列表

### 数据集模块
- 上传/下载数据集（CSV, JSON, Parquet）
- 数据分析（质量、schema、洞察）
- CRUD 操作

### 文档模块
- 上传/下载文档
- 文档分析

### 技能模块
- 浏览/搜索技能
- 安装/卸载技能
- 技能配置

### 权限管理
- 公开/私有/共享
- 文件夹级权限控制
- 用户授权

### 其他功能
- 版本管理
- 分类/标签
- 导入/导出
- 备份/恢复

---

## 维护

### 备份数据

```bash
# 备份 market 目录
tar -czvf market-backup-$(date +%Y%m%d).tar.gz market/
```

### 更新服务

```bash
# 拉取最新代码
git pull

# 重新构建
docker build -t market-service .

# 重启服务
docker-compose restart
```

### 日志查看

```bash
# Docker 日志
docker logs -f market-service

# 本地运行日志
tail -f logs/market.log
```

---

## 常见问题

### Q: 服务启动失败？
A: 检查端口是否被占用：`lsof -i :8000`

### Q: 上传文件失败？
A: 检查目录权限：`chmod -R 755 market/`

### Q: 权限检查失败？
A: 确认 JWT_TOKEN 正确配置

---

## API 文档

启动服务后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

*最后更新: 2024-03-11*
