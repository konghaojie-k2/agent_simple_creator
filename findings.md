# 实验场开发 - 发现与问题

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
