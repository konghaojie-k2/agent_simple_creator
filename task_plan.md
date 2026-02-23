# 实验场 (Experiment Arena) - 任务规划

## 目标
将现有的 Agent领养平台 扩展为支持实验场功能，Agent可以接受任务并在实验环境中执行。

## 阶段进度

### Phase 1: 数据模型 ✅ COMPLETE
- [x] Experiment 模型
- [x] ExperimentTemplate 模型
- [x] ExperimentExperience 模型

### Phase 2: 后端服务 ✅ COMPLETE
- [x] ExperimentService (CRUD)
- [x] ExperimentTemplateService
- [x] ExperimentExperienceService
- [x] API Routes

### Phase 3: 前端界面 ✅ COMPLETE
- [x] 实验列表页
- [x] 创建实验页
- [x] 实验详情页
- [x] 模板市场
- [x] 经验库

### Phase 4: 认证修复 ✅ COMPLETE
- [x] api.ts 添加 Authorization header
- [x] chatApi.sendMessage 修复

### Phase 5: 实验执行引擎 (TODO)
- [ ] experiment_engine.py
- [ ] 代码执行 + 文件操作
- [ ] API 工具调用

### Phase 6: 文档超市 MVP (TODO)
- [ ] README 生成
- [ ] API 文档生成
- [ ] 技术文档

## 关键文件

### 后端
- `backend/src/agent_builder/db/models.py` - 数据模型
- `backend/src/agent_builder/schemas/pydantic.py` - Pydantic schemas
- `backend/src/agent_builder/services/experiment_service.py` - 服务层
- `backend/src/agent_builder/api/routes/experiments.py` - API 路由

### 前端
- `frontend/src/types/index.ts` - TypeScript 类型
- `frontend/src/lib/api.ts` - API 客户端
- `frontend/src/app/(dashboard)/experiments/` - 实验页面
- `frontend/src/app/(dashboard)/templates/` - 模板市场
- `frontend/src/app/(dashboard)/experiences/` - 经验库

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

## API 端点

- `POST /api/experiments` - 创建实验
- `GET /api/experiments` - 列表实验
- `GET /api/experiments/{id}` - 实验详情
- `POST /api/experiments/{id}/run` - 运行实验
- `GET /api/templates` - 模板列表
- `POST /api/experiences` - 创建经验
- `GET /api/experiences/search` - 搜索经验

## 后续任务
1. 实现实验执行引擎
2. 文档生成实验类型
3. 技能创建实验类型
4. 数据分析实验类型
