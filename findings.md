# Findings - 研究发现和决策记录

**更新日期**: 2026-02-26

---

## 2026-02-26: 记忆系统架构优化研究

### Clawdbot SOUL.md 设计研究

**来源**: `C:\Users\17625\Documents\GitHub\clawdbot\docs\reference\templates\SOUL.md`

**核心概念**:
- **Core Truths**: 核心价值观
- **Boundaries**: 行为边界
- **Vibe**: 风格/氛围

**关键原则**:
- "Be genuinely helpful, not performatively helpful" - 真正有用而非表演
- "Have opinions" - 允许有观点
- "Be resourceful before asking" - 先尝试再问

### IDENTITY.md 设计研究

**来源**: `C:\Users\17625\Documents\GitHub\clawdbot\docs\reference\templates\IDENTITY.md`

**核心字段**:
- Name: Agent 名称
- Creature: Agent 类型
- Vibe: 风格
- Emoji: 标识符
- Avatar: 头像

### 技术决策

| 决策 | 选项 | 选择 |
|------|------|------|
| SOUL 存储 | 文件 vs 数据库 | 数据库表 |
| Identity 存储 | 单独表 vs JSON | JSON 字段 |
| 能力聚合 | 自动 vs 手动 | 手动触发 |

---

## 历史发现 (实验场开发)

## 发现

### 1. SQLAlchemy 关系配置
由于没有外键约束，需要使用 `primaryjoin` 和 `foreign_keys` 参数来定义关系。

### 2. myauth 认证
- Token 存储在 cookie 中，key 为 `access_token`
- 需要在每个 API 请求中添加 `Authorization: Bearer {token}` header
- Token 过期时间: 30 分钟

### 3. 前端认证问题
- api.ts 使用 fetch 时需要手动添加 Authorization header
- chatApi.sendMessage 函数漏掉了认证

## 问题记录

| 问题 | 解决方案 |
|------|----------|
| 后端启动失败 `ModuleNotFoundError: No module named 'myauth'` | 安装 myauth: `uv pip install -e "C:\Users\17625\Documents\GitHub\my-auth"` |
| 创建 Provider 401 未认证 | api.ts 添加 Authorization header |
| 聊天 401 未认证 | chatApi.sendMessage 添加 Authorization header |
| pyproject.toml 重复 key | 修复 TOML 语法 |

## 技术栈
- 后端: FastAPI + SQLAlchemy (async) + SQLite
- 前端: Next.js 14 + React + Tailwind CSS
- 认证: my-auth framework
