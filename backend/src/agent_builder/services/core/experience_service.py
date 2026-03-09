# -*- coding: utf-8 -*-
"""Experience service for managing agent experiences."""

import json
import math
import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from agent_builder.db.models import Experience, AgentExperienceAbsorption, Agent, LLMProvider
from agent_builder.services.core.llm_service import LLMClient


class ExperienceService:
    """Service for managing agent experiences."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_embedding_client(self, user_id: str) -> Optional[LLMClient]:
        """获取用于生成 embedding 的 LLM 客户端"""
        # 查询用户默认的 LLM provider
        result = await self.db.execute(
            select(LLMProvider).where(
                LLMProvider.user_id == user_id,
                LLMProvider.is_active == True,
            )
        )
        provider = result.scalars().first()

        if not provider:
            # 如果没有自定义 provider，尝试使用 Ollama 默认配置
            return LLMClient(
                api_key="",  # Ollama 不需要 API key
                api_base="http://localhost:11434",
                model="qwen3-embedding:4b",
                provider_type="ollama",
            )

        return LLMClient(
            api_key=provider.api_key,
            api_base=provider.api_base,
            model=provider.default_model or "qwen3-embedding:4b",
            provider_type=provider.provider_type,
        )

    async def _generate_embedding(self, text: str, user_id: str) -> Optional[List[float]]:
        """生成文本的 embedding 向量"""
        try:
            client = await self._get_embedding_client(user_id)
            if not client:
                return None

            # 构建用于 embedding 的文本（组合多个字段以获得更好的语义表示）
            embedding_text = f"{text}"
            embedding = await client.generate_embedding(embedding_text)
            await client.close()
            return embedding
        except Exception as e:
            print(f"Failed to generate embedding: {e}")
            return None

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算两个向量的余弦相似度"""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    async def create_experience(self, data: dict, auto_generate_embedding: bool = True) -> Experience:
        """创建新经验（初始状态为 draft）

        Args:
            data: 经验数据字典
            auto_generate_embedding: 是否自动生成 embedding（默认 True）
        """
        # 自动生成 embedding（如果未提供）
        embedding = data.get("embedding")
        if not embedding and auto_generate_embedding:
            # 组合多个字段生成更丰富的语义表示
            text_to_embed = f"{data.get('situation', '')} {data.get('action', '')} {data.get('lesson', '')} {data.get('solution', '')}"
            embedding = await self._generate_embedding(text_to_embed, data["user_id"])
            if embedding:
                embedding = json.dumps(embedding)  # 转换为 JSON 字符串存储

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
            embedding=embedding,
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
        use_semantic_search: bool = True,
    ) -> List[Experience]:
        """
        检索相关经验：
        - 同用户的 verified 经验
        - 当前 Agent 自己的 draft 经验

        使用混合搜索策略：
        1. 如果启用语义搜索且成功生成 query embedding，使用向量相似度
        2. 同时保留关键词匹配作为 fallback
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

        # 先获取所有符合条件的经验（有 embedding 的优先）
        base_query = (
            select(Experience)
            .where(Experience.user_id == user_id)
            .where(conditions)
        )

        result = await self.db.execute(base_query)
        all_experiences = list(result.scalars().all())

        if not all_experiences:
            return []

        # 尝试语义搜索
        query_embedding = None
        if use_semantic_search:
            query_embedding = await self._generate_embedding(query, user_id)

        if query_embedding:
            # 计算每个经验的向量相似度
            scored_experiences = []
            for exp in all_experiences:
                if exp.embedding:
                    try:
                        exp_embedding = json.loads(exp.embedding)
                        similarity = self._cosine_similarity(query_embedding, exp_embedding)
                        scored_experiences.append((exp, similarity))
                    except (json.JSONDecodeError, TypeError):
                        # 无法解析 embedding，跳过
                        pass

            # 按相似度排序
            scored_experiences.sort(key=lambda x: x[1], reverse=True)

            # 返回 top_k（有 embedding 的）
            results = [exp for exp, _ in scored_experiences[:top_k]]

            # 如果有 embedding 的经验不够，用关键词搜索补充
            if len(results) < top_k:
                remaining = [exp for exp in all_experiences if exp not in results]
                search_pattern = f"%{query}%"
                for exp in remaining:
                    # 简单的关键词匹配
                    if (search_pattern.lower() in exp.situation.lower() or
                        search_pattern.lower() in exp.action.lower() or
                        search_pattern.lower() in exp.lesson.lower() or
                        search_pattern.lower() in exp.solution.lower()):
                        results.append(exp)
                        if len(results) >= top_k:
                            break

            return results[:top_k]
        else:
            # 无法生成 embedding，回退到关键词搜索
            search_pattern = f"%{query}%"
            text_matched = []
            for exp in all_experiences:
                if (search_pattern.lower() in exp.situation.lower() or
                    search_pattern.lower() in exp.action.lower() or
                    search_pattern.lower() in exp.result.lower() or
                    search_pattern.lower() in exp.lesson.lower() or
                    search_pattern.lower() in exp.solution.lower()):
                    text_matched.append(exp)

            # 优先返回 verified 经验
            text_matched.sort(key=lambda x: (x.status != "verified", x.created_at), reverse=True)
            return text_matched[:top_k]

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

    async def list_user_experiences(
        self,
        user_id: str,
        status: Optional[str] = None,
        limit: int = 10,
    ) -> List[Experience]:
        """
        获取用户所有Agent的verified经验（跨Agent经验查询）

        Args:
            user_id: 用户ID
            status: 过滤经验状态 (verified, draft, deprecated)，默认返回verified
            limit: 返回结果的最大数量

        Returns:
            经验列表
        """
        query = select(Experience).where(Experience.user_id == user_id)

        # 如果没有指定status，默认返回verified经验
        if status:
            query = query.where(Experience.status == status)
        else:
            query = query.where(Experience.status == "verified")

        query = query.order_by(
            Experience.last_applied_at.desc().nullslast(),
            Experience.created_at.desc()
        ).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())
