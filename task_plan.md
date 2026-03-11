# 任务规划 - Market Service 架构

## 目标

构建基于 Service 的 Market 系统，整合现有技术资产

## 架构决策 ✅ 已确认
- **选用 Service 而非 CLI**：适合多用户共享需求
- **HTTP 调用**：开发阶段 localhost，生产阶段远程服务器
- **插件机制**：OpenClaw 通过 Lab Tools 插件调用 Service

### 技术资产复用
| 项目 | 路径 | 复用方向 |
|------|------|----------|
| Skill Market | `C:/CODE/skill market` | Skill 模块核心逻辑 |
| Dataset Manager | `C:/CODE/dataset-manager` | Data 模块核心逻辑 |
| Project Space | `C:/CODE/project space` | 架构参考 |

---

## 开发进度

### 阶段 1: MVP（1-2周）- ✅ 完成
- [x] 1.1 搭建 Market Service 骨架
- [x] 1.2 实现一个简单 API 验证
- [x] 1.3 编写一个插件 demo

### 阶段 2: 核心功能（2-3周）- 🔄 进行中
- [x] 2.1 完成 Data/Doc/Skill API (基础 CRUD)
- [x] 2.2 权限管理 (共享/发布/授权)
- [x] 2.3 完善 3 个插件 (Lab Tools)

### 阶段 3: 集成（1-2周）- ⏳ 待开始
- [ ] 3.1 Skill 配置
- [ ] 3.2 端到端测试
- [ ] 3.3 部署文档

---

## Lab Tools 插件功能清单

### 总计：50+ Tools

| 类别 | Tools |
|------|-------|
| **数据集 (8)** | list, get, search, create, upload, delete, download, update |
| **数据分析 (4)** | analyze, quality, schema, insights |
| **文档 (8)** | list, get, search, upload, delete, download, update, analyze |
| **技能 (6)** | list, get, search, install, list_installed, uninstall |
| **搜索 (1)** | search_rag |
| **共享/发布 (4)** | share_dataset, share_document, share_skill, publish_to_public |
| **权限管理 (4)** | grant, revoke, list, check |
| **版本管理 (3)** | list_versions, create_version, rollback |
| **分类/标签 (3)** | list_categories, create_category, list_tags |
| **导入/导出 (2)** | export, import |
| **活动日志 (1)** | get_activity_log |
| **备份恢复 (3)** | create_backup, restore_backup, list_backups |
| **工具 (2)** | health_check, get_stats |

---

## PR 状态
- **PR #1**: https://github.com/konghaojie-k2/agent_simple_creator/pull/1 (Open)

## 当前分支
`feature/ai-assistant-work`
