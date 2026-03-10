# 研究发现 - Market Service 架构

## 2026-03-10: 架构讨论结论

### 核心决策

1. **Service 优先于 CLI**
   - 原因：多人/多组织共享素材需要统一服务
   - 现有项目本身就是 Service 架构

2. **开发/生产环境分离**
   - 开发：localhost:5000 (Service 本地运行)
   - 生产：远程服务器 HTTPS

3. **OpenClaw 调用方式**
   - 通过 HTTP 调用 Service
   - Lab Tools 插件封装 HTTP 请求

### 技术资产分析

#### Skill Market (`C:/CODE/skill market`)
- 核心逻辑：`backend/app/services/`
- 可复用：上传/下载/版本控制
- 需改造：去除 GitLab 集成

#### Dataset Manager (`C:/CODE/dataset-manager`)
- 核心逻辑：`backend/src/tools/`
- 可复用：文件上传/元数据管理

#### Project Space (`C:/CODE/project space`)
- 架构参考：FastAPI + 前端模式

### 插件架构

```
OpenClaw → Lab Tools (插件) → HTTP → Market Service
```

插件职责：
1. 暴露 Tool 给 OpenClaw
2. 封装 HTTP 请求调用 Service
3. 通过配置切换开发/生产环境

## 待验证

- [ ] OpenClaw 插件机制是否支持配置化
- [ ] Service API 具体设计
- [ ] 权限模型设计
