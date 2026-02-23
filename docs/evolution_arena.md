# Agent Evolution Arena 使用文档

## 概述

Agent Evolution Arena 是一个让 Agent 能够从执行中学习并持续进化的系统。通过 Sense-Plan-Act-Reflect 循环，Agent 能够沉淀经验、发现技能、不断进化。

## 核心概念

### 经验 (Experience)

从实验执行中沉淀的教训，包含以下核心要素：

- **情境 (situation)**: 任务描述或问题背景
- **行动 (action)**: 采取的执行步骤
- **结果 (result)**: 执行结果（成功/失败）
- **教训 (lesson)**: 从执行中获得的洞察
- **解决方案 (solution)**: 成功的解决方法

### 验证期机制

新创建的经验处于 `draft` 状态，需要经过验证：

- **应用 3 次，成功 2 次以上** → 状态变为 `verified`
- **应用 3 次，成功少于 2 次** → 状态变为 `deprecated`

只有 `verified` 状态的经验会被所有 Agent 共享，`draft` 状态的经验只对创建它的 Agent 可见。

### 经验族谱

经验支持变异进化：

- **parent_id**: 指向父经验
- **evolution_chain**: 记录完整的进化链
- **generation**: 表示第几代经验

### 技能发现

Agent 在执行时如果发现能力不足，会自动：

1. 搜索可用的 MCP Server
2. 匹配最适合的工具
3. 调用工具完成任务
4. 记录技能使用到经验中

## 快速开始

### 1. 启动服务

```bash
cd "C:\CODE\agent_simple_creator\.worktrees\feature-evolution-arena\backend"
uv run uvicorn src.agent_builder.main:app --reload --port 8001
```

### 2. 创建用户并登录

使用 myauth 的注册/登录接口获取 JWT token：

```bash
# 注册
POST http://localhost:8001/auth/register
{
  "email": "user@example.com",
  "password": "password123"
}

# 登录
POST http://localhost:8001/auth/login
{
  "email": "user@example.com",
  "password": "password123"
}
```

### 3. 创建 Agent

```bash
POST http://localhost:8001/api/agents
Authorization: Bearer <jwt_token>
{
  "name": "My Agent",
  "model": "deepseek-chat",
  "max_steps": 50,
  "system_prompt": "You are a helpful assistant."
}
```

### 4. 配置 MCP Server（可选，用于技能发现）

```bash
POST http://localhost:8001/api/mcp-servers
Authorization: Bearer <jwt_token>
{
  "name": "fetch",
  "transport": "stdio",
  "command": "uvx",
  "args": ["mcp-server-fetch"],
  "allowed_agents": []
}
```

### 5. 创建并运行 Experiment

创建实验：

```bash
POST http://localhost:8001/api/experiments
Authorization: Bearer <jwt_token>
{
  "agent_id": "<agent_id>",
  "name": "Document Analysis",
  "experiment_type": "document",
  "input_data": {
    "task": "搜索并分析关于 AI 的文档"
  }
}
```

运行实验：

```bash
POST http://localhost:8001/api/experiments/{experiment_id}/run
Authorization: Bearer <jwt_token>
```

### 6. 查看沉淀的经验

```bash
GET http://localhost:8001/api/experiences
Authorization: Bearer <jwt_token>
```

## API 参考

### 经验管理

#### 创建经验

```bash
POST /api/experiences
{
  "source_agent_id": "<agent_id>",
  "type": "success",
  "situation": "任务描述",
  "action": "执行的行动",
  "result": "执行结果",
  "lesson": "获得的经验",
  "solution": "解决方案"
}
```

#### 获取经验列表

```bash
GET /api/experiences?agent_id=<agent_id>&status=draft&type=success
```

参数：
- `agent_id`: 按 Agent 过滤
- `status`: 按状态过滤 (draft | verified | deprecated)
- `type`: 按类型过滤 (success | failure)

#### 获取经验详情

```bash
GET /api/experiences/{experience_id}
```

#### 更新经验

```bash
PUT /api/experiences/{experience_id}
{
  "lesson": "更新的经验",
  "solution": "更新的解决方案"
}
```

#### 删除经验

```bash
DELETE /api/experiences/{experience_id}
```

#### 应用经验

标记经验已被应用，并记录应用结果：

```bash
POST /api/experiences/{experience_id}/apply
{
  "success": true
}
```

返回：
- 应用成功后可能触发状态变更（draft → verified/deprecated）

#### 变异经验

基于已有经验创建改进版本：

```bash
POST /api/experiences/{experience_id}/mutate
{
  "improved_solution": "改进后的解决方案",
  "variant_reason": "改进原因说明"
}
```

#### 搜索相关经验

```bash
POST /api/experiences/search?agent_id=<agent_id>
{
  "query": "搜索关键词",
  "top_k": 5
}
```

### Agent 经验吸收

#### Agent 吸收经验

```bash
POST /api/agents/{agent_id}/absorb-experience
{
  "experience_id": "<experience_id>",
  "absorption_type": "referenced",
  "helpful_rating": 5
}
```

#### 获取 Agent 吸收的经验

```bash
GET /api/agents/{agent_id}/absorbed-experiences
```

### MCP Server 配置

#### 创建 MCP Server 配置

```bash
POST /api/mcp-servers
{
  "name": "fetch",
  "transport": "stdio",
  "command": "uvx",
  "args": ["mcp-server-fetch"],
  "allowed_agents": []
}
```

#### 获取 MCP Server 列表

```bash
GET /api/mcp-servers
```

#### 获取 MCP Server 详情

```bash
GET /api/mcp-servers/{config_id}
```

#### 更新 MCP Server 配置

```bash
PUT /api/mcp-servers/{config_id}
{
  "args": ["mcp-server-fetch", "--limit", "1000"]
}
```

#### 删除 MCP Server 配置

```bash
DELETE /api/mcp-servers/{config_id}
```

#### 测试 MCP Server 连接

```bash
POST /api/mcp-servers/{config_id}/test
```

### 实验执行

#### 创建实验

```bash
POST /api/experiments
{
  "agent_id": "<agent_id>",
  "name": "Experiment Name",
  "experiment_type": "document",
  "input_data": {
    "task": "任务描述"
  }
}
```

实验类型：
- `skill_creation`: 技能创建
- `document`: 文档分析
- `problem_solving`: 问题解决
- `data_analysis`: 数据分析
- `custom`: 自定义

#### 获取实验列表

```bash
GET /api/experiments?agent_id=<agent_id>&status=success
```

#### 获取实验详情

```bash
GET /api/experiments/{experiment_id}
```

#### 运行实验

```bash
POST /api/experiments/{experiment_id}/run
{
  "input_data": {
    "task": "可选的覆盖输入数据"
  }
}
```

执行流程：
1. **Sense**: 检索相关经验
2. **Plan**: 制定执行计划
3. **Act**: 执行计划步骤
4. **Reflect**: 总结经验教训

#### 获取实验执行结果

```bash
GET /api/experiments/{experiment_id}/execution
```

返回：
```json
{
  "success": true,
  "status": "success",
  "output": "执行输出",
  "error_message": null,
  "duration_ms": 1500,
  "steps_executed": 3,
  "experience_id": "<experience_id>"
}
```

## 执行流程详解

### Sense-Plan-Act-Reflect 循环

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  Sense  │ -> │  Plan   │ -> │   Act   │ -> │ Reflect │
└─────────┘    └─────────┘    └─────────┘    └─────────┘
     |              |              |              |
     v              v              v              v
 检索相关经验    制定执行计划    执行步骤      总结经验
```

### 经验沉淀流程

```
实验执行
    |
    v
执行成功/失败
    |
    v
创建经验记录
    |
    v
状态 = draft
    |
    v
应用 3 次 -> verified/deprecated
```

### 经验复用流程

```
新实验
    |
    v
Sense 阶段
    |
    v
搜索相关经验
    |
    v
应用经验提示
    |
    v
执行并更新统计
```

## 权限控制

所有数据都基于用户隔离：

- 用户只能访问自己的经验
- 用户只能访问自己的实验
- 用户只能访问自己的 Agent
- MCP Server 配置按用户隔离

验证方式：JWT Token

```bash
Authorization: Bearer <jwt_token>
```

## 测试

运行端到端测试：

```bash
uv run pytest tests/test_evolution_arena.py -v
```

测试覆盖：
- 经验生命周期（创建 → 沉淀 → 复用）
- 技能发现流程
- 权限隔离
- 实验执行引擎
- 经验变异

## 最佳实践

### 1. 经验管理

- 定期审查 `draft` 状态的经验
- 对有价值的经验进行变异进化
- 使用搜索功能发现相关经验

### 2. MCP Server 配置

- 为不同用途配置多个 MCP Server
- 使用 `allowed_agents` 限制 Agent 访问权限
- 定期测试 MCP Server 连接状态

### 3. 实验执行

- 使用描述性的实验名称
- 合理设置 `input_data` 以便经验检索
- 监控实验执行状态和输出

### 4. 性能优化

- 经验数量增多后，考虑使用向量搜索
- 定期清理 `deprecated` 状态的经验
- 对频繁使用的经验进行变异优化

## 故障排查

### 实验执行失败

检查：
1. Agent 是否存在且属于当前用户
2. 实验输入数据格式是否正确
3. 查看 `error_message` 字段

### 经验未找到

检查：
1. 经验是否属于当前用户
2. 经验状态是否为 `verified` 或当前 Agent 的 `draft`
3. 搜索关键词是否匹配

### MCP Server 连接失败

检查：
1. 命令和参数是否正确
2. 环境变量是否配置
3. 使用测试接口验证连接

## 后续规划

- [ ] 集成向量数据库实现语义搜索
- [ ] 支持经验的手动审核
- [ ] 经验分享和导入导出
- [ ] 执行过程可视化
- [ ] 经验效果统计分析
