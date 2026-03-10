# 任务规划 - Market Service 架构

## 目标

构建基于 Service 的 Market 系统，整合现有技术资产

## 架构决策

### 核心决策
- **选用 Service 而非 CLI**：适合多用户共享需求
- **HTTP 调用**：开发阶段 localhost，生产阶段远程服务器
- **插件机制**：OpenClaw 通过 Lab Tools 插件调用 Service

### 技术资产复用
| 项目 | 路径 | 复用方向 |
|------|------|----------|
| Skill Market | `C:/CODE/skill market` | Skill 模块核心逻辑 |
| Dataset Manager | `C:/CODE/dataset-manager` | Data 模块核心逻辑 |
| Project Space | `C:/CODE/project space` | 架构参考 |

## 开发阶段

### 阶段 1: MVP（1-2周）- 状态: pending
- [ ] 1.1 搭建 Market Service 骨架
- [ ] 1.2 实现一个简单 API 验证
- [ ] 1.3 编写一个插件 demo

### 阶段 2: 核心功能（2-3周）- 状态: pending
- [ ] 2.1 完成 Data/Doc/Skill API
- [ ] 2.2 权限管理
- [ ] 2.3 完善 3 个插件

### 阶段 3: 集成（1-2周）- 状态: pending
- [ ] 3.1 Skill 配置
- [ ] 3.2 端到端测试
- [ ] 3.3 部署文档

## 待讨论

- [ ] OpenClaw 插件机制确认
- [ ] API 详细设计
- [ ] 权限模型设计

## 当前分支

`feature/market-service-architecture`
