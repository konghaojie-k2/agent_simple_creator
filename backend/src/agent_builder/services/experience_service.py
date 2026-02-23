# -*- coding: utf-8 -*-
"""Experience service for managing agent experiences."""

import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from agent_builder.db.models import Experience, AgentExperienceAbsorption, Agent


class ExperienceService:
    """Service for managing agent experiences."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_experience(self, data: dict) -> Experience:
        """创建新经验（初始状态为 draft）"""
        experience = Experience(
            id=str(uuid.uuid4()),
            user_id=data["user_id"],
            source_agent_id=data["source_agent_id"],
            source_experiment_id=data.get("source_experiment_id"),
            type=data["type"],
            situation=data["situation"],
            action=data["action"],
            result=data["result"],
            lesson=data["lesson"],
            solution=data["solution"],
            skills_used=data.get("skills_used", []),
            skills_discovered=data.get("skills_discovered", []),
            status="draft",
            applied_count=0,
            success_count=0,
            is_auto_variant=data.get("is_auto_variant", False),
            variant_reason=data.get("variant_reason"),
            embedding=data.get("embedding"),
        )

        self.db.add(experience)
        await self.db.flush()
        await self.db.refresh(experience)

        return experience

    async def get_experience(self, exp_id: str, user_id: str) -> Optional[Experience]:
        """获取经验详情"""
        result = await self.db.execute(
            select(Experience).where(
                Experience.id == exp_id,
                Experience.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_experiences(
        self,
        user_id: str,
        agent_id: Optional[str] = None,
        status: Optional[str] = None,
        exp_type: Optional[str] = None,
    ) -> List[Experience]:
        """获取经验列表"""
        query = select(Experience).where(Experience.user_id == user_id)

        if agent_id:
            query = query.where(Experience.source_agent_id == agent_id)
        if status:
            query = query.where(Experience.status == status)
        if exp_type:
            query = query.where(Experience.type == exp_type)

        query = query.order_by(Experience.created_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def apply_experience(
        self, exp_id: str, user_id: str, success: bool
    ) -> Optional[Experience]:
        """
        应用经验后更新统计
        验证期检查：3次应用，2次成功 → verified
        """
        result = await self.db.execute(
            select(Experience).where(
                Experience.id == exp_id,
                Experience.user_id == user_id,
            )
        )
        experience = result.scalar_one_or_none()

        if not experience:
            return None

        # 更新统计
        experience.applied_count += 1
        if success:
            experience.success_count += 1
        experience.last_applied_at = datetime.utcnow()

        # 验证期逻辑
        if experience.status == "draft":
            if experience.applied_count >= 3:
                # 3次应用后判断状态
                if experience.success_count >= 2:
                    experience.status = "verified"
                else:
                    experience.status = "deprecated"

        await self.db.flush()
        await self.db.refresh(experience)

        return experience

    async def search_relevant_experiences(
        self,
        user_id: str,
        agent_id: str,
        query: str,
        top_k: int = 5,
    ) -> List[Experience]:
        """
        检索相关经验：
        - 同用户的 verified 经验
        - 当前 Agent 自己的 draft 经验
        """
        # 首先获取当前 agent 的信息以检查它是否存在
        agent_result = await self.db.execute(
            select(Agent).where(Agent.id == agent_id, Agent.user_id == user_id)
        )
        agent = agent_result.scalar_one_or_none()

        if not agent:
            return []

        # 构建查询条件
        # 条件1: verified 经验（同用户所有 Agent 共享）
        # 条件2: 当前 Agent 自己的 draft 经验
        conditions = or_(
            Experience.status == "verified",
            and_(
                Experience.status == "draft",
                Experience.source_agent_id == agent_id,
            ),
        )

        # 文本搜索（简单的关键词匹配）
        search_pattern = f"%{query}%"
        text_conditions = or_(
            Experience.situation.ilike(search_pattern),
            Experience.action.ilike(search_pattern),
            Experience.result.ilike(search_pattern),
            Experience.lesson.ilike(search_pattern),
            Experience.solution.ilike(search_pattern),
        )

        sql_query = (
            select(Experience)
            .where(Experience.user_id == user_id)
            .where(conditions)
            .where(text_conditions)
            .order_by(
                # 优先返回 verified 经验，然后按创建时间排序
                Experience.status == "verified",
                Experience.created_at.desc(),
            )
            .limit(top_k)
        )

        result = await self.db.execute(sql_query)
        return list(result.scalars().all())

    async def mutate_experience(
        self,
        original_id: str,
        user_id: str,
        agent_id: str,
        improved_solution: str,
        variant_reason: str,
    ) -> Optional[Experience]:
        """自动变异产生新经验"""
        # 获取原始经验并验证所有权
        result = await self.db.execute(
            select(Experience).where(
                Experience.id == original_id,
                Experience.user_id == user_id,
            )
        )
        original = result.scalar_one_or_none()

        if not original:
            return None

        # 构建族谱链
        evolution_chain = list(original.evolution_chain or [])
        if not evolution_chain:
            evolution_chain = [original_id]
        evolution_chain.append(str(uuid.uuid4()))  # 新经验的ID占位，后面会替换

        # 创建新经验
        new_experience = Experience(
            id=evolution_chain[-1],  # 使用族谱链最后一个作为ID
            user_id=original.user_id,
            source_agent_id=agent_id,
            source_experiment_id=original.source_experiment_id,
            parent_id=original_id,
            evolution_chain=evolution_chain,
            generation=original.generation + 1,
            type=original.type,
            situation=original.situation,
            action=original.action,
            result=original.result,
            lesson=original.lesson,
            solution=improved_solution,  # 使用改进的解决方案
            skills_used=original.skills_used,
            skills_discovered=original.skills_discovered,
            status="draft",
            applied_count=0,
            success_count=0,
            is_auto_variant=True,
            variant_reason=variant_reason,
        )

        self.db.add(new_experience)
        await self.db.flush()
        await self.db.refresh(new_experience)

        return new_experience

    async def absorb_experience(
        self,
        agent_id: str,
        experience_id: str,
        user_id: str,
        absorption_type: str = "referenced",
        helpful_rating: Optional[int] = None,
        applied_experiment_id: Optional[str] = None,
    ) -> Optional[AgentExperienceAbsorption]:
        """Agent 吸收经验"""
        # 验证 agent 属于当前用户
        agent_result = await self.db.execute(
            select(Agent).where(
                Agent.id == agent_id,
                Agent.user_id == user_id,
            )
        )
        if not agent_result.scalar_one_or_none():
            return None

        # 验证 experience 属于当前用户
        result = await self.db.execute(
            select(Experience).where(
                Experience.id == experience_id,
                Experience.user_id == user_id,
            )
        )
        experience = result.scalar_one_or_none()

        if not experience:
            return None

        # 创建吸收记录
        absorption = AgentExperienceAbsorption(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            experience_id=experience_id,
            absorption_type=absorption_type,
            helpful_rating=helpful_rating,
            applied_experiment_id=applied_experiment_id,
        )

        self.db.add(absorption)
        await self.db.flush()
        await self.db.refresh(absorption)

        return absorption

    async def update_experience(
        self,
        exp_id: str,
        user_id: str,
        data: dict,
    ) -> Optional[Experience]:
        """更新经验"""
        experience = await self.get_experience(exp_id, user_id)
        if not experience:
            return None

        # 只允许更新特定字段
        allowed_fields = [
            "situation", "action", "result", "lesson", "solution",
            "skills_used", "skills_discovered", "embedding",
        ]

        for field in allowed_fields:
            if field in data:
                setattr(experience, field, data[field])

        await self.db.flush()
        await self.db.refresh(experience)

        return experience

    async def delete_experience(self, exp_id: str, user_id: str) -> bool:
        """删除经验"""
        experience = await self.get_experience(exp_id, user_id)
        if not experience:
            return False

        await self.db.delete(experience)
        await self.db.flush()

        return True

    async def get_agent_absorptions(
        self,
        agent_id: str,
        user_id: str,
    ) -> List[AgentExperienceAbsorption]:
        """获取 Agent 吸收的所有经验记录"""
        # 验证 agent 属于该用户
        agent_result = await self.db.execute(
            select(Agent).where(Agent.id == agent_id, Agent.user_id == user_id)
        )
        if not agent_result.scalar_one_or_none():
            return []

        result = await self.db.execute(
            select(AgentExperienceAbsorption)
            .where(AgentExperienceAbsorption.agent_id == agent_id)
            .order_by(AgentExperienceAbsorption.absorbed_at.desc())
        )
        return list(result.scalars().all())
