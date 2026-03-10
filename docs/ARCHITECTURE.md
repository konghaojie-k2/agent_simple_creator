# Market Service 架构设计

## 目标

基于 Service 优先的方案，整合现有技术资产

## 核心决策

**选用 Service 而非 CLI**，原因：
- 多人/多组织共享素材需要
- 现有项目（Skill Market、Dataset Manager、Project Space）本身就是 Service 架构
- OpenClaw 通过 HTTP 调用，本地开发即 localhost Service

## 架构设计

```
┌─────────────────────────────────────────────────────────┐
│                    开发阶段 (localhost)                   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   OpenClaw ──► HTTP ──► localhost:5000 (Service)      │
│                                                         │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                    生产阶段 (远程服务器)                  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   用户电脑              服务器                          │
│   OpenClaw ──► HTTP ──► https://market.yourcompany.com │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## 技术资产复用

| 现有项目 | 复用方向 |
|----------|----------|
| Skill Market | Skill 模块核心逻辑（去 GitLab 集成，保留版本控制） |
| Dataset Manager | Data 模块核心逻辑（文件上传、元数据） |
| Project Space | 架构参考（RAG、FastAPI 模式） |

## 系统架构

```
┌─────────────────────────────────────────────────────────┐
│              OpenClaw (原版，不修改)                      │
│                                                         │
│   ┌─────────┐    HTTP    ┌──────────────┐            │
│   │  Skill  │ ◄─────────► │  Lab Tools   │            │
│   │ (轻量)   │            │  (插件)       │            │
│   └────┬────┘            └──────┬───────┘            │
│        │                         │                     │
│        │ Tool 调用                │ HTTP 调用           │
│        ▼                         ▼                     │
│   ┌─────────┐            ┌──────────────┐             │
│   │  Tool   │            │Market Service│             │
│   │(data_   │            │  (独立服务)   │             │
│   │market)  │            └──────┬───────┘             │
│   └─────────┘                   │                     │
│                                 ▼                      │
│                        ┌────────────────┐              │
│                        │   存储层        │              │
│                        │ Data/Doc/Skill │              │
│                        └────────────────┘              │
└─────────────────────────────────────────────────────────┘
```

## 组件说明

### 1. Lab Tools 插件
- 位置：`~/.openclaw/extensions/lab-tools/`
- 职责：HTTP 调用 Market Service
- 代码示例：
```python
class DataMarketTool:
    def execute(self, action: str, **kwargs):
        url = f"{MARKET_SERVICE_URL}/api/data/{action}"
        response = requests.post(url, json=kwargs)
        return response.json()
```

### 2. Market Service
- 职责：Data/Doc/Skill 的 CRUD + 权限管理
- 技术选型：FastAPI + 现有项目改造
- API 设计：
  - `/api/data/*` - 数据管理
  - `/api/doc/*` - 文档管理
  - `/api/skill/*` - 技能管理

## 开发计划

### 阶段 1：MVP（1-2周）
1. 搭建 Market Service 骨架
2. 实现一个简单 API 验证
3. 编写一个插件 demo

### 阶段 2：核心功能（2-3周）
1. 完成 Data/Doc/Skill API
2. 权限管理
3. 完善 3 个插件

### 阶段 3：集成（1-2周）
1. Skill 配置
2. 端到端测试
3. 部署文档

## 待讨论

- [ ] OpenClaw 插件机制确认
- [ ] API 详细设计
- [ ] 权限模型设计
