#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Experiment 执行引擎
实现 Sense-Plan-Act-Reflect 循环
"""

import uuid
import time
from typing import Optional, List, Dict, Any
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from agent_builder.db.models import Experiment, Agent, Experience, ExperimentTemplate
from agent_builder.schemas.execution import (
    ExecutionStatus, ExecutionStep, ExecutionContext,
    ExecutionResult, PlanStep
)
from agent_builder.services.core.experience_service import ExperienceService
from agent_builder.services.market.skills.skill_service import SkillService
from agent_builder.services.core.mcp_client_manager import MCPClientManager
from agent_builder.services.core.tool_registry import get_tool_registry
from agent_builder.services.core.experience_manager import get_experience_manager
from agent_builder.services.market.skills.skill_system import AgentSkillSystem
from agent_builder.services.core.prompt_builder import get_prompt_builder


class ExperimentEngine:
    """
    实验执行引擎

    核心循环：Sense -> Plan -> Act -> Reflect
    """

    def __init__(
        self,
        db: AsyncSession,
        experience_service: ExperienceService,
        skill_discovery_service: SkillService,
        mcp_manager: Optional[MCPClientManager] = None,
    ):
        self.db = db
        self.experience_service = experience_service
        self.skill_discovery = skill_discovery_service
        self.mcp_manager = mcp_manager or MCPClientManager()

    async def run_experiment(
        self,
        experiment_id: str,
        user_id: str
    ) -> ExecutionResult:
        """
        运行实验（完整的 Sense-Plan-Act-Reflect 循环）
        """
        start_time = time.time()

        # 1. 获取实验和 Agent 信息
        experiment = await self._get_experiment(experiment_id, user_id)
        if not experiment:
            return ExecutionResult(
                success=False,
                status=ExecutionStatus.FAILED,
                error_message="Experiment not found or access denied",
                duration_ms=0,
                steps_executed=0
            )

        agent = await self._get_agent(experiment.agent_id, user_id)
        if not agent:
            return ExecutionResult(
                success=False,
                status=ExecutionStatus.FAILED,
                error_message="Agent not found or access denied",
                duration_ms=0,
                steps_executed=0
            )

        # ========== 初始化 Agent 技能系统 ==========
        # 1. 创建技能系统（加载共享技能 + Agent专属技能 + 经验）
        skill_system = AgentSkillSystem(
            user_id=user_id,
            agent_id=agent.id,
            shared_skills_dir="./skills",
            workspaces_dir="./workspaces"
        )

        # 2. 获取系统提示（包含技能元数据）
        skill_prompt = skill_system.get_system_prompt()

        # 3. 设置技能系统到工具注册表（用于 get_skill 工具）
        from agent_builder.services.core.tool_registry import get_tool_registry
        tool_registry = get_tool_registry()
        tool_registry.set_skill_system(skill_system)
        available_tools = tool_registry.list_tools()

        # 更新实验状态为 running
        experiment.status = ExecutionStatus.RUNNING.value
        await self.db.commit()

        context = None

        try:
            # 2. SENSE - 感知阶段
            await self._update_experiment_status(experiment, ExecutionStatus.SENSE)
            context = await self._sense_phase(experiment, agent, user_id)

            # 3. PLAN - 决策阶段
            await self._update_experiment_status(experiment, ExecutionStatus.PLAN)
            plan = await self._plan_phase(experiment, agent, context)
            context.plan = plan

            # 4. ACT - 执行阶段
            await self._update_experiment_status(experiment, ExecutionStatus.ACT)
            execution_success = await self._act_phase(experiment, agent, context, user_id)

            # 5. REFLECT - 反思阶段
            await self._update_experiment_status(experiment, ExecutionStatus.REFLECT)
            experience_id = await self._reflect_phase(
                experiment, agent, context, execution_success, user_id
            )

            # 更新实验状态
            final_status = ExecutionStatus.SUCCESS if execution_success else ExecutionStatus.FAILED
            experiment.status = final_status.value
            experiment.output_data = {
                "result": context.steps[-1].output_data if context.steps else {},
                "steps": [self._serialize_step(step) for step in context.steps],
                "experience_id": experience_id
            }
            await self.db.commit()

            duration_ms = int((time.time() - start_time) * 1000)

            # 安全获取输出，处理 output_data 为 None 的情况
            output_content = None
            if context.steps and context.steps[-1].output_data:
                output_content = context.steps[-1].output_data.get("content")

            return ExecutionResult(
                success=execution_success,
                status=final_status,
                output=output_content,
                duration_ms=duration_ms,
                steps_executed=len(context.steps),
                experience_id=experience_id
            )

        except Exception as e:
            experiment.status = ExecutionStatus.FAILED.value
            experiment.error_message = str(e)
            await self.db.commit()

            return ExecutionResult(
                success=False,
                status=ExecutionStatus.FAILED,
                error_message=str(e),
                duration_ms=int((time.time() - start_time) * 1000),
                steps_executed=len(context.steps) if context else 0
            )

    async def _sense_phase(
        self,
        experiment: Experiment,
        agent: Agent,
        user_id: str
    ) -> ExecutionContext:
        """
        感知阶段：收集信息

        1. 检索相关经验
        2. 构建动态提示词
        3. 准备执行上下文
        """
        context = ExecutionContext(
            experiment_id=experiment.id,
            agent_id=agent.id,
            user_id=user_id
        )

        # ========== 新增：构建动态提示词 ==========
        task_description = experiment.input_data.get("task", "")

        # 获取技能元数据（来自技能系统）
        skill_system = AgentSkillSystem(
            user_id=user_id,
            agent_id=agent.id,
            shared_skills_dir="./skills",
            workspaces_dir="./workspaces"
        )
        skill_metadata = skill_system.get_system_prompt()

        # 构建动态提示词（基础提示 + 能力 + 经验 + 技能）
        prompt_builder = get_prompt_builder(self.db, self.experience_service)
        dynamic_prompt = await prompt_builder.build_agent_prompt(
            agent=agent,
            task_description=task_description,
            user_id=user_id,
            skill_metadata=skill_metadata,
            additional_context={
                "experiment_type": experiment.experiment_type,
                "experiment_name": experiment.name,
            }
        )

        # 将动态提示词保存到上下文
        context.dynamic_system_prompt = dynamic_prompt

        # 检索相关经验（同用户的 verified 经验 + 当前 agent 的 draft 经验）
        relevant_exps = await self.experience_service.search_relevant_experiences(
            user_id=user_id,
            agent_id=agent.id,
            query=task_description,
            top_k=5
        )

        context.relevant_experiences = [
            {
                "id": exp.id,
                "type": exp.type,
                "lesson": exp.lesson,
                "solution": exp.solution,
                "status": exp.status
            }
            for exp in relevant_exps
        ]

        return context

    async def _plan_phase(
        self,
        experiment: Experiment,
        agent: Agent,
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """
        决策阶段：制定执行计划

        优先级：
        1. 使用模板的 execution_plan（如果存在）
        2. 回退到内置计划（向后兼容）

        后续可以接入 LLM 进行智能规划
        """
        task_type = experiment.experiment_type
        task_description = experiment.input_data.get("task", "")

        # 1. 优先使用模板的 execution_plan
        if experiment.template_id:
            template = await self._load_template(experiment.template_id)
            if template and "execution_plan" in template.template_config:
                return template.template_config["execution_plan"]

        # 2. 回退到内置逻辑（向后兼容）
        return await self._builtin_plan_phase(experiment, agent, context)

    async def _load_template(self, template_id: str) -> Optional[ExperimentTemplate]:
        """加载模板"""
        from sqlalchemy import select

        result = await self.db.execute(
            select(ExperimentTemplate).where(ExperimentTemplate.id == template_id)
        )
        return result.scalar_one_or_none()

    async def _builtin_plan_phase(
        self,
        experiment: Experiment,
        agent: Agent,
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """
        内置计划生成逻辑（向后兼容）

        简化版：基于任务类型生成计划
        """
        task_type = experiment.experiment_type
        task_description = experiment.input_data.get("task", "")

        # 构建经验提示
        experience_hints = ""
        if context.relevant_experiences:
            experience_hints = "\n".join([
                f"- 经验: {exp['lesson']}"
                for exp in context.relevant_experiences[:3]
            ])

        # 根据任务类型生成计划（简化版）
        plan = {
            "steps": [],
            "experience_hints_used": len(context.relevant_experiences) > 0
        }

        if task_type == "skill_creation":
            plan["steps"] = [
                {"action": "analyze_requirement", "params": {}},
                {"action": "design_interface", "params": {}},
                {"action": "implement_logic", "params": {}},
                {"action": "test_skill", "params": {}}
            ]
        elif task_type == "document_generation":
            # 生成结构化报告：摘要、正文、结论
            plan["steps"] = [
                {"action": "understand_topic", "params": {"topic": task_description}},
                {"action": "create_outline", "params": {}},
                {"action": "write_summary", "params": {}},
                {"action": "write_body", "params": {}},
                {"action": "write_conclusion", "params": {}},
                {"action": "format_report", "params": {}},
                {"action": "validate_structure", "params": {}}
            ]
        elif task_type == "document":
            plan["steps"] = [
                {"action": "search_documents", "params": {"query": task_description}},
                {"action": "analyze_content", "params": {}},
                {"action": "generate_response", "params": {}}
            ]
        elif task_type == "problem_solving":
            plan["steps"] = [
                {"action": "analyze_problem", "params": {}},
                {"action": "search_solution", "params": {}},
                {"action": "execute_solution", "params": {}}
            ]
        else:
            # 通用计划
            plan["steps"] = [
                {"action": "understand_task", "params": {}},
                {"action": "execute_task", "params": {}},
                {"action": "validate_result", "params": {}}
            ]

        return plan

    async def _act_phase(
        self,
        experiment: Experiment,
        agent: Agent,
        context: ExecutionContext,
        user_id: str
    ) -> bool:
        """
        执行阶段：执行计划中的步骤

        1. 先检查 Agent 技能库是否有匹配的技能
        2. 如果没有，去技能超市发现并加载
        3. 执行并记录结果
        """
        from agent_builder.services.market.skills.skill_service import SkillService

        plan = context.plan
        steps = plan.get("steps", [])

        # 创建技能服务实例
        skill_service = SkillService(self.db, self.mcp_manager)

        for i, step in enumerate(steps):
            step_start = time.time()
            action = step.get("action")
            params = step.get("params", {})

            execution_step = ExecutionStep(
                step_number=i + 1,
                action=action,
                status="running",
                input_data={"action": action, "params": params},
                timestamp=datetime.utcnow()
            )

            try:
                # ========== 关键变化：优先使用 Agent 自己的技能 ==========

                # 需要技能的 action（简化判断：包含特定关键词的 action 需要技能）
                if self._needs_skill(action):
                    # 1a. 尝试从 Agent 技能库找到匹配技能
                    existing_skill = await skill_service.find_skill_for_capability(
                        agent_id=agent.id,
                        user_id=user_id,
                        capability=action
                    )

                    if existing_skill:
                        # 1b. 直接用 Agent 的技能
                        result = await skill_service.execute_skill(
                            agent_id=agent.id,
                            user_id=user_id,
                            skill_name=existing_skill.name,
                            parameters=params
                        )

                        execution_step.status = "success" if result.get("success") else "failed"
                        execution_step.output_data = {
                            "skill_source": "agent_library",
                            "skill_name": existing_skill.name,
                            "result": result
                        }
                    else:
                        # 1c. 去技能超市发现新技能
                        matches = await skill_service.discover_skills(
                            user_id=user_id,
                            agent_id=agent.id,
                            capability_need=action,
                            top_k=3
                        )

                        if matches:
                            # 加载到 Agent 技能库
                            best_match = matches[0]
                            new_skill = await skill_service.load_skill(
                                agent_id=agent.id,
                                user_id=user_id,
                                source_server=best_match.server_name,
                                source_tool=best_match.tool_name,
                                custom_name=best_match.tool_name
                            )

                            if new_skill:
                                # 执行新加载的技能
                                result = await skill_service.execute_skill(
                                    agent_id=agent.id,
                                    user_id=user_id,
                                    skill_name=new_skill.name,
                                    parameters=params
                                )

                                execution_step.status = "success" if result.get("success") else "failed"
                                execution_step.output_data = {
                                    "skill_source": "discovered_and_loaded",
                                    "skill_name": new_skill.name,
                                    "result": result
                                }

                                # 记录发现的技能
                                context.discovered_skills.append({
                                    "skill_id": new_skill.id,
                                    "name": new_skill.name,
                                    "source": f"{best_match.server_name}/{best_match.tool_name}"
                                })
                            else:
                                execution_step.status = "failed"
                                execution_step.error_message = f"Failed to load skill: {best_match.tool_name}"
                        else:
                            # 没有可用技能
                            execution_step.status = "failed"
                            execution_step.error_message = f"No skill available for: {action}"
                else:
                    # 2. 不需要技能的 action，直接执行（简化版）
                    result = await self._execute_action(action, params, context, user_id)
                    execution_step.status = "success"
                    execution_step.output_data = {"result": result}

            except Exception as e:
                execution_step.status = "failed"
                execution_step.error_message = str(e)
                context.steps.append(execution_step)
                return False

            execution_step.duration_ms = int((time.time() - step_start) * 1000)

            # 检查结果状态，如果返回 capability_missing 则标记为失败
            if execution_step.output_data:
                result_data = execution_step.output_data.get("result", {})
                if isinstance(result_data, dict) and result_data.get("status") == "capability_missing":
                    execution_step.status = "failed"
                    execution_step.error_message = f"Missing capability: {result_data.get('missing_capability', 'unknown')}"

            context.steps.append(execution_step)

            # 如果步骤失败，立即返回
            if execution_step.status == "failed":
                return False

        return True

    def _validate_report_structure(self, report_content: str) -> Dict[str, Any]:
        """
        验证报告结构是否完整

        检查是否包含：
        - 摘要 (Summary)
        - 结论 (Conclusion)
        - 正文内容（通常在摘要和结论之间）

        Args:
            report_content: 报告内容

        Returns:
            验证结果字典
        """
        content_lower = report_content.lower()

        # 检查必需部分
        has_summary = any(keyword in content_lower for keyword in
                         ["摘要", "summary", "概述", "overview", "概要"])
        has_conclusion = any(keyword in content_lower for keyword in
                           ["结论", "conclusion", "总结", "summary", "总结"])

        # 检查是否有足够的正文内容（在摘要和结论之间的内容）
        # 简化判断：检查是否有足够的段落或字数
        word_count = len(report_content.strip())
        has_body = word_count > 200  # 至少200字符

        valid = has_summary and has_conclusion and has_body

        return {
            "valid": valid,
            "has_summary": has_summary,
            "has_conclusion": has_conclusion,
            "has_body": has_body,
            "word_count": word_count,
            "missing_sections": [] if valid else (
                (["摘要"] if not has_summary else []) +
                (["结论"] if not has_conclusion else []) +
                (["正文"] if not has_body else [])
            )
        }

    def _needs_skill(self, action: str) -> bool:
        """判断 action 是否需要外部技能"""
        skill_keywords = ["fetch", "web", "parse", "call", "api", "search", "download", "upload"]
        action_lower = action.lower()
        return any(keyword in action_lower for keyword in skill_keywords)

    async def _execute_action(
        self,
        action: str,
        params: Dict[str, Any],
        context: ExecutionContext,
        user_id: str
    ) -> Dict[str, Any]:
        """
        执行单个动作

        优先使用工具注册表中的实际工具
        """
        # 获取工具注册表
        tool_registry = get_tool_registry()

        # 动作到工具的映射
        action_to_tool = {
            "search_documents": "search_documents",  # 需要外部技能
            "analyze_content": "analyze_content",    # 需要外部技能
            "generate_response": "generate_response",  # 需要 LLM
            "execute_code": "execute_python",
            "run_code": "execute_python",
            "read_file": "read_file",
            "write_file": "write_file",
            "delete_file": "delete_file",
            "list_files": "list_files",
            "file_exists": "file_exists",
            "understand_task": None,  # 需要 LLM
            "understand_topic": None,  # 需要 LLM
            "execute_task": None,     # 需要 LLM 或工具
            "validate_result": None,  # 需要 LLM
            "validate_structure": None,  # 内置验证
            "analyze_requirement": None,  # 需要 LLM
            "design_interface": None,     # 需要 LLM
            "implement_logic": None,      # 需要 LLM
            "test_skill": None,           # 需要 LLM
            "analyze_problem": None,      # 需要 LLM
            "search_solution": None,      # 需要外部技能
            "execute_solution": None,     # 需要工具
            "create_outline": None,       # 需要 LLM
            "write_summary": None,        # 需要 LLM
            "write_body": None,           # 需要 LLM
            "write_conclusion": None,     # 需要 LLM
            "format_report": None,        # 需要 LLM
        }

        tool_name = action_to_tool.get(action)

        # 特殊处理：validate_structure 使用内置验证
        if action == "validate_structure":
            # 收集之前步骤的输出
            report_content = ""
            for step in context.steps:
                if step.status == "success" and step.output_data:
                    content = step.output_data.get("result", {}).get("content", "")
                    if content:
                        report_content += "\n\n" + content
            validation_result = self._validate_report_structure(report_content)
            return {
                "status": "success" if validation_result["valid"] else "failed",
                "validation": validation_result,
                "content": f"报告结构验证: {'通过' if validation_result['valid'] else '失败'}"
            }

        # 如果有对应的工具，使用工具执行
        if tool_name and tool_name in tool_registry.list_tools():
            tool_params = self._build_tool_params(action, params)
            result = await tool_registry.execute_tool(tool_name, tool_params)
            return {
                "status": "success" if result.get("success") else "failed",
                "tool": tool_name,
                "result": result
            }

        # 如果没有对应工具，需要外部技能或 LLM
        # 返回 capability_missing，触发技能发现流程
        return {
            "status": "capability_missing",
            "missing_capability": action,
            "suggestion": "This action requires external skill or LLM"
        }

    def _build_tool_params(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """构建工具参数"""
        if action in ["execute_code", "run_code"]:
            return {
                "code": params.get("code", params.get("script", "")),
                "timeout": params.get("timeout", 30)
            }
        elif action == "read_file":
            return {"path": params.get("path", "")}
        elif action == "write_file":
            return {
                "path": params.get("path", ""),
                "content": params.get("content", "")
            }
        elif action == "delete_file":
            return {"path": params.get("path", "")}
        elif action == "list_files":
            return {"path": params.get("path", ".")}
        elif action == "file_exists":
            return {"path": params.get("path", "")}
        else:
            return params

    async def _reflect_phase(
        self,
        experiment: Experiment,
        agent: Agent,
        context: ExecutionContext,
        execution_success: bool,
        user_id: str
    ) -> Optional[str]:
        """
        反思阶段：总结经验教训

        1. 分析执行过程
        2. 提取关键教训
        3. 创建经验记录
        """
        from agent_builder.services.market.skills.skill_service import SkillService

        # 构建经验内容
        exp_type = "success" if execution_success else "failure"

        situation = experiment.input_data.get("task", "")
        action = "; ".join([s.action for s in context.steps])
        result = "Success" if execution_success else "Failed"

        if execution_success:
            lesson = f"成功完成任务: {situation}"
            solution = context.steps[-1].output_data.get("content", "") if context.steps else ""
        else:
            # 找出失败的步骤
            failed_step = next((s for s in context.steps if s.status == "failed"), None)
            if failed_step:
                lesson = f"在 '{failed_step.action}' 步骤失败: {failed_step.error_message}"
            else:
                lesson = f"任务执行失败"
            solution = ""

        # 从 Agent 技能库获取实际使用的技能
        skill_service = SkillService(self.db, self.mcp_manager)
        agent_skills = await skill_service.list_agent_skills(agent.id, user_id)
        # 获取调用次数 > 0 的技能（即实际使用的技能）
        skills_used = [s.name for s in agent_skills if s.call_count > 0]

        # 发现的新技能（从 discovered_skills 获取）
        skills_discovered = [s.get("name") for s in context.discovered_skills]

        # 创建经验记录
        experience_data = {
            "user_id": user_id,
            "source_agent_id": agent.id,
            "source_experiment_id": experiment.id,
            "type": exp_type,
            "situation": situation,
            "action": action,
            "result": result,
            "lesson": lesson,
            "solution": solution,
            "skills_used": skills_used,
            "skills_discovered": skills_discovered
        }

        experience = await self.experience_service.create_experience(experience_data)

        # 如果使用了相关经验，更新它们的应用统计
        for exp_info in context.relevant_experiences:
            await self.experience_service.apply_experience(
                exp_id=exp_info["id"],
                user_id=user_id,
                success=execution_success
            )

        # ========== 保存技能到文件系统（经验沉淀）==========
        # 如果执行成功且有新发现的技能，保存到 experiences/ 目录
        if execution_success and context.discovered_skills:
            exp_manager = get_experience_manager()
            for skill_info in context.discovered_skills:
                await exp_manager.create_experience(
                    user_id=user_id,
                    agent_id=agent.id,
                    name=skill_info.get("name", f"skill_{skill_info.get('skill_id', 'unknown')}"),
                    description=f"Skill discovered during experiment: {skill_info.get('name', 'unknown')}",
                    skill_content=f"# {skill_info.get('name', 'Skill')}\n\nSource: {skill_info.get('source', 'unknown')}",
                    task_context=situation,
                    source="agent_created"
                )

        return experience.id

    def _serialize_step(self, step: ExecutionStep) -> Dict[str, Any]:
        """将 ExecutionStep 序列化为可 JSON 序列化的字典"""
        return {
            "step_number": step.step_number,
            "action": step.action,
            "status": step.status,
            "input_data": step.input_data,
            "output_data": step.output_data,
            "error_message": step.error_message,
            "duration_ms": step.duration_ms,
            "timestamp": step.timestamp.isoformat() if step.timestamp else None,
        }

    async def _get_experiment(self, experiment_id: str, user_id: str) -> Optional[Experiment]:
        """获取实验（带权限验证）"""
        result = await self.db.execute(
            select(Experiment).where(
                Experiment.id == experiment_id,
                Experiment.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def _get_agent(self, agent_id: str, user_id: str) -> Optional[Agent]:
        """获取 Agent（带权限验证）"""
        result = await self.db.execute(
            select(Agent).where(
                Agent.id == agent_id,
                Agent.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def _update_experiment_status(self, experiment: Experiment, status: ExecutionStatus):
        """更新实验状态"""
        experiment.status = status.value
        await self.db.commit()


class MultiAgentExperimentEngine(ExperimentEngine):
    """
    多Agent协作实验执行引擎

    支持多种协作模式：
    - sequential: 顺序执行（按 join_order 顺序）
    - parallel: 并行执行（所有 Agent 同时工作）
    - debate: 辩论模式（Agent 互相讨论后达成共识）
    """

    async def run_collaboration_experiment(
        self,
        experiment_id: str,
        user_id: str
    ) -> ExecutionResult:
        """
        运行多Agent协作实验
        """
        start_time = time.time()

        # 1. 获取实验和参与者
        experiment = await self._get_experiment(experiment_id, user_id)
        if not experiment:
            return ExecutionResult(
                success=False,
                status=ExecutionStatus.FAILED,
                error_message="Experiment not found or access denied",
                duration_ms=0,
                steps_executed=0
            )

        participants = await self._get_participants(experiment_id, user_id)
        if not participants:
            return ExecutionResult(
                success=False,
                status=ExecutionStatus.FAILED,
                error_message="No participants found for collaboration experiment",
                duration_ms=0,
                steps_executed=0
            )

        collaboration_type = experiment.collaboration_type or "sequential"

        # 更新实验状态
        experiment.status = ExecutionStatus.RUNNING.value
        await self.db.commit()

        try:
            # 2. 根据协作类型执行
            if collaboration_type == "sequential":
                result = await self._run_sequential(experiment, participants, user_id)
            elif collaboration_type == "parallel":
                result = await self._run_parallel(experiment, participants, user_id)
            elif collaboration_type == "debate":
                result = await self._run_debate(experiment, participants, user_id)
            else:
                result = ExecutionResult(
                    success=False,
                    status=ExecutionStatus.FAILED,
                    error_message=f"Unknown collaboration type: {collaboration_type}",
                    duration_ms=int((time.time() - start_time) * 1000),
                    steps_executed=0
                )

            # 3. 更新实验状态
            final_status = ExecutionStatus.SUCCESS if result.success else ExecutionStatus.FAILED
            experiment.status = final_status.value
            experiment.output_data = {
                "result": result.output,
                "collaboration_type": collaboration_type,
                "participants_count": len(participants)
            }
            await self.db.commit()

            return result

        except Exception as e:
            experiment.status = ExecutionStatus.FAILED.value
            experiment.error_message = str(e)
            await self.db.commit()

            return ExecutionResult(
                success=False,
                status=ExecutionStatus.FAILED,
                error_message=str(e),
                duration_ms=int((time.time() - start_time) * 1000),
                steps_executed=0
            )

    async def _get_participants(
        self,
        experiment_id: str,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """获取实验参与者列表"""
        from sqlalchemy import select
        from agent_builder.db.models import ExperimentParticipant

        result = await self.db.execute(
            select(ExperimentParticipant).where(
                ExperimentParticipant.experiment_id == experiment_id,
                ExperimentParticipant.user_id == user_id
            ).order_by(ExperimentParticipant.join_order)
        )

        participants = result.scalars().all()

        return [
            {
                "id": p.id,
                "agent_id": p.agent_id,
                "role": p.role,
                "join_order": p.join_order,
                "status": p.status,
                "config": p.config or {}
            }
            for p in participants
        ]

    async def _run_sequential(
        self,
        experiment: Experiment,
        participants: List[Dict[str, Any]],
        user_id: str
    ) -> ExecutionResult:
        """
        顺序执行模式

        Agent 按 join_order 顺序依次执行，每个 Agent 的输出传递给下一个
        """
        start_time = time.time()
        all_steps = []
        shared_context = experiment.input_data.copy()

        for participant in participants:
            agent = await self._get_agent(participant["agent_id"], user_id)
            if not agent:
                continue

            # 更新实验输入数据为共享上下文
            original_input_data = experiment.input_data.copy()
            experiment.input_data = shared_context.copy()
            await self.db.flush()

            # 创建执行上下文
            context = await self._sense_phase(experiment, agent, user_id)
            plan = await self._plan_phase(experiment, agent, context)
            context.plan = plan

            success = await self._act_phase(experiment, agent, context, user_id)

            # 收集输出并更新共享上下文
            if context.steps:
                all_steps.extend(context.steps)
                last_output = context.steps[-1].output_data.get("result", {})
                if isinstance(last_output, dict):
                    shared_context.update(last_output)

            # 记录消息
            await self._save_agent_message(
                experiment, user_id,
                participant["agent_id"], "next",
                {"step": "sequential_output", "output": context.steps[-1].output_data if context.steps else {}}
            )

            # 恢复原始输入数据
            experiment.input_data = original_input_data
            await self.db.flush()

        return ExecutionResult(
            success=True,
            status=ExecutionStatus.SUCCESS,
            output=f"Sequential collaboration completed with {len(participants)} agents",
            duration_ms=int((time.time() - start_time) * 1000),
            steps_executed=len(all_steps)
        )

    async def _run_parallel(
        self,
        experiment: Experiment,
        participants: List[Dict[str, Any]],
        user_id: str
    ) -> ExecutionResult:
        """
        并行执行模式

        所有 Agent 同时执行，最后汇总结果
        """
        import asyncio

        start_time = time.time()
        all_steps = []

        async def run_single_agent(participant: Dict[str, Any]):
            agent = await self._get_agent(participant["agent_id"], user_id)
            if not agent:
                return None

            context = await self._sense_phase(experiment, agent, user_id)
            plan = await self._plan_phase(experiment, agent, context)
            context.plan = plan

            success = await self._act_phase(experiment, agent, context, user_id)

            return {
                "agent_id": participant["agent_id"],
                "role": participant["role"],
                "steps": context.steps,
                "success": success
            }

        # 并行执行所有 Agent
        results = await asyncio.gather(*[
            run_single_agent(p) for p in participants
        ])

        # 汇总结果
        for result in results:
            if result and result["steps"]:
                all_steps.extend(result["steps"])

        return ExecutionResult(
            success=True,
            status=ExecutionStatus.SUCCESS,
            output=f"Parallel collaboration completed with {len(participants)} agents",
            duration_ms=int((time.time() - start_time) * 1000),
            steps_executed=len(all_steps)
        )

    async def _run_debate(
        self,
        experiment: Experiment,
        participants: List[Dict[str, Any]],
        user_id: str
    ) -> ExecutionResult:
        """
        辩论模式

        Agent 轮流发表观点，进行多轮讨论后达成共识
        """
        start_time = time.time()
        all_steps = []

        # 获取 leader
        leader = next((p for p in participants if p["role"] == "leader"), None)
        if not leader:
            leader = participants[0]  # 默认第一个为 leader

        max_rounds = experiment.workflow_config.get("max_rounds", 3) if experiment.workflow_config else 3

        for round_num in range(max_rounds):
            for participant in participants:
                agent = await self._get_agent(participant["agent_id"], user_id)
                if not agent:
                    continue

                # 记录本轮发言
                await self._save_agent_message(
                    experiment, user_id,
                    participant["agent_id"], "all",
                    {"round": round_num + 1, "action": "present_view"}
                )

                # 执行 Agent 思考
                context = await self._sense_phase(experiment, agent, user_id)
                plan = await self._plan_phase(experiment, agent, context)
                context.plan = plan

                await self._act_phase(experiment, agent, context, user_id)

                if context.steps:
                    all_steps.extend(context.steps)

        # Leader 总结
        leader_agent = await self._get_agent(leader["agent_id"], user_id)
        if leader_agent:
            # 保存原始输入数据
            original_input_data = experiment.input_data.copy()

            # 更新实验任务为总结任务
            experiment.input_data = {
                **experiment.input_data,
                "task": "总结所有 Agent 的讨论结果"
            }
            await self.db.flush()

            context = await self._sense_phase(experiment, leader_agent, user_id)
            plan = await self._plan_phase(experiment, leader_agent, context)
            context.plan = plan

            await self._act_phase(experiment, leader_agent, context, user_id)

            if context.steps:
                all_steps.extend(context.steps)

            # 恢复原始输入数据
            experiment.input_data = original_input_data
            await self.db.flush()

        return ExecutionResult(
            success=True,
            status=ExecutionStatus.SUCCESS,
            output=f"Debate collaboration completed with {len(participants)} agents in {max_rounds} rounds",
            duration_ms=int((time.time() - start_time) * 1000),
            steps_executed=len(all_steps)
        )

    async def _save_agent_message(
        self,
        experiment: Experiment,
        user_id: str,
        from_agent: str,
        to_agent: str,
        message: Dict[str, Any]
    ):
        """保存 Agent 间通信消息"""
        from agent_builder.services.experiment.experiment_workspace import get_experiment_workspace

        workspace = get_experiment_workspace()
        workspace.save_agent_message(
            user_id=user_id,
            experiment_id=experiment.id,
            from_agent=from_agent,
            to_agent=to_agent,
            message=message
        )
