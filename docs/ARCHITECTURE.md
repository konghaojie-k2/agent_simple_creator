# Agent Simple Creator - 架构设计文档

> 更新时间: 2026-03-05

---

## 一、系统概述

Agent Simple Creator 是一个 AI Agent 创建平台，支持多 LLM 提供商（DeepSeek、Qwen、OpenAI）。

### 核心特性
- **多 Agent 管理**: 创建、配置、对话
- **实验场 (Experiment Arena)**: Agent 自主实验与学习
- **记忆系统**: 分层记忆架构（SOUL → Identity → Experience）
- **素材市场**: Data/Skill/Doc 三大市场

---

## 二、系统架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                Frontend                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Agents  │  │   Chat   │  │Experiments│  │Experiences│  │ Markets  │   │
│  │          │  │          │  │          │  │          │  │(Data/Skill│   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  │  /Doc)   │   │
│       │             │             │             │        └────┬─────┘   │
│       └─────────────┴─────────────┴─────────────┴─────────────┘          │
│                                     │                                       │
│                              ┌──────┴──────┐                               │
│                              │    API      │                               │
│                              │   Client    │                               │
│                              └──────┬──────┘                               │
└─────────────────────────────────────┼───────────────────────────────────────┘
                                      │
┌─────────────────────────────────────┼───────────────────────────────────────┐
│                                     │         Backend                      │
│  ┌──────────────────────────────────┴───────────────────────────────────┐  │
│  │                         API Layer (FastAPI)                          │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐ │  │
│  │  │ agents   │ │  chat    │ │experiments│ │  soul    │ │ markets │ │  │
│  │  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └───┬────┘ │  │
│  └───────┼────────────┼────────────┼────────────┼───────────┼──────┘  │
│          │            │            │            │           │          │
│  ┌───────┴────────────┴────────────┴────────────┴───────────┴──────┐  │
│  │                        Service Layer                                │  │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐    │  │
│  │  │LLM Service │ │Agent Service│ │ Experiment │ │   Market   │    │  │
│  │  │            │ │             │ │  Engine    │ │  Service   │    │  │
│  │  └────────────┘ └────────────┘ └────────────┘ └────────────┘    │  │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐    │  │
│  │  │ Experience │ │  Prompt    │ │   MCP      │ │   Code     │    │  │
│  │  │  Service   │ │  Builder   │ │  Manager   │ │  Sandbox   │    │  │
│  │  └────────────┘ └────────────┘ └────────────┘ └────────────┘    │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                     │                                       │
│  ┌──────────────────────────────────┴───────────────────────────────────┐  │
│  │                    Database Layer (SQLAlchemy + SQLite)               │  │
│  │  ┌────────┐ ┌────────┐ ┌──────────┐ ┌────────┐ ┌────────┐        │  │
│  │  │ Agent  │ │Experi- │ │Experience │ │UserSoul│ │  MCP   │        │  │
│  │  │        │ │ ment   │ │           │ │        │ │ Config │        │  │
│  │  └────────┘ └────────┘ └───────────┘ └────────┘ └────────┘        │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                     │                                       │
│  ┌──────────────────────────────────┴───────────────────────────────────┐  │
│  │                    File System (Workspaces)                          │  │
│  │  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐     │  │
│  │  │   Data Market   │ │  Skill Market   │ │  Doc Market     │     │  │
│  │  │   ./data/       │ │   ./skills/      │ │   ./templates/  │     │  │
│  │  └─────────────────┘ └─────────────────┘ └─────────────────┘     │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 三、数据库模型

### 核心实体关系

```
┌─────────────────┐       ┌─────────────────┐
│   UserSoul     │       │  LLMProvider    │
│  (用户级SOUL)   │       │  (LLM配置)       │
└────────┬────────┘       └────────┬────────┘
         │                          │
         │         ┌────────────────┴────────────────┐
         │         │             Agent              │
         │         │   (Agent + Identity +能力)     │
         │         └───────────────┬────────────────┘
         │                         │
    ┌────┴────────┐    ┌────────────┴────────────┐
    │            │    │            │              │
┌───┴────┐  ┌────┴───┐ ┌─────┴─────┐  ┌─────┴─────┐
│Session │  │Experiment│ │Experience │  │AgentSkill│
│(聊天)   │  │ (实验)   │ │ (经验)     │  │ (技能)   │
└────────┘  └─────────┘ └───────────┘  └──────────┘
```

### 主要数据表

| 表名 | 说明 | 关键字段 |
|------|------|----------|
| `agents` | Agent 配置 | identity, capabilities, prompt_config, system_prompt |
| `llm_providers` | LLM 提供商 | provider_type, api_base, api_key |
| `chat_sessions` | 聊天会话 | messages[] |
| `experiments` | 实验记录 | type, status, input_data, **data_ids**, **skill_ids**, **template_id** |
| `experiment_templates` | 实验模板 | template_config |
| `experiences` | 经验沉淀 | situation, action, result, lesson, status |
| `user_souls` | 用户级 SOUL | core_truths, boundaries, vibe, soul_content |
| `agent_skills` | Agent 技能库 | source_type, name, wrapper_template |
| `mcp_server_configs` | MCP 服务配置 | transport, command, args, env |

---

## 四、服务层架构

### 4.1 LLM Service

**职责**: 多 LLM 提供商集成

```python
class LLMService:
    # 支持的提供商
    - deepseek
    - qwen
    - openai
    - custom

    # 核心能力
    - chat_complete()      # 流式对话
    - embedding()           # 向量嵌入
```

### 4.2 Experiment Engine

**职责**: Agent 实验执行核心

```
┌─────────────────────────────────────────────────────────────┐
│                    Experiment Engine                        │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐ │
│  │  Sense  │ →  │  Plan   │ →  │   Act   │ →  │ Reflect │ │
│  │  感知   │    │  规划   │    │  执行   │    │  反思   │ │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘ │
│       ↑                                                      │
│       └──────────────────────────────────────────────────────┤
│              Tool Registry (25+ 内置工具)                     │
│              + 素材市场加载 (Data/Skill/Doc)                  │
└─────────────────────────────────────────────────────────────┘
```

**实验类型**:
- `skill_creation` - 技能创建
- `document_generation` - 报告生成
- `problem_solving` - 问题解决
- `data_analysis` - 数据分析
- `collaboration` - 多 Agent 协作

### 4.3 Skill System

**职责**: 技能管理与渐进式披露

```
┌─────────────────────────────────────────────────────────────┐
│                   三级技能来源                                │
│                                                              │
│  1. 共享技能 (./skills/)                                     │
│     └── 所有 Agent 可用                                       │
│                                                              │
│  2. Agent 专属 (workspaces/{user}/{agent}/skills/)         │
│     └── 仅该 Agent 可用                                       │
│                                                              │
│  3. 经验沉淀 (workspaces/{user}/{agent}/experiences/)       │
│     └── 实验中学习到的经验                                     │
└─────────────────────────────────────────────────────────────┘
```

**渐进式披露**:
- Level 1: 系统提示包含技能元数据（名称+描述）
- Level 2: `get_skill` 工具按需加载完整内容

### 4.4 Experience Service

**职责**: 经验管理与复用

```
Experience 生命周期:
┌─────────┐    ┌──────────┐    ┌───────────┐    ┌───────────┐
│  draft  │ →  │ verified │ →  │ applied   │ →  │deprecated │
│  草稿   │    │  已验证   │    │  已应用    │    │  已废弃   │
└─────────┘    └──────────┘    └───────────┘    └───────────┘
```

**核心能力**:
- 创建/验证经验
- 跨 Agent 经验查询
- 经验应用追踪
- 族谱关系追踪

### 4.5 Prompt Builder

**职责**: 动态提示词构建

```
┌─────────────────────────────────────────────────────────────┐
│                  提示词构建层级                              │
│                                                              │
│  1. SOUL (UserSoul) - 用户级价值观                          │
│     ↓                                                        │
│  2. IDENTITY (Agent.identity) - Agent 个性                 │
│     ↓                                                        │
│  3. system_prompt - 基础指令                                │
│     ↓                                                        │
│  4. capabilities - 能力描述                                │
│     ↓                                                        │
│  5. experiences - 相关经验                                 │
│     ↓                                                        │
│  6. skills - 技能元数据                                     │
└─────────────────────────────────────────────────────────────┘
```

### 4.6 Market Service

**职责**: 素材市场管理（Data/Skill/Doc）

```
┌─────────────────────────────────────────────────────────────┐
│                    Market Service                           │
│  ┌─────────────────┐ ┌─────────────────┐ ┌────────────────┐ │
│  │  Data Market   │ │  Skill Market  │ │  Doc Market   │ │
│  │  ./data/       │ │  ./skills/     │ │  ./templates/ │ │
│  └────────┬────────┘ └────────┬────────┘ └───────┬────────┘ │
│           │                   │                  │          │
│           └───────────────────┴──────────────────┘          │
│                           │                                    │
│              ┌────────────┴────────────┐                      │
│              │   Experiment (引用)    │                      │
│              │   data_ids: []         │                      │
│              │   skill_ids: []        │                      │
│              │   template_id: ""     │                      │
│              └─────────────────────────┘                      │
└─────────────────────────────────────────────────────────────┘
```

### 4.7 Tool Registry

**职责**: 内置工具注册表（25+ 工具）

| 类别 | 工具 |
|------|------|
| 代码执行 | `execute_code`, `run_python` |
| 文件操作 | `read_file`, `write_file`, `delete_file`, `list_directory`, `file_exists` |
| 任务管理 | `create_task`, `update_task`, `list_tasks`, `complete_task` |
| 笔记 | `create_note`, `search_notes`, `update_note` |
| Web | `web_search`, `fetch_url` |
| 技能 | `get_skill`, `discover_skills` |
| 经验 | `search_user_experiences`, `apply_experience` |

---

## 五、API 路由

| 路由 | 说明 |
|------|------|
| `/api/agents` | Agent CRUD |
| `/api/chat/{agent_id}` | 流式对话 |
| `/api/experiments` | 实验管理 |
| `/api/experiments/{id}/run` | 执行实验 |
| `/api/templates` | 模板市场 |
| `/api/experiences` | 经验库 |
| `/api/soul` | 用户 SOUL |
| `/api/providers` | LLM 提供商 |
| `/api/mcp` | MCP 配置 |
| `/api/market/data` | Data Market |
| `/api/market/skills` | Skill Market |
| `/api/market/templates` | Doc Market |

---

## 六、前端页面结构

```
frontend/src/app/
├── (auth)/
│   ├── login/
│   └── register/
├── (dashboard)/
│   ├── agents/
│   │   ├── [id]/
│   │   │   ├── identity/     # Agent 身份编辑
│   │   │   ├── capabilities/ # 能力详情
│   │   │   └── experiments/  # 实验历史
│   │   └── page.tsx          # Agent 列表
│   ├── chat/[agentId]/       # 聊天页面
│   ├── experiments/
│   │   ├── [id]/             # 实验详情
│   │   │   └── collaboration/ # 协作实验
│   │   ├── new/              # 创建实验
│   │   └── new-collaboration/ # 创建协作实验
│   ├── experiences/          # 经验库
│   │   └── user/             # 用户经验
│   ├── markets/              # 素材市场
│   │   ├── data/             # Data Market
│   │   ├── skills/           # Skill Market
│   │   └── templates/         # Doc Market
│   ├── providers/            # LLM 提供商
│   ├── settings/
│   │   └── soul/             # SOUL 管理
│   └── page.tsx              # 首页
```

---

## 七、记忆系统架构

### 分层记忆

```
┌─────────────────────────────────────────────────────────────┐
│                    UserSoul (SOUL)                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Core Truths  - 核心价值观                            │   │
│  │  Boundaries   - 行为边界                              │   │
│  │  Vibe        - 风格/氛围                              │   │
│  └─────────────────────────────────────────────────────┘   │
│                        ↓ 继承                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │               Agent Identity                         │   │
│  │  name, creature, vibe, emoji, avatar                │   │
│  └─────────────────────────────────────────────────────┘   │
│                        ↓ 增强                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Agent Capabilities                      │   │
│  │  core_capabilities, learned_skills,                 │   │
│  │  successful_patterns, problem_domains               │   │
│  └─────────────────────────────────────────────────────┘   │
│                        ↓ 沉淀                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Experiences                             │   │
│  │  situation, action, result, lesson, solution       │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 八、素材市场架构

### 设计原则

**以素材为中心，实验引用素材**（不复制，只存ID）

### 8.1 Data Market (数据集市场)

**存储位置**: `workspaces/{user_id}/data/`

```
data/
└── {dataset_id}/
    ├── metadata.json          # 元数据
    ├── data.csv               # 数据文件
    ├── schema.json            # 数据结构定义
    └── README.md              # 数据说明
```

**metadata.json 示例**:
```json
{
  "id": "dataset_001",
  "name": "销售数据Q1",
  "description": "2024年第一季度销售数据",
  "type": "csv",
  "rows": 1000,
  "columns": ["date", "product", "amount", "region"],
  "created_at": "2026-03-01",
  "tags": ["sales", "Q1", "2024"]
}
```

### 8.2 Skill Market (技能市场)

**存储位置**: `workspaces/{user_id}/skills/` + 全局 `./skills/`

```
skills/
└── {skill_id}/
    ├── SKILL.md               # 技能定义
    ├── metadata.json           # 元数据
    └── scripts/               # 技能脚本
        └── tool.py
```

### 8.3 Doc Market (文档模板市场)

**存储位置**: `workspaces/{user_id}/templates/`

```
templates/
└── {template_id}/
    ├── template.md            # 模板内容
    ├── config.json            # 配置
    └── metadata.json          # 元数据
```

### 实验与素材的关系

```python
class Experiment:
    # ==================== 基础信息 ====================
    name: str                     # 实验名称
    description: str              # 简短描述

    # ==================== 混合模式：背景信息 ====================

    # 方式一：轻量级（简单实验）
    # 直接在实验内填写
    requirements: str             # 具体需求说明
    background: str               # 背景信息

    # 方式二：引用文档（复杂实验）
    # 先在 Doc Market 创建文档，然后引用
    doc_ids: List[str]           # 引用的文档ID列表
    data_ids: List[str]           # 引用的数据集ID列表
    skill_ids: List[str]         # 需要的技能ID列表
    template_id: str              # 使用的模板ID
```

### 实验背景信息的两种方式

| 场景 | 方式 | 说明 |
|------|------|------|
| 简单实验 | 轻量级 | 直接在 `requirements` / `background` 填写 |
| 复杂实验 | 引用文档 | 先在 Doc Market 创建文档，通过 `doc_ids` 引用 |

**设计原则**：灵活选择，轻量实验直接写，复杂项目引用详细文档

---

## 九、实验场架构

### 单 Agent 实验流程

```
User 创建实验
    ↓
选择背景信息（混合模式）
    ├── 轻量级：填写 requirements / background
    └── 复杂项目：引用 doc_ids / data_ids / skill_ids
    ↓
选择素材 (Data/Skill/Doc) - 可选
    ↓
Experiment Engine 初始化
    ↓
┌─────────────────────────────────────────────────────────────┐
│  Loop (max_steps):                                          │
│    1. Sense: 理解任务，分析上下文                             │
│    2. Plan: 制定行动计划                                     │
│    3. Act: 执行动作 (调用工具 + 加载素材)                     │
│    4. Reflect: 反思结果，沉淀经验                            │
└─────────────────────────────────────────────────────────────┘
    ↓
输出结果 + 经验沉淀
```

### 多 Agent 协作实验

```
┌─────────────────────────────────────────────────────────────┐
│                Collaboration Types                           │
│                                                              │
│  sequential (顺序执行):                                      │
│    Agent A → Agent B → Agent C                              │
│                                                              │
│  parallel (并行执行):                                        │
│    ┌─ Agent A ─┐                                           │
│    ├─ Agent B ─┤ → 结果聚合                                  │
│    └─ Agent C ─┘                                           │
│                                                              │
│  debate (辩论模式):                                          │
│    Agent A ↔ Agent B (交互式辩论)                            │
└─────────────────────────────────────────────────────────────┘
```

---

## 十、外部应用整合（未来规划）

### 整合方式

| 方式 | 说明 | 适用场景 |
|------|------|----------|
| **方案A: 整合进来** | 外部数据直接存到本地 Market | 数据需要离线使用 |
| **方案B: MCP 服务** | 外部API作为MCP接入 | 实时数据、大量数据 |

### 外部应用整合示例

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      External Applications (外部应用)                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
│  │  Skill Service │  │   Data Service  │  │   Doc Service  │            │
│  │  (技能服务)      │  │   (数据服务)      │  │   (文档服务)     │            │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘            │
│           │                    │                    │                       │
│           └────────────────────┼────────────────────┘                       │
│                                │                                             │
│                    ┌───────────┴───────────┐                                 │
│                    │   Integration Layer   │                                 │
│                    │   (整合层)            │                                 │
│                    └───────────┬───────────┘                                 │
│                                │                                             │
│              ┌─────────────────┼─────────────────┐                          │
│              │                 │                 │                          │
│     ┌────────┴────────┐ ┌─────┴─────┐ ┌────────┴────────┐                 │
│     │ Local Market   │ │   MCP     │ │  Future API    │                 │
│     │ (本地存储)      │ │  Server   │ │  (未来API)     │                 │
│     └─────────────────┘ └───────────┘ └─────────────────┘                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

### MCP Server 配置示例

```json
{
  "name": "huggingface-datasets",
  "transport": "sse",
  "url": "https://api.huggingface.co/datasets",
  "env": {"HF_TOKEN": "xxx"}
}
```

---

## 十一、目录结构

```
agent_simple_creator/
├── backend/
│   ├── src/agent_builder/
│   │   ├── api/routes/          # API 端点
│   │   │   ├── markets/         # 素材市场路由
│   │   │   ├── agents.py
│   │   │   ├── experiments.py
│   │   │   └── ...
│   │   ├── core/                # 核心配置
│   │   ├── db/                  # 数据库模型
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── services/            # 业务逻辑
│   │   │   ├── market_service.py  # 素材市场服务
│   │   │   ├── experiment_engine.py
│   │   │   └── ...
│   │   └── main.py              # FastAPI 应用
│   ├── tests/                   # 测试
│   └── workspaces/              # Agent 工作空间
│       └── {user_id}/
│           ├── data/             # Data Market
│           ├── skills/          # Skill Market
│           ├── templates/       # Doc Market
│           └── agents/          # Agent 目录
├── frontend/
│   ├── src/
│   │   ├── app/                 # Next.js 页面
│   │   │   └── (dashboard)/
│   │   │       └── markets/    # 素材市场页面
│   │   ├── components/          # 组件
│   │   ├── lib/                 # 工具库
│   │   ├── contexts/           # React Context
│   │   └── types/               # TypeScript 类型
│   └── package.json
├── skills/                       # 全局共享技能
└── docs/                        # 文档
```

---

## 附录：启动命令

```bash
# 后端
cd backend
uv pip install -e "C:\Users\17625\Documents\GitHub\my-auth"
uv run uvicorn src.agent_builder.main:app --reload --port 8000

# 前端
cd frontend
npm run dev
```

访问:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs
