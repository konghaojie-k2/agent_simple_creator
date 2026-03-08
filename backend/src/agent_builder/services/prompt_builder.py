#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent Prompt Builder - 动态提示词构建服务

职责：
1. 基础提示词 + 动态经验注入
2. 技能元数据注入
3. 能力描述注入

记忆架构映射：
- system_prompt: 基础提示词（静态）
- capabilities: 能力描述（从 Experience 聚合）
- experiences: 相关经验（动态检索和注入）
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from agent_builder.db.models import Agent, Experience, UserSoul
from agent_builder.services.experience_service import ExperienceService


class PromptBuilder:
    """
    动态提示词构建器

    构建流程：
    1. 基础提示词 (system_prompt)
    2. 能力描述 (capabilities)
    3. 相关经验注入 (relevant experiences)
    4. 技能元数据 (from skill_system)
    """

    def __init__(
        self,
        db: AsyncSession,
        experience_service: ExperienceService,
    ):
        self.db = db
        self.experience_service = experience_service

    async def build_agent_prompt(
        self,
        agent: Agent,
        task_description: str,
        user_id: str,
        skill_metadata: Optional[str] = None,
        additional_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        构建 Agent 的完整提示词

        层级结构（参考 clawdbot）：
        1. SOUL (UserSoul) - 用户级共享价值观
        2. IDENTITY (Agent.identity) - Agent 个性化身份
        3. system_prompt - 基础提示词
        4. capabilities - 能力描述
        5. experiences - 相关经验注入
        6. skills - 技能元数据

        Args:
            agent: Agent 实例
            task_description: 任务描述（用于检索相关经验）
            user_id: 用户 ID
            skill_metadata: 技能元数据（来自 skill_system.get_system_prompt()）
            additional_context: 额外上下文

        Returns:
            完整的系统提示词
        """
        prompt_sections = []

        # 1. SOUL - 用户级共享价值观（所有 Agent 共享）
        soul_section = await self._build_soul_section(user_id)
        if soul_section:
            prompt_sections.append(self._format_section("灵魂 (SOUL)", soul_section))

        # 2. IDENTITY - Agent 个性化身份
        identity_section = self._build_identity_section(agent)
        if identity_section:
            prompt_sections.append(self._format_section("身份 (IDENTITY)", identity_section))

        # 3. 基础提示词
        if agent.system_prompt:
            prompt_sections.append(self._format_section("基础指令", agent.system_prompt))

        # 4. 能力描述
        capabilities_section = await self._build_capabilities_section(agent, user_id)
        if capabilities_section:
            prompt_sections.append(self._format_section("核心能力", capabilities_section))

        # 5. 相关经验注入（如果启用）
        prompt_config = agent.prompt_config or {}
        if prompt_config.get("inject_experiences", True):
            experience_section = await self._build_experience_section(
                agent, task_description, user_id, prompt_config
            )
            if experience_section:
                prompt_sections.append(self._format_section("相关经验", experience_section))

        # 6. 技能元数据
        if skill_metadata:
            prompt_sections.append(self._format_section("可用技能", skill_metadata))

        # 7. 额外上下文
        if additional_context:
            context_section = self._build_context_section(additional_context)
            if context_section:
                prompt_sections.append(self._format_section("当前上下文", context_section))

        # 组合所有部分
        if prompt_sections:
            return "\n\n".join(prompt_sections)
        else:
            return "你是一个 AI 助手。"

    async def _build_capabilities_section(
        self, agent: Agent, user_id: str
    ) -> Optional[str]:
        """
        构建能力描述部分

        如果 agent.capabilities 不存在，从 Experience 聚合生成
        """
        # 如果 Agent 有自定义 capabilities，直接使用
        if agent.capabilities:
            return self._format_capabilities(agent.capabilities)

        # 否则从 Experience 聚合生成
        return await self._aggregate_capabilities_from_experience(agent.id, user_id)

    async def _aggregate_capabilities_from_experience(
        self, agent_id: str, user_id: str
    ) -> Optional[str]:
        """
        从 Experience 聚合生成能力描述

        策略：
        1. 统计 verified 经验中使用的技能
        2. 提取成功模式
        3. 生成能力描述
        """
        experiences = await self.experience_service.list_experiences(
            user_id=user_id,
            agent_id=agent_id,
            status="verified",
        )

        if not experiences:
            return None

        # 聚合能力信息
        capabilities = {
            "core_capabilities": [],
            "learned_skills": [],
            "successful_patterns": [],
        }

        for exp in experiences:
            # 添加使用的技能
            if exp.skills_used:
                for skill in exp.skills_used:
                    if skill not in capabilities["learned_skills"]:
                        capabilities["learned_skills"].append(skill)

            # 添加发现的技能
            if exp.skills_discovered:
                for skill in exp.skills_discovered:
                    if skill not in capabilities["learned_skills"]:
                        capabilities["learned_skills"].append(skill)

            # 提取成功模式（从成功的经验中）
            if exp.type == "success" and exp.lesson:
                pattern = self._extract_pattern_from_lesson(exp.lesson)
                if pattern and pattern not in capabilities["successful_patterns"]:
                    capabilities["successful_patterns"].append(pattern)

        # 生成自然语言描述
        return self._format_capabilities(capabilities)

    def _extract_pattern_from_lesson(self, lesson: str) -> Optional[str]:
        """从经验教训中提取成功模式"""
        # 简化版：取第一句话作为模式
        if not lesson:
            return None
        sentences = lesson.split("。")
        return sentences[0].strip() if sentences else None

    def _format_capabilities(self, capabilities: Dict[str, Any]) -> str:
        """格式化能力描述为自然语言"""
        parts = []

        core_caps = capabilities.get("core_capabilities", [])
        if core_caps:
            parts.append(f"核心能力: {', '.join(core_caps)}")

        learned_skills = capabilities.get("learned_skills", [])
        if learned_skills:
            parts.append(f"已掌握技能: {', '.join(learned_skills[:10])}")  # 限制数量

        successful_patterns = capabilities.get("successful_patterns", [])
        if successful_patterns:
            parts.append(f"成功经验模式:")
            for pattern in successful_patterns[:5]:  # 限制数量
                parts.append(f"  - {pattern}")

        return "\n".join(parts) if parts else "持续学习中..."

    async def _build_experience_section(
        self,
        agent: Agent,
        task_description: str,
        user_id: str,
        prompt_config: Dict[str, Any],
    ) -> Optional[str]:
        """
        构建相关经验部分

        检索与当前任务相关的经验，格式化为提示词
        """
        max_experiences = prompt_config.get("max_experiences", 5)

        # 检索相关经验
        relevant_exps = await self.experience_service.search_relevant_experiences(
            user_id=user_id,
            agent_id=agent.id,
            query=task_description,
            top_k=max_experiences
        )

        if not relevant_exps:
            return None

        # 格式化经验为提示词
        experience_parts = []
        for i, exp in enumerate(relevant_exps, 1):
            exp_text = f"{i}. {exp.lesson}\n   解决方案: {exp.solution[:100]}..."
            experience_parts.append(exp_text)

        return "\n".join(experience_parts)

    def _build_context_section(self, context: Dict[str, Any]) -> Optional[str]:
        """构建额外上下文部分"""
        if not context:
            return None

        parts = []
        for key, value in context.items():
            if isinstance(value, (str, int, float, bool)):
                parts.append(f"{key}: {value}")
            elif isinstance(value, list):
                parts.append(f"{key}: {', '.join(str(v) for v in value[:5])}")
            elif isinstance(value, dict):
                parts.append(f"{key}: {str(value)[:100]}")

        return "\n".join(parts) if parts else None

    async def _build_soul_section(self, user_id: str) -> Optional[str]:
        """
        构建 SOUL 部分（用户级共享价值观）

        从 UserSoul 表获取，如果不存在则使用默认 SOUL
        """
        from sqlalchemy import select

        result = await self.db.execute(
            select(UserSoul).where(UserSoul.user_id == user_id)
        )
        soul = result.scalar_one_or_none()

        if soul and soul.soul_content:
            return soul.soul_content

        # 默认 SOUL（参考 clawdbot 设计）
        return """## Core Truths

**Be genuinely helpful, not performatively helpful.** Skip the filler words — just help.

**Have opinions.** You're allowed to disagree, prefer things, find stuff amusing or boring.

**Be resourceful before asking.** Try to figure it out. Read the file. Check the context. Search for it.

**Earn trust through competence.** Be careful with external actions. Be bold with internal ones.

**Remember you're a guest.** Treat user's data with respect.

## Boundaries

- Private things stay private. Period.
- When in doubt, ask before acting externally.
- Never send half-baked replies to messaging surfaces.

## Vibe

Be the assistant you'd actually want to talk to. Concise when needed, thorough when it matters."""

    def _build_identity_section(self, agent: Agent) -> Optional[str]:
        """
        构建 IDENTITY 部分（Agent 个性化身份）

        从 agent.identity 获取
        """
        if not agent.identity:
            return None

        identity = agent.identity
        parts = []

        # Name
        if name := identity.get("name"):
            parts.append(f"- **Name:** {name}")

        # Creature
        if creature := identity.get("creature"):
            parts.append(f"- **Creature:** {creature}")

        # Vibe
        if vibe := identity.get("vibe"):
            parts.append(f"- **Vibe:** {vibe}")

        # Emoji
        if emoji := identity.get("emoji"):
            parts.append(f"- **Emoji:** {emoji}")

        # Avatar
        if avatar := identity.get("avatar"):
            parts.append(f"- **Avatar:** {avatar}")

        if parts:
            return "\n".join(parts) + "\n\n---"

        return None


class CapabilityService:
    """
    能力聚合服务

    负责：
    1. 从 Experience 聚合 Agent 能力
    2. 更新 Agent.capabilities 字段
    3. 提供能力查询 API
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def update_agent_capabilities(
        self, agent_id: str, user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        更新 Agent 的能力描述

        从所有 verified 经验中聚合能力信息，更新到 Agent.capabilities
        """
        # 获取 Agent
        result = await self.db.execute(
            select(Agent).where(
                Agent.id == agent_id,
                Agent.user_id == user_id
            )
        )
        agent = result.scalar_one_or_none()
        if not agent:
            return None

        # 获取所有 verified 经验
        exp_result = await self.db.execute(
            select(Experience).where(
                Experience.source_agent_id == agent_id,
                Experience.status == "verified"
            )
        )
        experiences = exp_result.scalars().all()

        # 聚合能力
        capabilities = await self._aggregate_capabilities(experiences)

        # 更新 Agent
        agent.capabilities = capabilities
        await self.db.flush()
        await self.db.refresh(agent)

        return capabilities

    async def _aggregate_capabilities(
        self, experiences: List[Experience]
    ) -> Dict[str, Any]:
        """从经验列表聚合能力"""
        capabilities = {
            "core_capabilities": [],
            "learned_skills": set(),
            "successful_patterns": [],
            "problem_domains": set(),
            "statistics": {
                "total_experiences": len(experiences),
                "success_count": 0,
                "failure_count": 0,
            }
        }

        for exp in experiences:
            # 统计
            if exp.type == "success":
                capabilities["statistics"]["success_count"] += 1
            else:
                capabilities["statistics"]["failure_count"] += 1

            # 技能
            if exp.skills_used:
                capabilities["learned_skills"].update(exp.skills_used)
            if exp.skills_discovered:
                capabilities["learned_skills"].update(exp.skills_discovered)

            # 成功模式
            if exp.type == "success" and exp.lesson:
                pattern = self._extract_pattern(exp.lesson)
                if pattern and pattern not in capabilities["successful_patterns"]:
                    capabilities["successful_patterns"].append(pattern)

            # 问题领域（从 situation 提取关键词）
            domain = self._extract_domain(exp.situation)
            if domain:
                capabilities["problem_domains"].add(domain)

        # 转换 set 为 list
        capabilities["learned_skills"] = list(capabilities["learned_skills"])
        capabilities["problem_domains"] = list(capabilities["problem_domains"])

        return capabilities

    def _extract_pattern(self, lesson: str) -> Optional[str]:
        """从教训中提取模式"""
        if not lesson:
            return None
        # 简化版：取第一句话
        sentences = lesson.split("。")
        return sentences[0].strip() if sentences else None

    def _extract_domain(self, situation: str) -> Optional[str]:
        """从情境中提取问题领域"""
        if not situation:
            return None
        # 简化版：使用前几个词作为领域
        words = situation.split()[:3]
        return " ".join(words) if words else None

    async def get_capability_summary(
        self, agent_id: str, user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        获取 Agent 能力摘要

        优先使用缓存的 capabilities，如果没有则实时计算
        """
        result = await self.db.execute(
            select(Agent).where(
                Agent.id == agent_id,
                Agent.user_id == user_id
            )
        )
        agent = result.scalar_one_or_none()
        if not agent:
            return None

        # 如果有缓存，直接返回
        if agent.capabilities:
            return agent.capabilities

        # 否则实时计算（不更新缓存）
        exp_result = await self.db.execute(
            select(Experience).where(
                Experience.source_agent_id == agent_id,
                Experience.status == "verified"
            )
        )
        experiences = exp_result.scalars().all()
        return await self._aggregate_capabilities(experiences)


# 全局实例缓存
_prompt_builder_instance = None
_capability_service_instance = None


def get_prompt_builder(
    db: AsyncSession,
    experience_service: ExperienceService,
) -> PromptBuilder:
    """获取 PromptBuilder 实例"""
    return PromptBuilder(db, experience_service)


def get_capability_service(db: AsyncSession) -> CapabilityService:
    """获取 CapabilityService 实例"""
    return CapabilityService(db)
