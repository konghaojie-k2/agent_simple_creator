# Agent架构验证报告

生成时间: 2026-02-26

## 一、用户需求确认

根据用户确认，需求如下：

| 需求编号 | 需求描述 | 验收标准 |
|----------|----------|----------|
| REQ-1 | Agent初始化配置基础技能和工具 | 自动加载skills/目录下全量共享技能 |
| REQ-2 | Agent自主更新/添加技能能力 | 在实验场可沉淀相关经验 |
| REQ-3 | 跨Agent经验采纳 | 提供手动API让Agent主动查询用户所有Agent经验 |
| REQ-4 | 实验环境无需外部MCP | 可完成内部任务（如根据主题写报告） |
| REQ-5 | 报告结构完整性 | 报告包含摘要、正文、结论 |

## 二、架构现状分析

### 2.1 Agent初始化 (agent_initializer.py)

**当前实现：**
- `AgentInitializer`类负责创建目录结构
- 目录包括: `skills/`, `experiences/`, `workspace/`
- `api/routes/agents.py`中的`create_agent`函数已集成初始化

**问题：**
- ❌ 仅创建空目录，没有复制任何基础技能
- ❌ Agent创建后skills/目录为空，没有预装任何技能

### 2.2 技能系统 (skill_system.py)

**当前实现：**
- `AgentSkillSystem`支持三级技能来源：
  1. 共享技能 (shared_skills/)
  2. Agent专属技能 (workspaces/{user}/{agent}/skills/)
  3. 沉淀的经验 (workspaces/{user}/{agent}/experiences/)
- 实现渐进式披露（Progressive Disclosure）
- `get_skill`工具按需加载

**状态：**
- ✅ 架构完善，支持技能加载
- ⚠️ 但Agent初始化时没有利用此能力预装技能

### 2.3 经验管理 (experience_manager.py)

**当前实现：**
- `ExperienceManager`管理经验文件系统存储
- 支持创建、复制、列出、删除经验
- 经验以完整技能目录形式存储

**状态：**
- ✅ 文件系统存储架构完善

### 2.4 实验执行引擎 (experiment_engine.py)

**当前实现：**
- 实现Sense-Plan-Act-Reflect循环
- Reflect阶段自动沉淀技能到experiences/
- 支持经验检索和应用

**状态：**
- ✅ REQ-2满足：具备自主更新技能和沉淀经验能力
- ⚠️ REQ-5部分满足：实验类型需验证报告结构

### 2.5 工具注册表 (tool_registry.py)

**当前实现：**
- 25个内置工具
- 包括：代码执行、文件操作、Todo、笔记、Web、技能工具

**状态：**
- ✅ REQ-4满足：内部工具足够完成写报告任务

## 三、需求对比表

| 需求 | 当前状态 | 缺失功能 | 优先级 |
|------|----------|----------|--------|
| REQ-1: Agent初始化基础技能 | ⚠️ 部分满足 | 自动复制共享技能到Agent skills/目录 | P0 |
| REQ-2: 自主更新技能 | ✅ 满足 | 无 | - |
| REQ-3: 跨Agent经验查询 | ❌ 缺失 | GET /api/experiences/user/{user_id} API | P0 |
| REQ-4: 内部实验环境 | ✅ 满足 | 无 | - |
| REQ-5: 报告结构验证 | ⚠️ 部分满足 | document_generation实验类型验证 | P1 |

## 四、具体改进建议

### 4.1 Agent初始化增强

**文件：** `backend/src/agent_builder/api/routes/agents.py`

**修改create_agent函数：**
```python
@router.post("", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    agent_data: AgentCreate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    """Create a new agent."""
    service = AgentService(db)
    agent = await service.create_agent(user_id, agent_data)

    # 初始化Agent目录结构
    from agent_builder.services.agent_initializer import get_agent_initializer
    initializer = get_agent_initializer()
    dirs = initializer.initialize_agent_directories(user_id, agent.id)

    # 【新增】复制共享技能到Agent技能目录
    await _copy_shared_skills_to_agent(user_id, agent.id, dirs["skills_dir"])

    return agent


async def _copy_shared_skills_to_agent(
    user_id: str,
    agent_id: str,
    agent_skills_dir: str
):
    """将共享技能复制到Agent技能目录"""
    import shutil
    from pathlib import Path

    shared_skills_dir = Path("./skills")
    agent_skills_path = Path(agent_skills_dir)

    if not shared_skills_dir.exists():
        return

    # 遍历共享技能目录
    for skill_dir in shared_skills_dir.iterdir():
        if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
            dest_dir = agent_skills_path / skill_dir.name
            shutil.copytree(skill_dir, dest_dir, dirs_exist_ok=True)
```

### 4.2 跨Agent经验查询API

**文件：** `backend/src/agent_builder/services/experience_service.py`

**添加方法：**
```python
async def list_user_experiences(
    self,
    user_id: str,
    status: Optional[str] = None,
    limit: int = 50
) -> List[Experience]:
    """
    获取用户所有Agent的verified经验

    Args:
        user_id: 用户ID
        status: 状态过滤 (verified | draft | deprecated)
        limit: 返回数量限制

    Returns:
        经验列表
    """
    query = select(Experience).where(
        Experience.user_id == user_id
    )

    if status:
        query = query.where(Experience.status == status)

    query = query.order_by(Experience.created_at.desc()).limit(limit)

    result = await self.db.execute(query)
    return list(result.scalars().all())
```

**文件：** `backend/src/agent_builder/api/routes/experiments.py`

**添加端点：**
```python
@router.get("/user/{user_id}", response_model=List[ExperienceResponse])
async def get_user_experiences(
    user_id: str,
    status: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user),
):
    """获取用户所有Agent的经验（仅允许查询自己的）"""
    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    service = ExperienceService(db)
    experiences = await service.list_user_experiences(user_id, status, limit)
    return experiences
```

**文件：** `backend/src/agent_builder/services/tool_registry.py`

**添加工具：**
```python
async def _search_user_experiences(
    self,
    user_id: str,
    status_filter: str = "verified",
    limit: int = 10
) -> Dict[str, Any]:
    """搜索用户所有Agent的经验"""
    from agent_builder.services.experience_service import ExperienceService
    from agent_builder.core.database import async_session_factory

    async with async_session_factory() as db:
        service = ExperienceService(db)
        experiences = await service.list_user_experiences(
            user_id=user_id,
            status=status_filter,
            limit=limit
        )

        return {
            "success": True,
            "count": len(experiences),
            "experiences": [
                {
                    "id": exp.id,
                    "type": exp.type,
                    "lesson": exp.lesson,
                    "solution": exp.solution,
                    "status": exp.status
                }
                for exp in experiences
            ]
        }
```

### 4.3 写报告实验类型

**文件：** `backend/src/agent_builder/services/experiment_engine.py`

**在_plan_phase中添加：**
```python
elif task_type == "document_generation":
    plan["steps"] = [
        {"action": "understand_topic", "params": {}},
        {"action": "create_outline", "params": {}},
        {"action": "write_summary", "params": {}},
        {"action": "write_body", "params": {}},
        {"action": "write_conclusion", "params": {}},
        {"action": "format_report", "params": {}}
    ]
```

**验证输出结构：**
```python
def _validate_report_structure(output: str) -> bool:
    """验证报告是否包含摘要、正文、结论"""
    required_sections = ["摘要", "结论"]  # 正文可能无明确标题
    return all(section in output for section in required_sections)
```

## 五、后续任务

1. ✅ 架构验证报告 - 完成
2. ⏳ 实现Agent初始化技能复制 - 进行中
3. ⏳ 实现跨Agent经验查询API - 待开始
4. ⏳ 编写完整测试套件 - 待开始
5. ⏳ 更新进度文档 - 待所有功能完成
