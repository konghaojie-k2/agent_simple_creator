# Agent Simple Creator - 任务规划

> 更新时间: 2026-03-05

## 当前任务: 素材市场架构 (2026-03-05)

### 目标
构建以素材为中心的市场架构，实验引用素材而非拥有素材

---

## 开发路线图

```
Phase 1: 本地素材市场（当前优先级）
├── 1.1 Data Market (数据集市场)
├── 1.2 Skill Market (技能市场) - 已有基础
├── 1.3 Doc Market (文档模板市场) - 已有基础
└── 1.4 实验引用素材

Phase 2: 外部应用整合（后期规划）
├── 2.1 外部数据源接入 (HuggingFace等)
├── 2.2 外部技能服务接入
└── 2.3 MCP 服务化
```

---

## Phase 1: 本地素材市场

### 1.1 Data Market (数据集市场)

#### 后端实现
- [x] 创建数据模型 `Dataset`
  - id, name, description, type, schema
  - user_id, created_at, updated_at
  - tags, row_count, metadata
- [x] 创建 `MarketService` - 素材市场服务
  - `create_dataset()` - 创建数据集
  - `list_datasets()` - 列出数据集
  - `get_dataset()` - 获取数据集
  - `update_dataset()` - 更新数据集
  - `delete_dataset()` - 删除数据集
- [x] 创建 API 路由 `/api/market/datasets`
- [ ] 创建文件系统存储 `workspaces/{user_id}/data/{dataset_id}/`

#### 前端实现
- [x] 数据集列表页 `/markets/data`
- [ ] 数据集详情页 `/markets/data/[id]`
- [x] 数据集创建页 `/markets/data/new`

#### 文件结构
```
workspaces/{user_id}/data/{dataset_id}/
├── metadata.json
├── data.csv|json
└── README.md
```

---

### 1.2 Skill Market (技能市场)

#### 现有基础
- [x] `./skills/` - 全局共享技能
- [x] `AgentSkillSystem` - 技能加载系统
- [x] `SkillLoader` - 技能解析

#### 后端实现
- [x] 创建 `Skill` 数据模型
- [x] 创建 `SkillService` 服务
- [x] 创建技能 API `/api/market/skills`

#### 前端实现
- [x] 技能市场列表页 `/markets/skills`
- [ ] 技能详情页 `/markets/skills/[id]`
- [x] 技能创建页 `/markets/skills/new`

---

### 1.3 Doc Market (文档模板市场)

#### 现有基础
- [x] `ExperimentTemplate` - 实验模板模型
- [x] `/api/templates` - 模板 API

#### 待实现
- [ ] 通用模板支持（非仅实验模板）
- [ ] 模板市场前端页 `/markets/templates`
- [ ] 模板分类/标签系统

---

### 1.4 实验引用素材 + 背景信息

#### 数据库变更（混合模式）

```python
class Experiment:
    # ==================== 基础信息 ====================
    name: str                     # 实验名称
    description: str              # 简短描述

    # ==================== 背景信息（混合模式） ====================

    # 方式一：轻量级（简单实验）- 直接填写
    requirements: str             # 具体需求说明
    background: str              # 背景信息

    # 方式二：引用文档（复杂实验）
    doc_ids: List[str] = []      # 引用的文档
    data_ids: List[str] = []     # 引用的数据集
    skill_ids: List[str] = []    # 需要的技能
    template_id: str = None      # 使用的模板
```

#### 设计原则

| 场景 | 方式 |
|------|------|
| 简单实验 | 直接填写 requirements / background |
| 复杂实验 | 引用 doc_ids / data_ids / skill_ids |

#### 后端实现
- [x] 更新 `Experiment` 模型（添加 requirements, background, doc_ids）
- [x] 更新 Pydantic schemas
- [x] 修改实验创建 API，支持两种模式
- [ ] 实验执行时加载引用的素材

#### 前端实现
- [x] 创建实验时填写背景信息（requirements / background）
- [x] 创建实验时选择引用的文档（doc_ids）
- [x] 创建实验时选择数据集（data_ids）
- [x] 创建实验时选择技能（skill_ids）
- [x] 实验详情页显示背景信息和引用素材

---

## Phase 2: 外部应用整合（后期规划）

### 2.1 外部数据源接入

- [ ] MCP Server 配置支持外部数据 API
- [ ] HuggingFace Datasets 集成
- [ ] 自定义数据源配置

### 2.2 外部技能服务

- [ ] 技能市场 API 标准化
- [ ] 外部技能同步机制
- [ ] 技能版本管理

### 2.3 MCP 服务化

- [ ] 通用 MCP 工具封装
- [ ] MCP 服务注册与管理
- [ ] MCP 工具发现与加载

---

## 已完成任务

### ✅ 实验场 (Experiment Arena) - 之前完成
- [x] Experiment 模型和服务
- [x] ExperimentTemplate 模板系统
- [x] ExperimentExperience 经验库
- [x] 实验执行引擎 (Sense-Plan-Act-Reflect)
- [x] 前端实验界面
- [x] 多 Agent 协作支持

### ✅ 记忆系统架构
- [x] UserSoul 模型
- [x] Agent Identity 字段
- [x] Agent Capabilities 字段
- [x] PromptBuilder 动态提示词
- [x] SOUL API

### ✅ 技能系统
- [x] 三级技能来源
- [x] 渐进式披露
- [x] 经验沉淀

---

## 关键文件

### 后端
- `backend/src/agent_builder/db/models.py` - 数据模型
- `backend/src/agent_builder/schemas/pydantic.py` - Pydantic schemas
- `backend/src/agent_builder/services/market_service.py` - 素材市场服务
- `backend/src/agent_builder/api/routes/markets.py` - 市场 API
- `backend/src/agent_builder/services/experiment_engine.py` - 实验引擎

### 前端
- `frontend/src/types/index.ts` - TypeScript 类型
- `frontend/src/lib/api.ts` - API 客户端
- `frontend/src/app/(dashboard)/markets/` - 市场页面

---

## 启动命令

```bash
# 后端
cd backend
uv pip install -e "C:\Users\17625\Documents\GitHub\my-auth"
uv run uvicorn src.agent_builder.main:app --reload --port 8000

# 前端
cd frontend
npm run dev
```

---

## API 端点 (规划)

### Data Market
- `POST /api/market/data` - 创建数据集
- `GET /api/market/data` - 列出数据集
- `GET /api/market/data/{id}` - 获取数据集详情
- `PUT /api/market/data/{id}` - 更新数据集
- `DELETE /api/market/data/{id}` - 删除数据集
- `POST /api/market/data/{id}/upload` - 上传数据文件

### Skill Market
- `POST /api/market/skills` - 创建技能
- `GET /api/market/skills` - 列出技能
- `GET /api/market/skills/{id}` - 获取技能详情
- `DELETE /api/market/skills/{id}` - 删除技能

### Doc Market
- `POST /api/market/templates` - 创建模板
- `GET /api/market/templates` - 列出模板
- `GET /api/market/templates/{id}` - 获取模板详情
- `DELETE /api/market/templates/{id}` - 删除模板

### Experiment (更新)
- `POST /api/experiments` - 创建实验（支持选择素材）
- `GET /api/experiments/{id}` - 实验详情（含引用素材）
